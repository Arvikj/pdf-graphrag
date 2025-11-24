# pdf-graphrag

An end-to-end pipeline for extracting insights from documents. Ingests PDFs, builds a knowledge graph, and enables intelligent querying via RAG.

## Current Status

**Phase 1 Complete**: PDF parsing and chunking  
**Phase 2 Complete**: LLM-based entity and relationship extraction  
**Phase 3 (In Progress)**: Neo4j ingestion

## Architecture

```
pdf-graphrag/
├── backend/            # FastAPI application and parsing logic
│   ├── api/           # API endpoints (/upload, /chat)
│   └── services/      # Core logic (PDF parsing)
├── frontend/          # React application (Vite)
│   └── src/components/  # Reusable UI components
├── pdf_parser_v1.py   # PDF parsing with Docling (OCR + table structure)
├── graph_models.py    # Pydantic models for Neo4j (Node, Relationship, GraphData)
├── llm_client.py      # Ollama integration for entity/relationship extraction
├── pipeline.py        # Main orchestration script
└── requirements.txt   # Dependencies
```

## Prerequisites

- **Python 3.10+**
- **Node.js 16+** & **npm**
- **Ollama** (for local LLM)

## Installation
## 🛠️ Prerequisites
- **Python 3.9+**
- **Node.js 16+** & **npm**

## 📦 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd pdf-graphrag
```

### 2. Backend Setup
The backend is built with FastAPI and handles PDF processing.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Ollama Setup
```bash
# Install Ollama from https://ollama.ai
# Then pull the model
ollama pull gemma3:12b
```

### 4. Frontend Setup
pip install fastapi uvicorn python-multipart docling
```

### 3. Frontend Setup
The frontend is a React application using Vite.

```bash
cd frontend
npm install
```

## Running the Application
## 🏃‍♂️ Running the Application

You need to run the **Backend** and **Frontend** in two separate terminal windows.

### Terminal 1: Backend
```bash
# Make sure you are in the root directory and venv is activated
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```
*The backend will start at `http://localhost:8000`*

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```
*The frontend will start at `http://localhost:5173`*

## Usage

### Via Web Interface
1. Open your browser and go to **http://localhost:5173**
2. **Upload**: Drag & drop a PDF file into the upload zone
3. **Process**: Watch the status stepper as the backend parses your file
4. **Chat**: Once "Ready!", type a question to interact with the document
5. **Graph**: Click "Knowledge Graph" in the sidebar to view the visualization

### Via Command Line (Phase 2 Pipeline)
```bash
python pipeline.py
```

This will:
1. Parse the PDF using Docling (with OCR and table structure recognition)
2. Chunk the document using HybridChunker
3. Extract entities and relationships from each chunk using the local LLM
4. Save the graph data to `results/graph_data.json`

### Configuration

Edit `pipeline.py` to customize:
- `INPUT_PDF`: Path to your PDF file
- `MODEL`: Ollama model to use (default: `gemma3:12b`)

## Output Format

The pipeline generates `results/graph_data.json` with this structure:

```json
{
  "nodes": [
    {
      "id": "unique_id",
      "label": "EntityType",
      "properties": {"key": "value"}
    }
  ],
  "relationships": [
    {
      "source_id": "node_id_1",
      "target_id": "node_id_2",
      "type": "RELATIONSHIP_TYPE",
      "properties": {"key": "value"}
    }
  ]
}
```

This format is ready for Neo4j ingestion.

## Dependencies

- **docling** (v2.62.0): PDF parsing with AI models
- **transformers**: Required for HybridChunker tokenization
- **ollama**: Local LLM client (Python v0.6.1, Ollama v0.13.0)
- **pydantic**: Data validation and schema enforcement
- **fastapi**: Web API framework
- **uvicorn**: ASGI server

## Notes

- Tested with gemma3:12b on ASU Sol supercomputer (A100 GPU)
- Code follows official Docling and Ollama documentation
- Minimal, functional design with no over-engineering

## 📖 Usage
1.  Open your browser and go to **http://localhost:5173**.
2.  **Upload**: Drag & drop a PDF file (e.g., from the `Data/` folder) into the upload zone.
3.  **Process**: Watch the status stepper as the backend parses your file.
4.  **Chat**: Once "Ready!", you will be taken to the Chat interface. Type a question to test it out.
5.  **Graph**: Click "Knowledge Graph" in the sidebar to view the visualization placeholder.

## 📂 Project Structure
- `backend/`: FastAPI application and parsing logic.
    - `api/`: API endpoints (`/upload`, `/chat`).
    - `services/`: Core logic (PDF parsing).
- `frontend/`: React application.
    - `src/components/`: Reusable UI components.
- `uploaded_documents/`: Stores uploaded PDFs and their parsed JSON output.
