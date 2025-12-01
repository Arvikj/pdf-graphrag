"""
GraphRAG Service - Simple RAG using document chunks + Gemini.

Uses google-genai SDK with Gemini 2.5 Flash.
"""
import logging
import time
import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
from google import genai

from .neo4j_service import get_neo4j_service

logger = logging.getLogger(__name__)

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Initialize client with API key from .env
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Model for chat/RAG
CHAT_MODEL = "gemini-2.5-flash"

# Stop words for keyword extraction
STOP_WORDS = {
    "what", "is", "the", "a", "an", "are", "how", "who", "where", "when",
    "why", "does", "do", "can", "could", "would", "should", "tell", "me",
    "about", "of", "in", "on", "at", "to", "for", "with", "by", "from",
    "this", "that", "these", "those", "it", "its", "and", "or", "but"
}


def query_gemini(prompt: str, model: str = CHAT_MODEL) -> str:
    """Query Gemini with 60s retry on rate limit."""
    while True:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            error_str = str(e).lower()
            if "429" in str(e) or "resource_exhausted" in error_str or "rate" in error_str:
                logger.warning("Rate limit hit, waiting 60s before retry...")
                time.sleep(60)
                continue
            logger.error(f"Gemini query failed: {e}")
            raise


def graphrag_query(question: str, model: str = CHAT_MODEL) -> Dict:
    """
    Answer a question using document chunks as context.
    
    1. Extract keywords from question
    2. Search chunks by keyword
    3. Send chunk text + question to Gemini
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
Be concise and specific. Quote relevant details. If the answer is not in the context or cannot be reliably inferred from it, say "I don't have enough information."

DOCUMENT CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    answer = query_gemini(prompt, model)
    
    return {
        "answer": answer,
        "sources": [],
        "context_used": len(chunk_texts)
    }


def simple_chat(message: str, model: str = CHAT_MODEL) -> str:
    """Simple chat without document context."""
    return query_gemini(f"You are a helpful assistant. Answer: {message}", model)
