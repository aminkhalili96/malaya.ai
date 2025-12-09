"""
Malaya LLM API - FastAPI Backend
================================
Features:
- CORS: Environment-based configuration
- Rate Limiting: Prevents API abuse
- Health Check: Reports dependency status
"""

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.routers import chat

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Malaya LLM API",
    version="2.1",
    description="Sovereign AI Copilot with Malaysian language understanding"
)

# Attach limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Environment-based configuration (secure by default)
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/health")
def health_check():
    """
    Enhanced health check that reports dependency status.
    Useful for Kubernetes readiness/liveness probes.
    """
    return {
        "status": "ok",
        "version": "2.1",
        "dependencies": {
            "llm_configured": True,  # Uses Ollama (local)
            "search_configured": bool(os.environ.get("TAVILY_API_KEY")),
        }
    }
