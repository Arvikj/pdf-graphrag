"""
PDF to Knowledge Graph Pipeline

Orchestrates PDF parsing, chunking, and LLM-based graph extraction.
"""
import json
from pathlib import Path
from docling.chunking import HybridChunker
from pdf_parser_v1 import parse_pdf
from llm_client import extract_graph_data
from graph_models import GraphData, Node, Relationship


# Configuration
INPUT_PDF = "Data/Insurance/Sample Policy Specimen.pdf"
OUT_DIR = Path("results")
MODEL = "llama3.1"  # Change to "phi3" or other Ollama model as needed


def main():
    """Main pipeline execution."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"📄 Parsing PDF: {INPUT_PDF}")
    doc = parse_pdf(INPUT_PDF)
    print(f"✓ Parsed successfully")
    
    print(f"✂️  Chunking document...")
    chunker = HybridChunker()
    chunks = list(chunker.chunk(dl_doc=doc))
    print(f"✓ Created {len(chunks)} chunks")
    
    print(f"🤖 Extracting graph data from chunks...")
    all_nodes = []
    all_relationships = []
    
    for i, chunk in enumerate(chunks, 1):
        print(f"   Processing chunk {i}/{len(chunks)}...", end="\r")
        
        # Get enriched text with context
        enriched_text = chunker.contextualize(chunk=chunk)
        
        # Extract graph data using LLM
        graph_data = extract_graph_data(enriched_text, model=MODEL)
        
        # Collect results
        all_nodes.extend(graph_data.nodes)
        all_relationships.extend(graph_data.relationships)
    
    print(f"\n✓ Extracted {len(all_nodes)} nodes and {len(all_relationships)} relationships")
    
    # Aggregate all graph data
    final_graph = GraphData(nodes=all_nodes, relationships=all_relationships)
    
    # Save to JSON
    output_file = OUT_DIR / "graph_data.json"
    with output_file.open("w", encoding="utf-8") as f:
        f.write(final_graph.model_dump_json(indent=2))
    
    print(f"💾 Saved graph data to: {output_file}")
    print(f"\n✅ Pipeline complete!")


if __name__ == "__main__":
    main()
