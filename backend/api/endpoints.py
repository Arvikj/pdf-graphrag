from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import time
import shutil
import os
import logging
from backend.services.pipeline import run_pipeline
from backend.services.graphrag import graphrag_query
from backend.services.neo4j_service import get_neo4j_service
from fastapi.responses import StreamingResponse
import json

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    upload_dir = "uploaded_documents"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📂 Saved file to: {file_path}")
        
        try:
            neo4j = get_neo4j_service()
            if neo4j.verify_connection():
                neo4j.clear_database()
                print("🗑️ Cleared existing graph data")
        except Exception as e:
            print(f"⚠️ Could not clear Neo4j (will continue): {e}")
        
        print("🚀 Starting GraphRAG pipeline... (This may take a minute)")
            
        async def event_generator():
            try:
                for event in run_pipeline(file_path):
                    yield json.dumps(event) + "\n"
            except Exception as e:
                yield json.dumps({"status": "error", "message": str(e)}) + "\n"

        return StreamingResponse(event_generator(), media_type="application/x-ndjson")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint using GraphRAG.
    Queries Neo4j for relevant context, then uses LLM to answer.
    """
    try:
        result = graphrag_query(request.message)
        return {"response": result["answer"]}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": f"I encountered an issue processing your question. Please ensure Neo4j is running (docker-compose up -d) and GEMINI_API_KEY is set. Error: {str(e)}"}


@router.get("/graph")
async def get_graph():
    """
    Get the knowledge graph data for visualization.
    Returns all nodes and relationships from Neo4j.
    """
    try:
        neo4j = get_neo4j_service()
        if not neo4j.verify_connection():
            raise HTTPException(status_code=503, detail="Neo4j is not available. Start it with: docker-compose up -d")
        
        graph_data = neo4j.get_graph()
        return {
            "status": "success",
            "data": graph_data,
            "stats": {
                "nodes": len(graph_data.get("nodes", [])),
                "relationships": len(graph_data.get("relationships", []))
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get graph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/stats")
async def get_graph_stats():
    """Get graph statistics."""
    try:
        neo4j = get_neo4j_service()
        if not neo4j.verify_connection():
            return {"status": "disconnected", "node_count": 0, "relationship_count": 0}
        
        stats = neo4j.get_stats()
        return {"status": "connected", **stats}
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"status": "error", "error": str(e)}


@router.delete("/graph")
async def clear_graph():
    """Clear all data from Neo4j."""
    try:
        neo4j = get_neo4j_service()
        neo4j.clear_database()
        return {"status": "success", "message": "Database cleared"}
    except Exception as e:
        logger.error(f"Clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
