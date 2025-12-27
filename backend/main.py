"""
Malaya LLM API - FastAPI Backend
================================
Features:
- CORS: Environment-based configuration
- Rate Limiting: Prevents API abuse
- Health Check: Reports dependency status
"""

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.routers import chat
from backend.observability import attach_middleware, metrics_response

# Optional error monitoring (Sentry)
SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
        )
    except Exception:
        pass

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Malaya LLM API",
    version="2.1",
    description="Sovereign AI Copilot with Malaysian language understanding"
)

attach_middleware(app)

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
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Routers
# Routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# WebSocket for Real-Time Voice
from fastapi import WebSocket, WebSocketDisconnect
from src.voice.connection_manager import manager
from backend.routers.chat import get_chatbot

@app.websocket("/ws/voice/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    bot = get_chatbot()
    try:
        while True:
            data = await websocket.receive_text()
            # 1. Echo/State update
            await manager.send_personal_message({"status": "processing", "input": data}, client_id)
            
            # 2. Process via Chatbot
            # TODO: Add specific Voice Logic (VAD checking, etc)
            response = await bot.process_query(data, chat_history=[])
            
            # 3. Send Response
            await manager.send_personal_message({
                "status": "responded",
                "text": response["answer"],
                "audio_base64": None # TODO: Generate TTS here
            }, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)



@app.get("/health")
def health_check():
    """
    Enhanced health check that reports dependency status.
    Useful for Kubernetes readiness/liveness probes.
    """
    llm_configured = False
    llm_error = None
    try:
        bot = chat.get_chatbot()
        llm_configured = bot.llm is not None and not bot.llm_error
        llm_error = bot.llm_error
    except Exception as exc:
        llm_error = str(exc)

    return {
        "status": "ok",
        "version": "2.1",
        "dependencies": {
            "llm_configured": llm_configured,
            "llm_error": llm_error,
            "search_configured": bool(os.environ.get("TAVILY_API_KEY")),
        }
    }


@app.get("/metrics")
def metrics():
    return metrics_response()

# ===== NEW FEATURE ENDPOINTS =====

from pydantic import BaseModel
from typing import Optional
from fastapi.responses import FileResponse, JSONResponse

# --- Snap & Translate ---
class TranslateImageRequest(BaseModel):
    image_base64: str
    target_language: str = "English"

@app.post("/api/vision/translate")
async def translate_image(request: TranslateImageRequest):
    """
    Translates text in an image (signboards, menus, etc.)
    """
    from src.chatbot.services.vision_service import VisionService
    vision = VisionService()
    result = await vision.translate_image(
        request.image_base64, 
        request.target_language
    )
    return result

@app.post("/api/vision/menu")
async def analyze_menu(request: TranslateImageRequest):
    """
    Analyzes a menu image and extracts items with prices.
    """
    from src.chatbot.services.vision_service import VisionService
    vision = VisionService()
    result = await vision.analyze_menu(request.image_base64)
    return result

# --- Podcast Mode ---
class PodcastRequest(BaseModel):
    url: str
    voice: str = "malay_female"
    summarize: bool = True

@app.post("/api/podcast/create")
async def create_podcast(request: PodcastRequest):
    """
    Creates a podcast summary of an article URL.
    Returns audio file path and summary text.
    """
    from src.chatbot.services.podcast_service import PodcastService
    bot = chat.get_chatbot()
    podcast = PodcastService(llm=bot.llm)
    result = await podcast.create_podcast(
        request.url,
        voice=request.voice,
        summarize=request.summarize
    )
    return result

@app.get("/api/podcast/audio/{filename}")
async def get_podcast_audio(filename: str):
    """
    Serves the generated audio file.
    """
    import tempfile
    audio_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/mpeg")
    return JSONResponse({"error": "Audio not found"}, status_code=404)

# --- Agent Mode (Multi-Step Tasks) ---
class AgentTaskRequest(BaseModel):
    task: str

@app.post("/api/agent/execute")
async def execute_agent_task(request: AgentTaskRequest):
    """
    Executes a multi-step task using the TaskAgent.
    Example: "Find a restaurant in KLCC, then get directions"
    """
    from src.chatbot.agents.task_agent import TaskAgent
    bot = chat.get_chatbot()
    agent = TaskAgent(llm=bot.llm, mcp_manager=bot.mcp_manager)
    result = await agent.execute(request.task)
    return result

# --- Tourist Mode ---
class TouristRequest(BaseModel):
    location: str
    days: int = 2
    interests: Optional[str] = None

@app.post("/api/tourist/itinerary")
async def generate_tourist_itinerary(request: TouristRequest):
    """
    Generates a tourist itinerary for a given location.
    """
    bot = chat.get_chatbot()
    prompt = f"""Create a detailed {request.days}-day tourist itinerary for {request.location}.
Focus on:
- Hidden gems and local favorites (not just tourist traps)
- Mix of food, culture, and sightseeing
- Practical timing and transportation tips
{"- Special interests: " + request.interests if request.interests else ""}

Format as a day-by-day schedule with times, locations, and brief descriptions."""
    
    response = await bot.llm.ainvoke(prompt)
    return {
        "location": request.location,
        "days": request.days,
        "itinerary": response.content if hasattr(response, 'content') else str(response)
    }

# ===== PHASE 2: NEW FEATURE ENDPOINTS =====

# --- Analytics ---
@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard():
    """Get analytics dashboard data."""
    from src.chatbot.services.analytics_service import analytics
    return analytics.get_dashboard_data()

# --- Streaming ---
from fastapi.responses import StreamingResponse

class StreamRequest(BaseModel):
    prompt: str
    model: Optional[str] = None

@app.post("/api/chat/stream")
async def stream_chat(request: StreamRequest):
    """Stream chat response using SSE."""
    from src.chatbot.services.streaming_service import streaming
    bot = chat.get_chatbot()
    
    async def generate():
        async for chunk in streaming.stream_tokens(bot.llm, request.prompt):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# --- Price Comparison ---
class PriceCompareRequest(BaseModel):
    query: str
    max_budget: Optional[float] = None
    max_results: int = 5

@app.post("/api/price/compare")
async def compare_prices(request: PriceCompareRequest):
    """Compare prices across Shopee and Lazada."""
    from src.chatbot.services.price_service import price_service
    return await price_service.compare_prices(
        request.query,
        request.max_budget,
        request.max_results
    )

# --- Currency Conversion ---
class CurrencyRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

@app.post("/api/currency/convert")
async def convert_currency(request: CurrencyRequest):
    """Convert currency with MYR support."""
    from src.chatbot.services.currency_service import currency_service
    return await currency_service.convert(
        request.amount,
        request.from_currency,
        request.to_currency
    )

@app.get("/api/currency/rates")
async def get_currency_rates():
    """Get MYR exchange rates."""
    from src.chatbot.services.currency_service import currency_service
    return await currency_service.get_myr_rates()

# --- Transcription & Meeting Summarizer ---
class TranscribeRequest(BaseModel):
    audio_base64: str
    filename: str = "audio.mp3"
    language: Optional[str] = None

@app.post("/api/transcribe")
async def transcribe_audio(request: TranscribeRequest):
    """Transcribe audio file."""
    from src.chatbot.services.transcription_service import transcription_service
    import base64
    
    audio_bytes = base64.b64decode(request.audio_base64)
    return await transcription_service.transcribe_bytes(
        audio_bytes,
        request.filename,
        request.language
    )

class SummarizeMeetingRequest(BaseModel):
    transcription: str

@app.post("/api/meeting/summarize")
async def summarize_meeting(request: SummarizeMeetingRequest):
    """Summarize meeting transcription."""
    from src.chatbot.services.transcription_service import transcription_service
    return await transcription_service.summarize_meeting(request.transcription)

# --- Dialect TTS ---
class DialectTTSRequest(BaseModel):
    text: str
    state: str = "selangor"

@app.post("/api/tts/dialect")
async def generate_dialect_tts(request: DialectTTSRequest):
    """Generate TTS with state dialect."""
    from src.chatbot.services.dialect_tts_service import dialect_tts
    path = await dialect_tts.generate_dialect_audio(request.text, request.state)
    return FileResponse(path, media_type="audio/mpeg")

@app.get("/api/tts/dialects")
async def list_dialects():
    """List available dialects."""
    from src.chatbot.services.dialect_tts_service import dialect_tts
    return {"dialects": dialect_tts.get_available_dialects()}

# --- Receipt Scanner ---
class ReceiptRequest(BaseModel):
    image_base64: str

@app.post("/api/receipt/scan")
async def scan_receipt(request: ReceiptRequest):
    """Scan and extract data from receipt."""
    from src.chatbot.services.receipt_service import receipt_scanner
    return await receipt_scanner.scan_receipt(request.image_base64)

# --- Document Q&A ---
class DocumentQueryRequest(BaseModel):
    doc_id: str
    question: str

@app.post("/api/document/query")
async def query_document(request: DocumentQueryRequest):
    """Query an ingested document."""
    from src.chatbot.services.document_qa_service import document_qa
    return await document_qa.query(request.doc_id, request.question)

@app.get("/api/document/list")
async def list_documents():
    """List ingested documents."""
    from src.chatbot.services.document_qa_service import document_qa
    return {"documents": document_qa.list_documents()}

# --- Code Explainer ---
class CodeExplainRequest(BaseModel):
    code: str
    language: str = "auto"
    style: str = "manglish"

@app.post("/api/code/explain")
async def explain_code(request: CodeExplainRequest):
    """Explain code in Manglish style."""
    from src.chatbot.services.code_explainer_service import code_explainer
    bot = chat.get_chatbot()
    code_explainer.llm = bot.llm
    return await code_explainer.explain(request.code, request.language, request.style)

# --- Meme Generator ---
class MemeRequest(BaseModel):
    topic: str
    style: str = "cartoon"

@app.post("/api/meme/generate")
async def generate_meme(request: MemeRequest):
    """Generate a meme from topic."""
    from src.chatbot.services.meme_service import meme_generator
    return await meme_generator.full_meme_generation(request.topic, request.style)

# --- Shared Conversations ---
class ShareRequest(BaseModel):
    conversation_id: str
    messages: list
    title: Optional[str] = None

@app.post("/api/share/create")
async def create_share_link(request: ShareRequest):
    """Create shareable link for conversation."""
    from src.chatbot.services.community_service import shared_conversations
    return shared_conversations.create_share_link(
        request.conversation_id,
        request.messages,
        request.title
    )

@app.get("/api/share/{share_id}")
async def get_shared_conversation(share_id: str):
    """Get shared conversation by ID."""
    from src.chatbot.services.community_service import shared_conversations
    result = shared_conversations.get_shared_conversation(share_id)
    if not result:
        return JSONResponse({"error": "Not found or expired"}, status_code=404)
    return result

# --- Prompt Library ---
@app.get("/api/prompts/popular")
async def get_popular_prompts():
    """Get popular community prompts."""
    from src.chatbot.services.community_service import prompt_library
    return {"prompts": prompt_library.get_popular(10)}

@app.get("/api/prompts/search")
async def search_prompts(query: Optional[str] = None, category: Optional[str] = None):
    """Search prompt library."""
    from src.chatbot.services.community_service import prompt_library
    return {"prompts": prompt_library.search_prompts(query, category)}

# --- Sentiment & Emotion ---
class SentimentRequest(BaseModel):
    text: str

@app.post("/api/sentiment/analyze")
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment and emotion."""
    from src.chatbot.services.sentiment_service import sentiment_service
    return sentiment_service.analyze(request.text)

# --- Fact Checker ---
class FactCheckRequest(BaseModel):
    claim: str
    sources: Optional[list] = None

@app.post("/api/factcheck")
async def check_fact(request: FactCheckRequest):
    """Check factual claims."""
    from src.chatbot.services.fact_checker import fact_checker
    return await fact_checker.verify_claim(request.claim, request.sources)

# --- Knowledge Graph ---
@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge graph statistics."""
    from src.chatbot.services.knowledge_graph import knowledge_graph
    return knowledge_graph.get_stats()

class KGSearchRequest(BaseModel):
    query: str
    entity_type: Optional[str] = None

@app.post("/api/knowledge/search")
async def search_knowledge(request: KGSearchRequest):
    """Search knowledge graph."""
    from src.chatbot.services.knowledge_graph import knowledge_graph
    entities = knowledge_graph.search_entities(request.query, request.entity_type)
    return {"entities": [{"id": e.id, "name": e.name, "type": e.entity_type} for e in entities]}

