"""
LLM client for extracting graph data from text using Gemini.

Uses google-genai SDK with Gemini 2.0 Flash Lite for entity extraction.
"""
import logging
import time
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from .graph_models import GraphData

logger = logging.getLogger(__name__)

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Initialize client with API key from .env
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Model for entity extraction (fast, cheap)
EXTRACTION_MODEL = "gemini-2.0-flash-lite"


def extract_graph_data(text: str, model: str = EXTRACTION_MODEL) -> GraphData:
    """
    Extract entities and relationships from text using Gemini.
    
    Includes 60s retry on rate limit errors.
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

    while True:
        try:
            logger.info(f"Sending request to {model}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            
            # Parse JSON from response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = GraphData.model_validate_json(response_text)
            logger.info(f"Extracted {len(result.nodes)} nodes, {len(result.relationships)} relationships")
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            # Check for rate limit error
            if "429" in str(e) or "resource_exhausted" in error_str or "rate" in error_str:
                logger.warning("Rate limit hit, waiting 60s before retry...")
                time.sleep(60)
                continue  # Retry same request
            
            logger.error(f"LLM extraction failed: {e}")
            return GraphData(nodes=[], relationships=[])
