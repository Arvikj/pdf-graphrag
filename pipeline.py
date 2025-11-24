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
from pdf_parser_v1 import parse_pdf
from llm_client import extract_graph_data
from graph_models import GraphData, Node, Relationship

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Configuration
INPUT_PDF = "Data/Insurance/Sample Policy Specimen.pdf"
OUT_DIR = Path("results")
MODEL = "gemma3:12b"

def main():
    """Main pipeline execution."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Parsing PDF: {INPUT_PDF}")
    doc = parse_pdf(INPUT_PDF)
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


if __name__ == "__main__":
    main()
