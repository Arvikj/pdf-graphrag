# pdf-graphrag

An end-to-end pipeline for extracting insights from documents. Ingests PDFs, builds a knowledge graph, and enables intelligent querying via RAG.

## Current Status

**Phase 1 Complete**: PDF parsing and chunking  
**Phase 2 Complete**: LLM-based entity and relationship extraction  
**Phase 3 (In Progress)**: Neo4j ingestion

## Architecture

```
pdf-graphrag/
├── pdf_parser_v1.py    # PDF parsing with Docling (OCR + table structure)
├── graph_models.py     # Pydantic models for Neo4j (Node, Relationship, GraphData)
├── llm_client.py       # Ollama integration for entity/relationship extraction
├── pipeline.py         # Main orchestration script
└── requirements.txt    # Dependencies
```

## Setup

### Prerequisites

1. **Python 3.10+**
2. **Ollama** (for local LLM)
   ```bash
   # Install Ollama from https://ollama.ai
   # Then pull a model (e.g., gemma3 or llama3.1)
   ollama pull gemma3:12b
   ```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify Ollama is running
ollama list
```

## Usage

### Run the Full Pipeline

```bash
python pipeline.py
```

This will:
1. Parse the PDF using Docling (with OCR and table structure recognition)
2. Chunk the document using HybridChunker
3. Extract entities and relationships from each chunk using the local LLM
4. Save the graph data to `results/graph_data.json`

### Configuration

Edit `pipeline.py` to customize:
- `INPUT_PDF`: Path to your PDF file
- `MODEL`: Ollama model to use (default: `gemma3:12b`)

### Run Individual Components

```bash
# PDF parsing only
python pdf_parser_v1.py
```

## Output Format

The pipeline generates `results/graph_data.json` with this structure:

```json
{
  "nodes": [
    {
      "id": "unique_id",
      "label": "EntityType",
      "properties": {"key": "value"}
    }
  ],
  "relationships": [
    {
      "source_id": "node_id_1",
      "target_id": "node_id_2",
      "type": "RELATIONSHIP_TYPE",
      "properties": {"key": "value"}
    }
  ]
}
```

This format is ready for Neo4j ingestion.

## Dependencies

- **docling** (v2.62.0): PDF parsing with AI models
- **transformers**: Required for HybridChunker tokenization
- **ollama**: Local LLM client (Python v0.6.1, Ollama v0.13.0)
- **pydantic**: Data validation and schema enforcement

## Notes

- Tested with gemma3:12b on ASU Sol supercomputer (A100 GPU)
- Code follows official Docling and Ollama documentation
- Minimal, functional design with no over-engineering

