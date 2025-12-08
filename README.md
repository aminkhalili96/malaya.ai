# Malaya LLM (Sovereign AI Copilot)

A full-stack AI application (FastAPI + React) designed for YTL AI Labs.

## 🚀 Quick Start

### 1. Start the Backend (FastAPI)
Runs the LLM engine and API.
```bash
cd backend
pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8002
```
*Backend runs at: `http://localhost:8002`*

### 2. Start the Frontend (React + Vite)
Runs the modern chat interface.
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs at: `http://localhost:5173`*

## 🏗 Architecture
- **Frontend**: React, Vite, Tailwind CSS (YTL Red Theme).
- **Backend**: FastAPI, LangChain, ChromaDB.
- **Engine**: Custom Python logic for RAG and Persona handling.

## 📚 Documentation
- [How it Works](.gemini/antigravity/brain/77f91eca-3e26-4619-82e3-5d72a1a9c2f8/how_it_works.md)
- [Project Tracking](GEMINI.md)
