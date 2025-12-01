"""
PDF to Knowledge Graph Pipeline

Orchestrates PDF parsing, chunking, and LLM-based graph extraction.
"""
import json
import logging
import time
from pathlib import Path
from ollama import Client
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
MODEL = "gemma3:1b"

def run_pipeline(pdf_path: str):
    """Main pipeline execution."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Parsing PDF: {pdf_path}")
    doc = parse_pdf(pdf_path)
    logger.info("PDF parsed successfully")
    
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
    
    logger.info(f"Saving chunks to {chunks_file}...")
    with chunks_file.open("w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks, 1):
            f.write(f"# Chunk {i}\n\n")
            f.write(chunker.contextualize(chunk=chunk))
            f.write("\n\n---\n\n")

    logger.info("Starting graph extraction from chunks...")
    all_nodes = []
    all_relationships = []
    
    for i, chunk in enumerate(chunks, 1):
        logger.info(f"Processing chunk {i}/{len(chunks)}")
        
        # Get enriched text with context
        enriched_text = chunker.contextualize(chunk=chunk)
        logger.debug(f"Chunk {i} enriched text length: {len(enriched_text)} chars")
        
        # Extract graph data using LLM
        logger.info(f"Sending chunk {i} to LLM for extraction...")
        graph_data = extract_graph_data(enriched_text, model=MODEL)
        logger.info(f"Chunk {i} extraction complete: {len(graph_data.nodes)} nodes, {len(graph_data.relationships)} relationships")
        
        # Prefix IDs with chunk number to avoid collisions across chunks
        prefix = f"c{i}_"
        for node in graph_data.nodes:
            node.id = prefix + node.id
        for rel in graph_data.relationships:
            rel.source_id = prefix + rel.source_id
            rel.target_id = prefix + rel.target_id
        
        # Collect results
        all_nodes.extend(graph_data.nodes)
        all_relationships.extend(graph_data.relationships)
        
        # Save partial results every 5 chunks or on the last chunk
        if i % 5 == 0 or i == len(chunks):
            logger.info(f"Saving partial results to {OUT_DIR}...")
            partial_graph = GraphData(nodes=all_nodes, relationships=all_relationships)
            with (OUT_DIR / "graph_data_partial.json").open("w", encoding="utf-8") as f:
                f.write(partial_graph.model_dump_json(indent=2))
    
    logger.info(f"Extraction complete: {len(all_nodes)} total nodes, {len(all_relationships)} total relationships")
    
    # Aggregate all graph data
    final_graph = GraphData(nodes=all_nodes, relationships=all_relationships)
    
    # Save to JSON
    output_file = OUT_DIR / "graph_data.json"
    with output_file.open("w", encoding="utf-8") as f:
        f.write(final_graph.model_dump_json(indent=2))
    
    logger.info(f"Saved graph data to: {output_file}")
    
    # Ingest into Neo4j
    try:
        from .neo4j_service import get_neo4j_service
        neo4j = get_neo4j_service()
        if neo4j.verify_connection():
            logger.info("Ingesting graph data into Neo4j...")
            stats = neo4j.ingest_graph(final_graph.model_dump())
            logger.info(f"Neo4j ingestion complete: {stats}")
        else:
            logger.warning("Neo4j not available - skipping ingestion. Start Neo4j with: docker-compose up -d")
    except Exception as e:
        logger.warning(f"Neo4j ingestion skipped: {e}")
    
    return final_graph.model_dump()
