from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import time
import shutil
import os
from backend.services.parser import parse_pdf

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
        print("🚀 Starting Docling processing... (This may take a minute)")
            
        # Process the PDF using the real parser
        parsed_data = parse_pdf(file_path)
        print(parsed_data)
        print("✅ Docling processing complete!")
        
        # Save the result to a JSON file for verification
        json_output_path = os.path.join(upload_dir, f"{file.filename}.json")
        import json
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2)
            
        print(f"💾 Saved parsed data to: {json_output_path}")
        
        return {
            "filename": file.filename, 
            "status": "success",
            "message": "File processed successfully",
            "data_preview": {
                "num_pages": len(parsed_data.get("pages", [])),
                "title": parsed_data.get("title", "Unknown")
            }
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
