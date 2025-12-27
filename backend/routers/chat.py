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
import json
import requests
import yaml
import asyncio
from pathlib import Path
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator
from typing import Any, List, Dict, Optional, Literal
from slowapi import Limiter
from slowapi.util import get_remote_address

# Add root to path to import src
sys.path.append(os.getcwd())

from src.chatbot.engine import MalayaChatbot
from src.storage import SQLiteStore
from backend.observability import log_event, record_error, redact_pii, metrics_snapshot, CHAT_REQUESTS, CHAT_ERRORS
from backend.security import (
    require_api_key,
    chat_rate_limit,
    voice_rate_limit,
    tts_rate_limit,
    image_rate_limit,
    analytics_rate_limit,
    feedback_rate_limit,
    require_role,
)
from backend.runtime_config import load_runtime_config, save_runtime_config

router = APIRouter()
share_store = SQLiteStore()
feedback_store = SQLiteStore()

# Rate limiter (uses same instance from main.py)
limiter = Limiter(key_func=get_remote_address)


# Payload size limits (bytes). Override via env if needed.
MAX_AUDIO_BYTES = int(os.environ.get("MAX_AUDIO_BYTES", 8 * 1024 * 1024))
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", 4 * 1024 * 1024))
MAX_ATTACHMENT_CHARS = int(os.environ.get("MAX_ATTACHMENT_CHARS", 12000))
MAX_ATTACHMENTS = int(os.environ.get("MAX_ATTACHMENTS", 6))


def _enforce_project_access(request: Request, project_id: str) -> None:
    runtime = load_runtime_config()
    access_map = runtime.get("project_access", {}) or {}
    required_role = access_map.get(project_id)
    if required_role and getattr(request.state, "api_role", None) != required_role:
        raise HTTPException(status_code=403, detail="Insufficient role for project.")


def _strip_data_url(value: str) -> str:
    if value.startswith("data:"):
        return value.split(",", 1)[-1]
    return value


def _estimate_base64_bytes(value: str) -> int:
    payload = _strip_data_url(value.strip())
    if not payload:
        return 0
    padding = payload.count("=")
    return max(0, (len(payload) * 3) // 4 - padding)


def _chunk_text(text: str, chunk_size: int = 48):
    if not text:
        return []
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


# Dependency injection for chatbot (singleton)
@lru_cache()
def get_chatbot() -> MalayaChatbot:
    """Lazy-load chatbot as singleton for reuse across requests."""
    return MalayaChatbot()


@lru_cache()
def _load_config() -> Dict:
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def _resolve_ollama_base_url(config: Optional[Dict] = None) -> str:
    base_url = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST")
    if not base_url:
        base_url = (config or {}).get("model", {}).get("base_url")
    return (base_url or "http://localhost:11434").rstrip("/")


def _load_prompt_variants() -> Dict[str, Dict[str, str]]:
    path = Path("docs/prompt_variants.yaml")
    variants: Dict[str, Dict[str, str]] = {}
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            raw = data.get("variants", data) if isinstance(data, dict) else {}
            if isinstance(raw, dict):
                for key, value in raw.items():
                    if not isinstance(value, dict):
                        continue
                    variants[key] = {
                        "label": value.get("label", key),
                        "description": value.get("description", ""),
                        "prefix": value.get("prefix", ""),
                        "suffix": value.get("suffix", ""),
                    }
        except Exception:
            variants = {}
    if "default" not in variants:
        variants["default"] = {
            "label": "Default",
            "description": "Base system prompt",
            "prefix": "",
            "suffix": "",
        }
    return variants


def _fetch_ollama_models(base_url: str):
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=2)
        response.raise_for_status()
        data = response.json()
        models = [item.get("name") for item in data.get("models", []) if item.get("name")]
        return models, None
    except Exception as exc:
        return [], str(exc)


class ChatMessage(BaseModel):
    role: str
    content: str


class ModelSelection(BaseModel):
    provider: Literal["ollama", "openai"]
    name: str = Field(..., min_length=1, description="Model name (e.g. qwen3:14b, gpt-4o)")


