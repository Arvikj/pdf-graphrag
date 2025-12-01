"""
PDF to Knowledge Graph Pipeline

Orchestrates PDF parsing, chunking, and LLM-based graph extraction.
"""
import json
import logging
import time
from pathlib import Path
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from .parser import parse_pdf
from .llm_client import extract_graph_data
from .graph_models import GraphData, Node, Relationship

# Configure logging
logger = logging.getLogger(__name__)


# Configuration
OUT_DIR = Path("results")

def run_pipeline(pdf_path: str):
    """
    Main pipeline execution.
    Yields progress updates as JSON-compatible dictionaries.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    yield {"status": "processing", "step": 1, "message": "Parsing PDF..."}
    logger.info(f"Parsing PDF: {pdf_path}")
    doc = parse_pdf(pdf_path)
    logger.info("PDF parsed successfully")
    
    yield {"status": "processing", "step": 2, "message": "Chunking text..."}
    logger.info("Setting up HybridChunker with tokenizer...")
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2"),
        max_tokens=512  # Match model max sequence length
    )
    chunker = HybridChunker(tokenizer=tokenizer)
    
    logger.info("Chunking document...")
    chunks = list(chunker.chunk(dl_doc=doc))
    logger.info(f"Created {len(chunks)} chunks")
    
    # Save chunks for verification
    CHUNKS_DIR = Path("chunks")
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    chunks_file = CHUNKS_DIR / "chunks.md"
    
    # Collect chunk texts for storage
    chunk_texts = []
    logger.info(f"Saving chunks to {chunks_file}...")
    with chunks_file.open("w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks, 1):
            text = chunker.contextualize(chunk=chunk)
            chunk_texts.append({"id": f"chunk_{i}", "text": text})
            f.write(f"# Chunk {i}\n\n")
            f.write(text)
            f.write("\n\n---\n\n")

    yield {"status": "processing", "step": 3, "message": "Extracting entities with AI..."}
    logger.info("Starting graph extraction from chunks...")
    all_nodes = []
    all_relationships = []
    
    for i, chunk in enumerate(chunks, 1):
        logger.info(f"Processing chunk {i}/{len(chunks)}")
        yield {"status": "processing", "step": 3, "message": f"Extracting from chunk {i}/{len(chunks)}..."}
        
        enriched_text = chunker.contextualize(chunk=chunk)
        logger.info(f"Sending chunk {i} to Gemini for extraction...")
        graph_data = extract_graph_data(enriched_text)
        logger.info(f"Chunk {i} extraction complete: {len(graph_data.nodes)} nodes, {len(graph_data.relationships)} relationships")
        prefix = f"c{i}_"
        for node in graph_data.nodes:
            node.id = prefix + node.id
            node.properties["source_chunk"] = f"chunk_{i}"
        for rel in graph_data.relationships:
            rel.source_id = prefix + rel.source_id
            rel.target_id = prefix + rel.target_id
        
        all_nodes.extend(graph_data.nodes)
        all_relationships.extend(graph_data.relationships)
    
    logger.info(f"Extraction complete: {len(all_nodes)} total nodes, {len(all_relationships)} total relationships")
    
    final_graph = GraphData(nodes=all_nodes, relationships=all_relationships)
    
    output_file = OUT_DIR / "graph_data.json"
    with output_file.open("w", encoding="utf-8") as f:
        f.write(final_graph.model_dump_json(indent=2))
    
    chunks_json = OUT_DIR / "chunks.json"
    with chunks_json.open("w", encoding="utf-8") as f:
        json.dump(chunk_texts, f, indent=2)
    
    logger.info(f"Saved graph data to: {output_file}")
    logger.info(f"Saved chunks to: {chunks_json}")
    
    yield {"status": "processing", "step": 4, "message": "Building Knowledge Graph..."}
    try:
        from .neo4j_service import get_neo4j_service
        neo4j = get_neo4j_service()
        if neo4j.verify_connection():
            logger.info("Ingesting graph data into Neo4j...")
            stats = neo4j.ingest_graph(final_graph.model_dump(), chunk_texts)
            logger.info(f"Neo4j ingestion complete: {stats}")
        else:
            logger.warning("Neo4j not available - skipping ingestion. Start Neo4j with: docker-compose up -d")
    except Exception as e:
        logger.warning(f"Neo4j ingestion skipped: {e}")
    
    yield {"status": "complete", "step": 5, "message": "Ready!", "data": final_graph.model_dump()}
