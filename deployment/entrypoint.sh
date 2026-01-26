#!/bin/bash
# Entrypoint script to handle Cloud Run's dynamic PORT

# Default to 8080 if PORT not set
PORT=${PORT:-8080}

echo "🚀 Starting Malaya LLM on port $PORT..."

# Start uvicorn with the dynamic port
exec uvicorn backend.main:app --host 0.0.0.0 --port $PORT
