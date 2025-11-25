"""
LLM client for extracting graph data from text using Ollama.

Uses Ollama's structured output feature with Pydantic schemas.
"""
import logging
from ollama import Client
from .graph_models import GraphData

logger = logging.getLogger(__name__)


def extract_graph_data(text: str, model: str = "gemma3:12b") -> GraphData:
    """
    Extract entities and relationships from text using a local LLM.
    
    Args:
        text: Input text to extract graph data from
        model: Ollama model name (default: gemma3:12b)
        
    Returns:
        GraphData: Extracted nodes and relationships
    """
    prompt = f"""You are an expert knowledge graph extractor.
    Task: Extract entities and relationships from the text below to build a property graph.
    
    1. Nodes (Entities):
       - id: unique, lowercase, snake_case identifier.
       - label: entity type (e.g., Person, Organization, Location, Concept, Event).
       - properties: meaningful attributes (e.g., names, dates, values, descriptions) as a dictionary.
       
    2. Relationships:
       - source_id: id of the source node.
       - target_id: id of the target node.
       - type: relationship type (uppercase, snake_case, e.g., LOCATED_IN).
       - properties: relationship details (e.g., role, since) as a dictionary.
       
    Constraints:
    - Reuse node IDs exactly for relationships.
    - Ensure referential integrity: all source_id and target_id values must exist in the nodes list.
    
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
