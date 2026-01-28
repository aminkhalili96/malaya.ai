# =================================================================
# Malaya LLM - Multi-Stage Docker Build
# Architecture: FastAPI (Backend) + React/Vite (Frontend)
# =================================================================

# -----------------------------------------------------------------
# Stage 1: Build Frontend
# -----------------------------------------------------------------
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend

# Install dependencies (cache layer)
COPY frontend/package*.json ./
RUN npm ci

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
COPY requirements-prod.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy backend application code
COPY backend/ ./backend/
COPY src/ ./src/
COPY config.yaml .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./static

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Cloud Run expects the container to listen on $PORT (default 8080)
ENV PORT=8080
EXPOSE 8080

# Healthcheck using dynamic port (localhost might not work if binding 0.0.0.0 only, but curl typically fine)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:$PORT/health || exit 1

# Run via entrypoint
ENTRYPOINT ["./entrypoint.sh"]
