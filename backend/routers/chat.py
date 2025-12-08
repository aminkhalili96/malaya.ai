"""
Chat Router - Malaya LLM API
============================
Features:
- Rate limiting: 10 requests/minute per IP
- Input validation: Max 4000 chars, max 10 history messages
- Dependency injection for testability
"""

import sys
import os
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

# Add root to path to import src
sys.path.append(os.getcwd())

from src.chatbot.engine import MalayaChatbot

router = APIRouter()

# Rate limiter (uses same instance from main.py)
limiter = Limiter(key_func=get_remote_address)


# Dependency injection for chatbot (singleton)
@lru_cache()
def get_chatbot() -> MalayaChatbot:
    """Lazy-load chatbot as singleton for reuse across requests."""
    return MalayaChatbot()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=4000, description="User message (max 4000 chars)")
    history: List[ChatMessage] = Field(default=[], max_length=10, description="Chat history (max 10 messages)")
    
    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict] = []
    context: Optional[str] = None


@router.post("/", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(
    request: Request,  # Required for rate limiter
    chat_request: ChatRequest,
    bot: MalayaChatbot = Depends(get_chatbot)
):
    """
    Process a chat message and return AI response.
    
    Rate limit: 10 requests per minute per IP.
    """
    try:
        # Convert Pydantic models to dicts for engine
        history_dicts = [{"role": m.role, "content": m.content} for m in chat_request.history]
        
        response = bot.process_query(chat_request.message, history_dicts)
        
        return ChatResponse(
            answer=response["answer"],
            sources=response["sources"],
            context=response.get("context")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

