"""
GraphRAG Service - Simple RAG using document chunks + LLM.
"""
import logging
from typing import Dict
from ollama import Client

from .neo4j_service import get_neo4j_service

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemma3:1b"

# Stop words for keyword extraction
STOP_WORDS = {
    "what", "is", "the", "a", "an", "are", "how", "who", "where", "when",
    "why", "does", "do", "can", "could", "would", "should", "tell", "me",
    "about", "of", "in", "on", "at", "to", "for", "with", "by", "from",
    "this", "that", "these", "those", "it", "its", "and", "or", "but"
}


def query_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Query Ollama LLM."""
    try:
        client = Client()
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_predict": 1024}
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"Ollama query failed: {e}")
        raise


def graphrag_query(question: str, model: str = DEFAULT_MODEL) -> Dict:
    """
    Answer a question using document chunks as context.
    
    1. Extract keywords from question
    2. Search chunks by keyword
    3. Send chunk text + question to LLM
    """
    neo4j = get_neo4j_service()
    
    # Extract keywords
    words = question.lower().split()
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    
    # Search for matching chunks
    chunk_texts = []
    for keyword in keywords[:5]:
        found = neo4j.search_chunks(keyword, limit=3)
        for text in found:
            if text not in chunk_texts:
                chunk_texts.append(text)
    
    # Fallback: get all chunks if no keyword matches
    if not chunk_texts:
        chunk_texts = neo4j.get_all_chunks()[:5]
    
    # Build context
    context = "\n\n---\n\n".join(chunk_texts[:5]) if chunk_texts else "No document content available."
    
    # Build prompt
    prompt = f"""Answer the question using ONLY the following document context.
Be concise. If the answer is not in the context, say "I don't have enough information."

DOCUMENT CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    answer = query_ollama(prompt, model)
    
    return {
        "answer": answer,
        "sources": [],
        "context_used": len(chunk_texts)
    }


def simple_chat(message: str, model: str = DEFAULT_MODEL) -> str:
    """Simple chat without document context."""
    prompt = f"You are a helpful assistant. Answer: {message}"
    return query_ollama(prompt, model)
