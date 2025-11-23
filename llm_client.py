"""
LLM client for extracting graph data from text using Ollama.

Uses Ollama's structured output feature with Pydantic schemas.
"""
import ollama
from graph_models import GraphData


def extract_graph_data(text: str, model: str = "llama3.1") -> GraphData:
    """
    Extract entities and relationships from text using a local LLM.
    
    Args:
        text: Input text to extract graph data from
        model: Ollama model name (default: llama3.1)
        
    Returns:
        GraphData: Extracted nodes and relationships
    """
    prompt = f"""Extract entities and relationships from the following text.
Focus on identifying:
- Entities: People, organizations, locations, concepts, etc.
- Relationships: How entities are connected (e.g., WORKS_AT, LOCATED_IN, PART_OF)

For each entity, provide:
- id: A unique identifier (lowercase, underscores for spaces)
- label: Entity type (Person, Organization, Location, Concept, etc.)
- properties: Key attributes as a dictionary

For each relationship, provide:
- source_id: ID of the source entity
- target_id: ID of the target entity
- type: Relationship type (uppercase, underscores)
- properties: Additional context as a dictionary

Text:
{text}
"""

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format=GraphData.model_json_schema(),
        )
        
        # Parse response into GraphData
        return GraphData.model_validate_json(response.message.content)
    
    except Exception as e:
        print(f"Warning: LLM extraction failed: {e}")
        # Return empty graph data on error
        return GraphData(nodes=[], relationships=[])
