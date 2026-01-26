#!/bin/bash
set -e

echo "🐳 initializing Malaya LLM v2 (Full Mode - Docker)..."

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Please start Docker Desktop and try again."
  exit 1
fi

echo "📦 Building Container Image (this may take a few minutes)..."
docker build -t malaya-v2-full .

# Prepare Cache Directory (to persist downloaded models)
CACHE_DIR="$HOME/.cache/malaya-docker"
mkdir -p "$CACHE_DIR"
echo "📂 Model Cache: $CACHE_DIR"

echo "🔥 Starting Malaya Server [Full Mode]..."
echo "---------------------------------------------------"
echo "Access the Testbench at: http://localhost:8000"
echo "Press Ctrl+C to stop."
echo "---------------------------------------------------"

docker run -it --rm \
    -p 8000:8000 \
    -v "$CACHE_DIR:/root/.cache/malaya" \
    -e MALAYA_FORCE_MOCK=0 \
    -e OLLAMA_HOST=http://host.docker.internal:11434 \
    --name malaya-v2-bench \
    malaya-v2-full
