from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import endpoints

app = FastAPI(title="PDF GraphRAG API", description="Backend for PDF Workflow Digitalization", version="0.1.0")

# CORS Setup
# Allow all origins for dev tunnel compatibility
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to PDF GraphRAG API"}
