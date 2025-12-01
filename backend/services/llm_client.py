"""
LLM client for extracting graph data from text using Ollama.

Uses Ollama's structured output feature with Pydantic schemas.
"""
import logging
from ollama import Client
from .graph_models import GraphData

logger = logging.getLogger(__name__)


def extract_graph_data(text: str, model: str = "gemma3:1b") -> GraphData:
    """
    Extract entities and relationships from text using a local LLM.
    
    Args:
        text: Input text to extract graph data from
        model: Ollama model name (default: gemma3:1b)
        
    Returns:
        GraphData: Extracted nodes and relationships
    """
    # Very explicit prompt with complete example for smaller models
    prompt = f"""Extract a knowledge graph from the text below.

EXAMPLE INPUT: "Facebook uses RocksDB for data storage. RocksDB is a key-value store."

EXAMPLE OUTPUT:
{{
  "nodes": [
    {{"id": "0", "label": "Organization", "properties": {{"name": "Facebook"}}}},
    {{"id": "1", "label": "Concept", "properties": {{"name": "RocksDB"}}}},
    {{"id": "2", "label": "Concept", "properties": {{"name": "key-value store"}}}}
  ],
  "relationships": [
    {{"source_id": "0", "target_id": "1", "type": "USES", "properties": {{}}}},
    {{"source_id": "1", "target_id": "2", "type": "IS_A", "properties": {{}}}}
  ]
}}

IMPORTANT:
- Every node MUST have "name" in properties
- You MUST extract relationships between entities
- Use IDs "0", "1", "2" etc. and reference them in relationships

TEXT:
{text}

OUTPUT:"""

    try:
        logger.debug(f"Initializing Ollama client")
        client = Client()
        
        logger.info(f"Sending request to model {model} (streaming)...")
        stream = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format=GraphData.model_json_schema(),
            options={
                "temperature": 0.0,      # Deterministic output
                "num_predict": 2048,     # Prevent infinite generation loops
                "repeat_penalty": 1.1,   # Reduce repetition
                "num_ctx": 4096          # Ensure sufficient context
            },
            stream=True
        )
        
        # Accumulate response
        full_response = ""
        print("Generating: ", end="", flush=True)
        for chunk in stream:
            content = chunk.get('message', {}).get('content', '')
            full_response += content
            print(".", end="", flush=True)
        print(" Done.")
        
        logger.debug("Parsing LLM response")
        # Parse response into GraphData
        result = GraphData.model_validate_json(full_response)
        logger.info(f"Successfully extracted {len(result.nodes)} nodes and {len(result.relationships)} relationships")
        return result
    
    except Exception as e:
        logger.error(f"LLM extraction failed: {type(e).__name__}: {e}")
        # Return empty graph data on error
        return GraphData(nodes=[], relationships=[])
