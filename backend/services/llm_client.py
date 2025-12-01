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
    # Prompt based on Neo4j GraphRAG documentation pattern
    prompt = f"""Extract entities and relationships from the text below.

Return JSON with this format:
{{"nodes": [{{"id": "0", "label": "Entity type", "properties": {{"name": "Entity name"}}}}],
 "relationships": [{{"source_id": "0", "target_id": "1", "type": "RELATIONSHIP_TYPE", "properties": {{}}}}]}}

Rules:
- Assign simple numeric string IDs ("0", "1", "2", etc.) to each node
- Reuse these exact IDs in relationships
- Label types: Person, Organization, Location, Concept, Document, Event
- Include "name" in properties for each node
- Relationship types should be UPPERCASE_WITH_UNDERSCORES

Input text:
{text}
"""

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
