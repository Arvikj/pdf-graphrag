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
pip install fastapi uvicorn python-multipart docling
```

### 3. Frontend Setup
The frontend is a React application using Vite.

```bash
cd frontend
npm install
```

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