class ToolSettings(BaseModel):
    web_search: bool = True
    citations: bool = True


class Attachment(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    mime_type: Optional[str] = Field(default=None, max_length=120)
    size: Optional[int] = None
    scope: Optional[Literal["message", "project"]] = Field(default="message")

    @field_validator("content")
    @classmethod
    def attachment_size_limit(cls, value: str) -> str:
        if len(value) > MAX_ATTACHMENT_CHARS:
            raise ValueError(f"Attachment content too large (max {MAX_ATTACHMENT_CHARS} chars)")
        return value


class ProviderModels(BaseModel):
    available: bool
    models: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    base_url: Optional[str] = None


class ModelsResponse(BaseModel):
    providers: Dict[str, ProviderModels]
    default: Optional[ModelSelection] = None


class PromptVariant(BaseModel):
    key: str
    label: str
    description: Optional[str] = None


class PromptVariantsResponse(BaseModel):
    variants: List[PromptVariant]


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=4000, description="User message (max 4000 chars)")
    history: List[ChatMessage] = Field(default_factory=list, max_length=10, description="Chat history (max 10 messages)")
    model: Optional[ModelSelection] = None
    response_mode: Optional[Literal["auto", "fast", "quality"]] = Field(default=None, description="Client-selected response mode")
    prompt_variant: Optional[str] = Field(default=None, max_length=80, description="Prompt variant key")
    tools: Optional[ToolSettings] = None
    project_id: Optional[str] = Field(default=None, description="Optional project id for memory")
    tone: Optional[str] = Field(default=None, description="Tone: neutral, formal, casual")
    profile: Optional[str] = Field(default=None, max_length=600, description="User profile / preferences")
    project_prompt: Optional[str] = Field(default=None, max_length=1000, description="Project-level instructions")
    attachments: List[Attachment] = Field(default_factory=list, description="Optional file attachments")
    
    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v

    @field_validator("attachments")
    @classmethod
    def attachments_limit(cls, value: List[Attachment]) -> List[Attachment]:
        if len(value) > MAX_ATTACHMENTS:
            raise ValueError(f"Too many attachments (max {MAX_ATTACHMENTS})")
        return value


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict] = Field(default_factory=list)
    context: Optional[str] = None
    tool_calls: List[Dict] = Field(default_factory=list)
    risk_score: Optional[float] = None
    cached: Optional[bool] = None
    pii_detected: Optional[bool] = None
    timings: Optional[Dict[str, Any]] = None


@router.get("/models", response_model=ModelsResponse, dependencies=[Depends(require_api_key)])
async def list_models(request: Request):
    config = _load_config()
    base_url = _resolve_ollama_base_url(config)
    ollama_models, ollama_error = _fetch_ollama_models(base_url)
    ollama_available = ollama_error is None

    openai_key = os.environ.get("OPENAI_API_KEY")
    openai_available = bool(openai_key)
    openai_error = None if openai_available else "OPENAI_API_KEY is not set."

    log_event(
        "models_list",
        request_id=getattr(request.state, "request_id", None),
        openai_available=openai_available,
        ollama_available=ollama_available,
    )

    default_model = None
    model_config = config.get("model", {}) if config else {}
    provider = model_config.get("provider")
    name = model_config.get("name")
    if provider in ("ollama", "openai") and name:
        default_model = ModelSelection(provider=provider, name=name)

    return ModelsResponse(
        providers={
            "ollama": ProviderModels(
                available=ollama_available,
                models=ollama_models,
                error=ollama_error,
                base_url=base_url,
            ),
            "openai": ProviderModels(
                available=openai_available,
                models=["gpt-4o", "gpt-4o-mini"],
                error=openai_error,
            ),
        },
        default=default_model,
    )


@router.get("/prompt-variants", response_model=PromptVariantsResponse, dependencies=[Depends(require_api_key)])
async def list_prompt_variants():
    variants = _load_prompt_variants()
    payload = [
        PromptVariant(
            key=key,
            label=value.get("label", key),
            description=value.get("description", ""),
        )
        for key, value in variants.items()
    ]
    return PromptVariantsResponse(variants=payload)


