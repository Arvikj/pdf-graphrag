from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import time
import shutil
import os
from backend.services.pipeline import run_pipeline
from backend.services.graph_db import run_cypher, populate_graph
from backend.services.rag_service import answer_query
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class QueryRequest(BaseModel):
    database: str
    cypher: str

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create a temporary file to save the upload
    # Create a permanent directory to save the upload
    upload_dir = "uploaded_documents"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        # Save the uploaded PDF
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📂 Saved file to: {file_path}")
        print("🚀 Starting GraphRAG pipeline... (This may take a minute)")
            
        # Process the PDF using the pipeline
        graph_data = run_pipeline(file_path)
        print("✅ Pipeline processing complete!")
        
        return {
            "filename": file.filename, 
            "status": "success",
            "message": "File processed successfully",
            "data_preview": {
                "num_nodes": len(graph_data.get("nodes", [])),
                "num_relationships": len(graph_data.get("relationships", []))
            },
            "graph_data": graph_data
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Use the default database (configurable via NEO4J_DB env var)
    print("Received chat request")
    database = os.getenv("NEO4J_DB", "neo4j")

    # Call the RAG service to retrieve context and generate an answer
    answer = await answer_query(database, request.message, top_k=5, use_graph_retriever=True)
    return {"response": answer}

@router.get("/neo4j/config")
async def get_config():
    return {
        "url": os.getenv("NEO4J_URI"),
        "user": os.getenv("NEO4J_USER"),
        "pass": os.getenv("NEO4J_PASSWORD")
    }

@router.get("/neo4j/databases")
async def get_databases():
    records = await run_cypher("neo4j", "SHOW DATABASES")
    print("records", records)
    return [r["name"] for r in records if r["name"] not in ("system")]

@router.get("/neo4j/{db}/node-labels")
async def get_node_labels(db: str):
    records = await run_cypher(db, "CALL db.labels()")
    return [r["label"] for r in records]

@router.get("/neo4j/{db}/relationship-types")
async def get_relationship_types(db: str):
    records = await run_cypher(db, "CALL db.relationshipTypes()")
    return [r["relationshipType"] for r in records]

@router.get("/neo4j/{db}/query")
async def run_query(db: str, query: str):
    return await run_cypher(db, query)