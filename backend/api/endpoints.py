from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import time
import shutil
import os
from backend.services.pipeline import run_pipeline

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

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
    # Cleanup removed as requested

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Simulate processing time
    time.sleep(0.5)
    
    # Dummy response logic
    return {"response": f"This is a dummy response to: '{request.message}'. The system is currently in UI-only mode."}