@router.post("/", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
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
    request_id = getattr(request.state, "request_id", None)
    model_provider = chat_request.model.provider if chat_request.model else "default"
    model_name = chat_request.model.name if chat_request.model else None
    tool_settings = chat_request.tools or ToolSettings()
    attachments_count = len(chat_request.attachments or [])
    if chat_request.project_id:
        _enforce_project_access(request, chat_request.project_id)

    CHAT_REQUESTS.labels(endpoint="chat").inc()
    log_event(
        "chat_request",
        request_id=request_id,
        message_length=len(chat_request.message),
        history_length=len(chat_request.history),
        model_provider=model_provider,
        model_name=model_name,
        response_mode=chat_request.response_mode,
        prompt_variant=chat_request.prompt_variant,
        web_search=tool_settings.web_search,
        citations=tool_settings.citations,
        project_id=chat_request.project_id,
        attachments_count=attachments_count,
        role=getattr(request.state, "api_role", None),
    )

    try:
        # Convert Pydantic models to dicts for engine
        history_dicts = [{"role": m.role, "content": m.content} for m in chat_request.history]
        
        response = await bot.process_query(
            chat_request.message,
            history_dicts,
            model=chat_request.model,
            tools=chat_request.tools,
            project_id=chat_request.project_id,
            tone=chat_request.tone,
            profile=chat_request.profile,
            project_prompt=chat_request.project_prompt,
            prompt_variant=chat_request.prompt_variant,
            attachments=[attachment.model_dump() for attachment in chat_request.attachments],
        )

        timings = response.get("timings") or {}
        log_event(
            "chat_response",
            request_id=request_id,
            cached=response.get("cached"),
            pii_detected=response.get("pii_detected"),
            total_ms=timings.get("total_ms"),
            llm_ms=timings.get("llm_ms"),
            retrieval_ms=timings.get("retrieval_ms"),
            tool_ms=timings.get("tool_ms"),
        )
        
        return ChatResponse(
            answer=response["answer"],
            sources=response["sources"],
            context=response.get("context"),
            tool_calls=response.get("tool_calls", []),
            risk_score=response.get("risk_score"),
            cached=response.get("cached"),
            pii_detected=response.get("pii_detected"),
            timings=response.get("timings"),
        )
    except Exception as e:
        CHAT_ERRORS.labels(endpoint="chat", error_type=type(e).__name__).inc()
        log_event(
            "chat_error",
            request_id=request_id,
            error_type=type(e).__name__,
            detail=str(e),
        )
        record_error(
            "chat_error",
            {"request_id": request_id, "error_type": type(e).__name__, "detail": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    bot: MalayaChatbot = Depends(get_chatbot),
):
    request_id = getattr(request.state, "request_id", None)
    model_provider = chat_request.model.provider if chat_request.model else "default"
    model_name = chat_request.model.name if chat_request.model else None
    tool_settings = chat_request.tools or ToolSettings()
    attachments_count = len(chat_request.attachments or [])
    if chat_request.project_id:
        _enforce_project_access(request, chat_request.project_id)

    CHAT_REQUESTS.labels(endpoint="chat_stream").inc()
    log_event(
        "chat_stream_request",
        request_id=request_id,
        message_length=len(chat_request.message),
        history_length=len(chat_request.history),
        model_provider=model_provider,
        model_name=model_name,
        response_mode=chat_request.response_mode,
        prompt_variant=chat_request.prompt_variant,
        web_search=tool_settings.web_search,
        citations=tool_settings.citations,
        project_id=chat_request.project_id,
        attachments_count=attachments_count,
        role=getattr(request.state, "api_role", None),
    )

    history_dicts = [{"role": m.role, "content": m.content} for m in chat_request.history]

    async def event_stream():
        try:
            response = await bot.process_query(
                chat_request.message,
                history_dicts,
                model=chat_request.model,
                tools=chat_request.tools,
                project_id=chat_request.project_id,
                tone=chat_request.tone,
                profile=chat_request.profile,
                project_prompt=chat_request.project_prompt,
                prompt_variant=chat_request.prompt_variant,
                attachments=[attachment.model_dump() for attachment in chat_request.attachments],
            )

            timings = response.get("timings") or {}
            log_event(
                "chat_stream_response",
                request_id=request_id,
                cached=response.get("cached"),
                pii_detected=response.get("pii_detected"),
                total_ms=timings.get("total_ms"),
                llm_ms=timings.get("llm_ms"),
                retrieval_ms=timings.get("retrieval_ms"),
                tool_ms=timings.get("tool_ms"),
            )

            meta_payload = {
                "request_id": request_id,
                "risk_score": response.get("risk_score"),
                "cached": response.get("cached"),
                "pii_detected": response.get("pii_detected"),
                "timings": response.get("timings"),
            }
            yield f"event: meta\ndata: {json.dumps(meta_payload)}\n\n"

            if response.get("tool_calls"):
                yield f"event: tool\ndata: {json.dumps(response['tool_calls'])}\n\n"

            if response.get("sources"):
                yield f"event: sources\ndata: {json.dumps(response['sources'])}\n\n"

            answer = response.get("answer", "")
            for chunk in _chunk_text(answer):
                yield f"event: delta\ndata: {json.dumps({'delta': chunk})}\n\n"
                await asyncio.sleep(0)

            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            CHAT_ERRORS.labels(endpoint="chat_stream", error_type=type(exc).__name__).inc()
            log_event(
                "chat_stream_error",
                request_id=request_id,
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            record_error(
                "chat_stream_error",
                {"request_id": request_id, "error_type": type(exc).__name__, "detail": str(exc)}
            )
            error_payload = {"error": str(exc)}
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============================================================================
# Voice Endpoints (TTS/STT)
# ============================================================================

class VoiceRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded audio")
    language: str = Field(default="ms", description="Language code (ms=Malay, en=English)")

    @field_validator("audio_base64")
    @classmethod
    def audio_size_limit(cls, value: str) -> str:
        size = _estimate_base64_bytes(value)
        if size > MAX_AUDIO_BYTES:
            raise ValueError(f"Audio payload too large (max {MAX_AUDIO_BYTES // (1024 * 1024)} MB)")
        return value


class VoiceChatResponse(BaseModel):
    transcribed_text: str
    answer: str
    sources: List[Dict] = Field(default_factory=list)
    audio_response_base64: Optional[str] = None


class TTSRequest(BaseModel):
    text: str = Field(..., max_length=2000, description="Text to synthesize")
    voice: str = Field(default="female", description="Voice: female, male, yasmin, osman")


class TTSResponse(BaseModel):
    audio_base64: str
    voice: str


@router.post("/voice", response_model=VoiceChatResponse, dependencies=[Depends(require_api_key)])
@limiter.limit("5/minute")
async def voice_chat(
    request: Request,
    voice_request: VoiceRequest,
    bot: MalayaChatbot = Depends(get_chatbot)
):
    """
    Process voice input: transcribe -> process -> respond with TTS.
    
    Rate limit: 5 requests per minute per IP.
    """
    request_id = getattr(request.state, "request_id", None)
    audio_size = _estimate_base64_bytes(voice_request.audio_base64)
    CHAT_REQUESTS.labels(endpoint="voice").inc()
    log_event(
        "voice_request",
        request_id=request_id,
        audio_bytes=audio_size,
        language=voice_request.language,
    )

    try:
        import base64
        import binascii
        from src.voice import VoiceAssistant
        
        assistant = VoiceAssistant()
        
        # Decode audio
        audio_payload = _strip_data_url(voice_request.audio_base64).strip()
        try:
            audio_bytes = base64.b64decode(audio_payload, validate=True)
        except binascii.Error:
            raise HTTPException(status_code=400, detail="Invalid base64 audio payload")
        
        # STT: Voice to text
        if not assistant.stt_available:
            raise HTTPException(status_code=503, detail="Speech-to-text service not available")
        
        transcribed = await run_in_threadpool(
            assistant.voice_to_text,
            audio_bytes,
            voice_request.language
        )
        
        # Process with chatbot
        response = await bot.process_query(transcribed)
        
        # TTS: Text to voice (optional)
        audio_response = None
        if assistant.tts_available:
            try:
                audio_bytes = await assistant.text_to_voice_async(response["answer"])
                audio_response = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception:
                pass  # TTS is optional
        
        return VoiceChatResponse(
            transcribed_text=transcribed,
            answer=response["answer"],
            sources=response["sources"],
            audio_response_base64=audio_response
        )
    except HTTPException:
        raise
    except Exception as e:
        CHAT_ERRORS.labels(endpoint="voice", error_type=type(e).__name__).inc()
        log_event(
            "voice_error",
            request_id=request_id,
            error_type=type(e).__name__,
            detail=str(e),
        )
        record_error(
            "voice_error",
            {"request_id": request_id, "error_type": type(e).__name__, "detail": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


class VoiceStreamRequest(VoiceRequest):
    session_id: Optional[str] = None


VOICE_SESSIONS = {}


@router.post("/voice/stream", dependencies=[Depends(require_api_key)])
@limiter.limit("5/minute")
async def voice_stream(
    request: Request,
    voice_request: VoiceStreamRequest,
    bot: MalayaChatbot = Depends(get_chatbot),
):
    request_id = getattr(request.state, "request_id", None)
    session_id = voice_request.session_id or f"voice-{request_id}"
    VOICE_SESSIONS.setdefault(session_id, {"cancelled": False})

    async def event_stream():
        try:
            import base64
            import binascii
            from src.voice import VoiceAssistant

            assistant = VoiceAssistant()
            audio_payload = _strip_data_url(voice_request.audio_base64).strip()
            try:
                audio_bytes = base64.b64decode(audio_payload, validate=True)
            except binascii.Error:
                yield f"event: error\ndata: {json.dumps({'error': 'Invalid base64 audio payload'})}\n\n"
                return

            if VOICE_SESSIONS.get(session_id, {}).get("cancelled"):
                yield "event: cancelled\ndata: {}\n\n"
                return

            if not assistant.stt_available:
                yield f"event: error\ndata: {json.dumps({'error': 'Speech-to-text service not available'})}\n\n"
                return

            transcribed = await run_in_threadpool(
                assistant.voice_to_text,
                audio_bytes,
                voice_request.language
            )
            yield f"event: transcript\ndata: {json.dumps({'text': transcribed})}\n\n"

            if VOICE_SESSIONS.get(session_id, {}).get("cancelled"):
                yield "event: cancelled\ndata: {}\n\n"
                return

            response = await bot.process_query(transcribed)
            answer = response.get("answer", "")
            yield f"event: answer\ndata: {json.dumps({'text': answer})}\n\n"

            if assistant.tts_available and answer:
                try:
                    audio_bytes = await assistant.text_to_voice_async(answer)
                    audio_response = base64.b64encode(audio_bytes).decode("utf-8")
                    yield f"event: audio\ndata: {json.dumps({'audio_base64': audio_response})}\n\n"
                except Exception:
                    pass

            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            CHAT_ERRORS.labels(endpoint="voice_stream", error_type=type(exc).__name__).inc()
            record_error(
                "voice_stream_error",
                {"request_id": request_id, "error_type": type(exc).__name__, "detail": str(exc)}
            )
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/voice/stop/{session_id}", dependencies=[Depends(require_api_key)])
@limiter.limit("5/minute")
async def stop_voice(request: Request, session_id: str):
    VOICE_SESSIONS[session_id] = {"cancelled": True}
    return {"status": "ok"}


@router.post("/tts", response_model=TTSResponse, dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
async def text_to_speech(
    request: Request,
    tts_request: TTSRequest
):
    """
    Convert text to Malaysian speech.
    
    Available voices:
    - female (ms-MY-YasminNeural)
    - male (ms-MY-OsmanNeural)
    """
    request_id = getattr(request.state, "request_id", None)
    CHAT_REQUESTS.labels(endpoint="tts").inc()
    log_event(
        "tts_request",
        request_id=request_id,
        text_length=len(tts_request.text),
        voice=tts_request.voice,
    )

    try:
        from src.voice import TextToSpeech
        import base64
        
        tts = TextToSpeech()
        if not tts.is_available:
            raise HTTPException(status_code=503, detail="TTS service not available. Install: pip install edge-tts")
        
        audio_bytes, _ = await tts.synthesize_async(tts_request.text, tts_request.voice)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        return TTSResponse(
            audio_base64=audio_base64,
            voice=tts_request.voice
        )
    except HTTPException:
        raise
    except Exception as e:
        CHAT_ERRORS.labels(endpoint="tts", error_type=type(e).__name__).inc()
        log_event(
            "tts_error",
            request_id=request_id,
            error_type=type(e).__name__,
            detail=str(e),
        )
        record_error(
            "tts_error",
            {"request_id": request_id, "error_type": type(e).__name__, "detail": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/status", dependencies=[Depends(require_api_key)])
async def voice_status():
    """Check status of voice services (TTS/STT)."""
    try:
        from src.voice import VoiceAssistant
        assistant = VoiceAssistant()
        return assistant.get_status()
    except Exception as e:
        return {"error": str(e), "tts": {"available": False}, "stt": {"available": False}}


# ============================================================================
# Vision Endpoints (Image Analysis)
# ============================================================================

class ImageRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image")
    question: Optional[str] = Field(default=None, description="Question about the image")
    mode: str = Field(default="general", description="Mode: general, food, meme, ocr")

    @field_validator("image_base64")
    @classmethod
    def image_size_limit(cls, value: str) -> str:
        size = _estimate_base64_bytes(value)
        if size > MAX_IMAGE_BYTES:
            raise ValueError(f"Image payload too large (max {MAX_IMAGE_BYTES // (1024 * 1024)} MB)")
        return value


class ImageResponse(BaseModel):
    analysis: str
    mode: str


class AnalyticsEvent(BaseModel):
    name: str = Field(..., min_length=1)
    payload: Dict = Field(default_factory=dict)
    timestamp: Optional[str] = None


class FeedbackRequest(BaseModel):
    conversation_id: Optional[str] = Field(default=None, max_length=120)
    message_id: Optional[str] = Field(default=None, max_length=120)
    rating: Literal["up", "down"]
    comment: Optional[str] = Field(default=None, max_length=600)
    model_provider: Optional[str] = Field(default=None, max_length=40)
    model_name: Optional[str] = Field(default=None, max_length=120)
    metadata: Dict = Field(default_factory=dict)


class ApiKeyEntry(BaseModel):
    key: str = Field(..., min_length=6)
    role: str = Field(default="admin")
    limits: Dict[str, str] = Field(default_factory=dict)


class RateLimitUpdate(BaseModel):
    chat: Optional[str] = None
    voice: Optional[str] = None
    tts: Optional[str] = None
    image: Optional[str] = None
    analytics: Optional[str] = None
    feedback: Optional[str] = None


class ShareRequest(BaseModel):
    type: Literal["conversation", "project"]
    payload: Dict
    ttl_seconds: Optional[int] = Field(default=7 * 24 * 3600, description="Share expiry in seconds")


class ShareResponse(BaseModel):
    share_id: str


@router.post("/image", response_model=ImageResponse, dependencies=[Depends(require_api_key)])
@limiter.limit("5/minute")
async def analyze_image(
    request: Request,
    image_request: ImageRequest
):
    """
    Analyze image with Malaysian context.
    
    Modes:
    - general: General analysis with MY context
    - food: Malaysian food recognition
    - meme: Malaysian meme understanding
    - ocr: Text extraction (BM/EN/CN/Tamil)
    """
    request_id = getattr(request.state, "request_id", None)
    image_size = _estimate_base64_bytes(image_request.image_base64)
    CHAT_REQUESTS.labels(endpoint="image").inc()
    log_event(
        "image_request",
        request_id=request_id,
        image_bytes=image_size,
        mode=image_request.mode,
        has_question=bool(image_request.question),
    )

    try:
        from src.vision import MalaysianVisionAnalyzer
        
        analyzer = MalaysianVisionAnalyzer()
        if not analyzer.is_available:
            raise HTTPException(status_code=503, detail="Vision service not available. Set OPENAI_API_KEY.")
        
        result = await run_in_threadpool(
            analyzer.analyze,
            image_request.image_base64,
            image_request.question,
            image_request.mode
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return ImageResponse(
            analysis=result["analysis"],
            mode=result["mode"]
        )
    except HTTPException:
        raise
    except Exception as e:
        CHAT_ERRORS.labels(endpoint="image", error_type=type(e).__name__).inc()
        log_event(
            "image_error",
            request_id=request_id,
            error_type=type(e).__name__,
            detail=str(e),
        )
        record_error(
            "image_error",
            {"request_id": request_id, "error_type": type(e).__name__, "detail": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vision/status", dependencies=[Depends(require_api_key)])
async def vision_status():
    """Check status of vision service."""
    try:
        from src.vision import MalaysianVisionAnalyzer
        analyzer = MalaysianVisionAnalyzer()
        return {
            "available": analyzer.is_available,
            "modes": ["general", "food", "meme", "ocr"]
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


@router.get("/projects/{project_id}/memory", dependencies=[Depends(require_api_key)])
async def get_project_memory(request: Request, project_id: str):
    _enforce_project_access(request, project_id)
    memory = share_store.get_project_memory(project_id)
    if not memory:
        return {"project_id": project_id, "summary": "", "message_count": 0}
    return {"project_id": project_id, **memory}


@router.delete("/projects/{project_id}/memory", dependencies=[Depends(require_api_key)])
async def clear_project_memory(request: Request, project_id: str, bot: MalayaChatbot = Depends(get_chatbot)):
    _enforce_project_access(request, project_id)
    bot.clear_project_memory(project_id)
    log_event(
        "project_memory_clear",
        request_id=getattr(request.state, "request_id", None),
        project_id=project_id,
        role=getattr(request.state, "api_role", None),
    )
    return {"status": "ok", "project_id": project_id}


@router.post("/analytics", dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
async def track_analytics(request: Request, event: AnalyticsEvent):
    request_id = getattr(request.state, "request_id", None)
    safe_payload = redact_pii(event.payload)
    log_event(
        "ui_event",
        request_id=request_id,
        name=event.name,
        payload=safe_payload,
        timestamp=event.timestamp,
        role=getattr(request.state, "api_role", None),
    )
    return {"status": "ok"}


@router.post("/feedback", dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
async def submit_feedback(request: Request, feedback: FeedbackRequest):
    import uuid

    request_id = getattr(request.state, "request_id", None)
    feedback_id = uuid.uuid4().hex
    CHAT_REQUESTS.labels(endpoint="feedback").inc()
    try:
        safe_metadata = redact_pii(feedback.metadata)
        feedback_store.create_feedback(
            feedback_id=feedback_id,
            conversation_id=feedback.conversation_id,
            message_id=feedback.message_id,
            rating=feedback.rating,
            comment=feedback.comment,
            model_provider=feedback.model_provider,
            model_name=feedback.model_name,
            metadata=safe_metadata,
        )
        log_event(
            "feedback_submit",
            request_id=request_id,
            feedback_id=feedback_id,
            rating=feedback.rating,
            conversation_id=feedback.conversation_id,
            message_id=feedback.message_id,
            model_provider=feedback.model_provider,
            model_name=feedback.model_name,
            comment_length=len(feedback.comment or ""),
            role=getattr(request.state, "api_role", None),
        )
        return {"status": "ok", "feedback_id": feedback_id}
    except Exception as exc:
        CHAT_ERRORS.labels(endpoint="feedback", error_type=type(exc).__name__).inc()
        record_error(
            "feedback_error",
            {"request_id": request_id, "error_type": type(exc).__name__, "detail": str(exc)}
        )
        raise HTTPException(status_code=500, detail="Failed to record feedback.")


@router.post("/share", response_model=ShareResponse, dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
async def create_share(request: Request, share: ShareRequest):
    import uuid

    share_id = uuid.uuid4().hex
    ttl_seconds = int(share.ttl_seconds or 0)
    share_store.create_share(share_id, share.type, share.payload, ttl_seconds)
    log_event(
        "share_create",
        request_id=getattr(request.state, "request_id", None),
        share_type=share.type,
        role=getattr(request.state, "api_role", None),
    )
    return ShareResponse(share_id=share_id)


@router.get("/share/{share_id}", dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
async def get_share(request: Request, share_id: str):
    payload = share_store.get_share(share_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Share not found or expired.")
    return payload


def _mask_key(value: str) -> str:
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:4]}...{value[-2:]}"


def _key_id(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


@router.get("/admin/summary", dependencies=[Depends(require_api_key), Depends(require_role("admin"))])
async def admin_summary():
    return metrics_snapshot()


@router.get("/admin/feedback", dependencies=[Depends(require_api_key), Depends(require_role("admin"))])
async def admin_feedback():
    summary = feedback_store.feedback_summary()
    recent = feedback_store.list_feedback(limit=20)
    return {"summary": summary, "recent": recent}


@router.get("/admin/config", dependencies=[Depends(require_api_key), Depends(require_role("admin"))])
async def admin_config():
    runtime = load_runtime_config()
    api_keys = runtime.get("api_keys", []) or []
    masked = [
        {
            "key": _mask_key(item.get("key", "")),
            "key_id": _key_id(item.get("key", "")),
            "role": item.get("role", "public"),
            "limits": item.get("limits", {}),
        }
        for item in api_keys
    ]
    return {
        "api_keys": masked,
        "rate_limits": runtime.get("rate_limits", {}),
        "project_access": runtime.get("project_access", {}),
    }


@router.post("/admin/keys", dependencies=[Depends(require_api_key), Depends(require_role("admin"))])
async def admin_add_key(entry: ApiKeyEntry):
    runtime = load_runtime_config()
    api_keys = runtime.get("api_keys", []) or []
    api_keys = [item for item in api_keys if item.get("key") != entry.key]
    api_keys.append(entry.model_dump())
    runtime["api_keys"] = api_keys
    save_runtime_config(runtime)
    log_event(
        "admin_add_key",
        key_id=_key_id(entry.key),
        role=entry.role,
    )
    return {"status": "ok", "key": _mask_key(entry.key), "key_id": _key_id(entry.key)}


@router.delete("/admin/keys/{key_id}", dependencies=[Depends(require_api_key), Depends(require_role("admin"))])
async def admin_delete_key(key_id: str):
    runtime = load_runtime_config()
    api_keys = runtime.get("api_keys", []) or []
    api_keys = [item for item in api_keys if _key_id(item.get("key", "")) != key_id]
    runtime["api_keys"] = api_keys
    save_runtime_config(runtime)
    log_event(
        "admin_delete_key",
        key_id=key_id,
    )
    return {"status": "ok"}


@router.post("/admin/rate-limits", dependencies=[Depends(require_api_key), Depends(require_role("admin"))])
async def admin_update_rate_limits(update: RateLimitUpdate):
    runtime = load_runtime_config()
    rate_limits = runtime.get("rate_limits", {}) or {}
    for key, value in update.model_dump(exclude_unset=True).items():
        if value:
            rate_limits[key] = value
    runtime["rate_limits"] = rate_limits
    save_runtime_config(runtime)
    log_event(
        "admin_update_rate_limits",
        rate_limits=rate_limits,
    )
    return {"status": "ok", "rate_limits": rate_limits}
