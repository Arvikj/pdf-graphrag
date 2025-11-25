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
- **Ollama** (for local LLM) — or access to ASU Sol Supercomputer

## 📦 Installation (Local Machine)

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

### 3. Ollama Setup (Local Machine)
```bash
# Install Ollama from https://ollama.ai
# Then pull the model
ollama pull gemma3:12b
```

> **💡 Tip for Local Users:** If you're running locally with limited resources, you can use a lighter model. Simply replace the model name in `llm_client.py` and pull it:
> ```bash
> ollama pull gemma3:1b   # Lightest option
> ollama pull gemma3:4b   # Balanced option
> ollama pull llama3.2    # Alternative lightweight model available in 1b or 3b parameters
> ```

### 4. Frontend Setup
The frontend is a React application using Vite.

```bash
cd frontend
npm install
```

---

## 🖥️ ASU Sol Supercomputer Setup

This section provides detailed instructions for running pdf-graphrag on the **ASU Sol Supercomputer**.

### Prerequisites
- Access to ASU Sol supercomputer (request at [ASU Research Computing](https://cores.research.asu.edu/research-computing/getting-started))
- Your ASURITE login credentials

### Step 1: Initial Environment Setup (One-Time, on Login Node)

Connect to Sol via SSH or VS Code Remote, then run these commands on the **login node**:

```bash
# 1. Clone the repository
git clone https://github.com/Arvikj/pdf-graphrag.git
cd pdf-graphrag

# 2. Load Mamba (Python environment manager)
module load mamba/latest

# 3. Create the Python environment
mamba create -n graphrag_env -c conda-forge python=3.10 -y

# 4. Activate the environment and install dependencies
source activate graphrag_env
pip install -r requirements.txt
```

### Step 2: Download the Model (One-Time, on Compute Node)

**⚠️ Important:** You cannot run Ollama on the login node. You must start an interactive GPU session.

```bash
# 1. Start an interactive session with 1 GPU (1 hour)
interactive -G 1 -t 0-1:00

# --- WAIT for the prompt to change (e.g., [yourname@sg...]) ---

# 2. Set your HOME path (replace 'yourname' with your ASURITE)
export HOME=/home/yourname
export OLLAMA_MODELS=/home/yourname/ollama-models

# 3. Load CUDA and Ollama modules
module load cuda-12.4.1-gcc-12.1.0
module load ollama/0.12.10

# 4. Start the Ollama server
ollama-start
sleep 5

# 5. Pull the model
ollama pull gemma3:12b

# 6. Verify GPU/CUDA is working (optional)
ollama run gemma3:12b "Hello, are you working?"
# Type /bye to exit the chat

# 7. Stop Ollama to exit the session
ollama-stop
exit
```

### Step 3: Running the Pipeline (Interactive Mode)

For running the pipeline interactively:

```bash
# 1. Start an interactive GPU session
interactive -G 1 -t 0-2:00

# 2. Load all required modules
module load mamba/latest
module load cuda-12.4.1-gcc-12.1.0
module load ollama/0.12.10

# 3. Activate your environment
source activate graphrag_env

# 4. Set environment variables (replace 'yourname' with your ASURITE)
export HOME=/home/yourname
export OLLAMA_MODELS=/home/yourname/ollama-models

# 5. Start Ollama server
ollama-start
sleep 5

# 6. Run the pipeline
cd ~/pdf-graphrag
python pipeline.py

# 7. When done, cleanup
ollama-stop
exit
```

### Using Lighter Models on Sol

If you want to use a lighter model (faster inference, less GPU memory), pull a lighter model during your interactive session:

```bash
ollama pull gemma3:1b   # ~1GB, fastest
ollama pull gemma3:4b   # ~4GB, balanced
ollama pull llama3.2    # Alternative option
```

Then update `llm_client.py` to use your chosen model, or modify `pipeline.py`:
```python
MODEL = "gemma3:4b"  # Change from "gemma3:12b"
```

---

## 🏃‍♂️ Running the Application

You need to run the **Backend** and **Frontend** in two separate terminal windows.

### Terminal 1: Backend
```bash
# Make sure you are in the root directory and venv is activated
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
# alternatively, if that doesn't work, for sol try:
uvicorn backend.main:app --reload --reload-dir backend --port 8000 --host 0.0.0.0
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
