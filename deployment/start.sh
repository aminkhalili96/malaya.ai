#!/bin/bash
set -eo pipefail
echo "🚀 Starting Malaya LLM..."
echo "========================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

# Check Env
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Copying .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        echo "❌ No .env found. Please create one with your API keys."
        exit 1
    fi
fi
# Load .env variables into shell environment safely
set -a
[ -f .env ] && source .env
set +a

# Activate venv if exists
VENV_DIR=""
if [ -d "${ROOT_DIR}/venv" ]; then
    VENV_DIR="${ROOT_DIR}/venv"
elif [ -d "${ROOT_DIR}/.venv" ]; then
    VENV_DIR="${ROOT_DIR}/.venv"
elif [ -d "${ROOT_DIR}/../.venv" ]; then
    VENV_DIR="${ROOT_DIR}/../.venv"
fi

if [ -n "${VENV_DIR}" ]; then
    source "${VENV_DIR}/bin/activate"
fi

# Optional dependency install
if [ "${INSTALL_DEPS:-}" = "1" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    echo "📦 Installing frontend dependencies..."
    (cd frontend && npm install)
fi

# Kill existing processes on ports 8000 (Backend) and 5173 (Frontend)
echo "🧹 Cleaning up old processes..."
if command -v lsof >/dev/null 2>&1; then
    for port in 8000 5173; do
        pids=$(lsof -ti:${port} || true)
        if [ -n "${pids}" ]; then
            kill ${pids} 2>/dev/null || true
        fi
    done
else
    echo "⚠️  lsof not found; skipping port cleanup."
fi
sleep 2

# Run Backend & Frontend
echo "🔊 Starting Backend (Port 8000)..."
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"
export VITE_GOOGLE_MAPS_API_KEY="${GOOGLE_MAPS_API_KEY:-}"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3
if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
    echo "❌ Backend failed to start. Check your Python env and dependencies."
    exit 1
fi

echo "💻 Starting Frontend (Port 5173)..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

# Trap Ctrl+C to kill both
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT

echo "
✅ Malaya LLM is running!
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173
"

wait
