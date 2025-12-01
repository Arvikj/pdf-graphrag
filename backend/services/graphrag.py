"""
GraphRAG Service

Simple RAG implementation using Neo4j knowledge graph + LLM.
Uses Ollama by default, with commented Gemini 2.5 Pro option.
"""
import os
import logging
from typing import Dict, List
from ollama import Client

from .neo4j_service import get_neo4j_service

logger = logging.getLogger(__name__)

# Default model for Ollama
DEFAULT_MODEL = "gemma3:12b"

# ============================================================================
# GEMINI 2.5 PRO OPTION (commented out - uncomment to use instead of Ollama)
# ============================================================================
# To use Gemini instead of Ollama:
# 1. pip install google-genai
# 2. Set GEMINI_API_KEY environment variable
# 3. Uncomment the Gemini code below and comment out the Ollama code
#
# from google import genai
# 
# # Client picks up API key from GEMINI_API_KEY env var automatically
# gemini_client = genai.Client()
# 
# def query_gemini(prompt: str) -> str:
#     """Query Gemini 2.5 Pro model per https://ai.google.dev/gemini-api/docs/quickstart"""
#     response = gemini_client.models.generate_content(
#         model="gemini-2.5-pro",
#         contents=prompt
#     )
#     return response.text
# ============================================================================


def format_context(graph_data: Dict) -> str:
    """
    Format graph data into a text context for the LLM.
    
    Args:
        graph_data: Dict with 'nodes' and 'relationships'
        
    Returns:
        Formatted string context
    """
    context_parts = []
    
    # Format nodes
    nodes = graph_data.get("nodes", [])
    if nodes:
        context_parts.append("=== ENTITIES ===")
        for node in nodes:
            node_id = node.get("id", "unknown")
            label = node.get("label", "Entity")
            props = node.get("properties", {})
            
            # Build entity description
            desc = f"- {label}: {node_id}"
            if props.get("name"):
                desc = f"- {label}: {props['name']}"
            if props.get("description"):
                desc += f" ({props['description']})"
            
            context_parts.append(desc)
    
    # Format relationships
    relationships = graph_data.get("relationships", [])
    if relationships:
        context_parts.append("\n=== RELATIONSHIPS ===")
        for rel in relationships:
            source = rel.get("source_id", "?")
            target = rel.get("target_id", "?")
            rel_type = rel.get("type", "RELATED_TO")
            context_parts.append(f"- {source} --[{rel_type}]--> {target}")
    
    return "\n".join(context_parts) if context_parts else "No context available."


def query_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Query Ollama LLM with the given prompt.
    
    Args:
        prompt: The full prompt including context and question
        model: Ollama model to use
        
    Returns:
        LLM response text
    """
    try:
        client = Client()
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.3,
                "num_predict": 1024,
            }
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama query failed: {e}")
        raise


def graphrag_query(question: str, model: str = DEFAULT_MODEL) -> Dict:
    """
    Answer a question using GraphRAG.
    
    Process:
    1. Search Neo4j for relevant nodes based on keywords in question
    2. Get context (neighboring nodes/relationships)
    3. Format context and send to LLM with question
    4. Return answer
    
    Args:
        question: User's question
        model: LLM model to use
        
    Returns:
        Dict with 'answer', 'sources' (relevant nodes), and 'context_used'
    """
    neo4j = get_neo4j_service()
    
    # Step 1: Extract keywords from question and search for relevant nodes
    # Simple approach: split question into words, search for each
    words = question.lower().split()
    # Filter out common words
    stop_words = {"what", "is", "the", "a", "an", "are", "how", "who", "where", "when", 
                  "why", "does", "do", "can", "could", "would", "should", "tell", "me",
                  "about", "of", "in", "on", "at", "to", "for", "with", "by", "from",
                  "this", "that", "these", "those", "it", "its", "and", "or", "but"}
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Search for nodes matching keywords
    relevant_nodes = []
    seen_ids = set()
    for keyword in keywords[:5]:  # Limit to top 5 keywords
        found = neo4j.search_nodes(keyword, limit=5)
        for node in found:
            if node["id"] not in seen_ids:
                seen_ids.add(node["id"])
                relevant_nodes.append(node)
    
    # Step 2: Get context for relevant nodes
    if relevant_nodes:
        node_ids = [n["id"] for n in relevant_nodes[:10]]  # Limit context nodes
        context_data = neo4j.get_node_context(node_ids)
    else:
        # If no relevant nodes found, get a sample of the graph
        context_data = neo4j.get_graph()
        # Limit to first 20 nodes if graph is large
        if len(context_data.get("nodes", [])) > 20:
            context_data["nodes"] = context_data["nodes"][:20]
            context_data["relationships"] = context_data["relationships"][:30]
    
    # Step 3: Format context
    context_text = format_context(context_data)
    
    # Step 4: Build prompt and query LLM
    prompt = f"""You are a helpful assistant answering questions about a document based on a knowledge graph.
Use the following context from the knowledge graph to answer the question.
If you cannot find the answer in the context, say so honestly.

CONTEXT FROM KNOWLEDGE GRAPH:
{context_text}

QUESTION: {question}

ANSWER:"""

    # Query LLM (Ollama by default)
    answer = query_ollama(prompt, model)
    
    # ========================================================================
    # GEMINI ALTERNATIVE (uncomment to use instead of Ollama)
    # ========================================================================
    # answer = query_gemini(prompt)
    # ========================================================================
    
    return {
        "answer": answer,
        "sources": relevant_nodes[:5],  # Return top 5 source nodes
        "context_used": len(context_data.get("nodes", []))
    }


def simple_chat(message: str, model: str = DEFAULT_MODEL) -> str:
    """
    Simple chat without graph context (fallback).
    
    Args:
        message: User message
        model: LLM model to use
        
    Returns:
        LLM response
    """
    prompt = f"""You are a helpful assistant. Please answer the following question or respond to the message.

Message: {message}

Response:"""
    
    return query_ollama(prompt, model)
