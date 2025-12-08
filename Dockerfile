# =================================================================
# Malaya LLM - Multi-Stage Docker Build
# Architecture: FastAPI (Backend) + React/Vite (Frontend)
# =================================================================

# -----------------------------------------------------------------
# Stage 1: Build Frontend
# -----------------------------------------------------------------
FROM node:18-slim AS frontend-builder

WORKDIR /app/frontend

# Install dependencies (cache layer)
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY frontend/ ./
RUN npm run build

# -----------------------------------------------------------------
# Stage 2: Python Backend
# -----------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ ./backend/
COPY src/ ./src/
COPY config.yaml .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose FastAPI port
EXPOSE 8000

# Healthcheck using FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
