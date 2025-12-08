#!/bin/bash
# =================================================================
# Malaya LLM - Startup Script
# =================================================================
# This script starts both the FastAPI backend and React frontend

set -e

# Install Python dependencies if missing
echo "📦 Checking Python dependencies..."
pip install -r requirements.txt -q

# Install frontend dependencies if missing
echo "📦 Checking frontend dependencies..."
cd frontend && npm install -q && cd ..

# Start backend in background
echo "🚀 Starting FastAPI backend on port 8000..."
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Start frontend
echo "🎨 Starting React frontend on port 5173..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "============================================================"
echo "✅ Malaya LLM is running!"
echo "============================================================"
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "============================================================"

# Wait for Ctrl+C and cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
