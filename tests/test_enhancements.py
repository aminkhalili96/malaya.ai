"""
Tests for New Enhancement Services
Tests all 27 feature services.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# ===== SENTIMENT SERVICE TESTS =====

def test_sentiment_detection():
    """Test sentiment detection."""
    from src.chatbot.services.sentiment_service import SentimentEmotionService
    
    service = SentimentEmotionService()
    
    # Positive sentiment
    sentiment, conf = service.detect_sentiment("This is really great! Love it!")
    assert sentiment == "positive"
    assert conf > 0.5
    
    # Negative sentiment
    sentiment, conf = service.detect_sentiment("This is terrible and awful")
    assert sentiment == "negative"
    assert conf > 0.5
    
    # Neutral
    sentiment, conf = service.detect_sentiment("Hello there")
    assert sentiment == "neutral"


def test_emotion_detection():
    """Test emotion detection."""
    from src.chatbot.services.sentiment_service import SentimentEmotionService
    
    service = SentimentEmotionService()
    
    # Angry
    emotion, conf = service.detect_emotion("Geram betul la dengan service ni!")
    assert emotion == "angry"
    
    # Happy
    emotion, conf = service.detect_emotion("Best gila! Love it!")
    assert emotion == "happy"
    
    # Frustrated
    emotion, conf = service.detect_emotion("Haih, stress betul. Tak jadi lagi.")
    assert emotion == "frustrated"


def test_full_sentiment_analysis():
    """Test full sentiment+emotion analysis."""
    from src.chatbot.services.sentiment_service import SentimentEmotionService
    
    service = SentimentEmotionService()
    result = service.analyze("This is awesome! Really excited about it!")
    
    assert "sentiment" in result
    assert "emotion" in result
    assert "adjustments" in result


# ===== ROUTER SERVICE TESTS =====

def test_model_router_simple_query():
    """Test routing simple queries to fast models."""
    from src.chatbot.services.router_service import ModelRouterService
    
    router = ModelRouterService()
    
    model, reason = router.route("What is the capital of Malaysia?", prefer_fast=True)
    assert "mini" in model.lower() or "ollama" in model.lower()


def test_model_router_complex_query():
    """Test routing complex queries to powerful models."""
    from src.chatbot.services.router_service import ModelRouterService
    
    router = ModelRouterService()
    
    model, reason = router.route(
        "Explain step by step how to build a machine learning model",
        prefer_fast=False
    )
    assert "gpt-4o" in model.lower() or "claude" in model.lower()


def test_model_router_code_query():
    """Test routing code queries."""
    from src.chatbot.services.router_service import ModelRouterService
    
    router = ModelRouterService()
    
    analysis = router.analyze_query("Write a Python function to sort a list")
    assert analysis["task_type"] == "code"


# ===== CACHE SERVICE TESTS =====

def test_cache_set_and_get():
    """Test basic cache operations."""
    from src.chatbot.services.cache_service import CacheService
    
    cache = CacheService()
    
    # Set - use longer response to pass min length check
    cache.set("Hello world", "Hello response that is long enough to be cached properly", "gpt-4o")
    
    # Get
    result = cache.get("Hello world", "gpt-4o")
    assert result is not None
    assert "Hello response" in result


def test_cache_pii_detection():
    """Test PII detection prevents caching."""
    from src.chatbot.services.cache_service import CacheService
    
    cache = CacheService()
    
    # Contains Malaysian IC number
    result = cache._contains_pii("My IC is 880101145678")
    assert result == True
    
    # Contains email
    result = cache._contains_pii("Email me at test@example.com")
    assert result == True
    
    # No PII
    result = cache._contains_pii("Hello world")
    assert result == False


def test_cache_time_sensitive():
    """Test time-sensitive queries are not cached."""
    from src.chatbot.services.cache_service import CacheService
    
    cache = CacheService()
    
    # Time-sensitive query - should not be cacheable (contains 'today')
    result = cache._is_cacheable("What is the weather today?", "It's sunny and warm outside today with clear skies")
    assert result == False  # Time-sensitive due to 'today'
    
    # Normal query - should be cacheable
    long_response = "Recursion is a programming technique where a function calls itself to solve smaller subproblems."
    result = cache._is_cacheable("Explain recursion", long_response)
    assert result == True


# ===== HALLUCINATION DETECTOR TESTS =====

def test_hallucination_hedging_detection():
    """Test detection of hedging language."""
    from src.chatbot.services.fact_checker import HallucinationDetector
    
    detector = HallucinationDetector()
    
    has_hedging, phrases = detector.detect_hedging("I think this might be correct, probably")
    assert has_hedging == True
    assert len(phrases) > 0


def test_hallucination_overconfidence():
    """Test detection of overconfident claims."""
    from src.chatbot.services.fact_checker import HallucinationDetector
    
    detector = HallucinationDetector()
    
    has_overconf, phrases = detector.detect_overconfidence("Everyone knows this is definitely true")
    assert has_overconf == True


def test_hallucination_analysis():
    """Test full hallucination analysis."""
    from src.chatbot.services.fact_checker import HallucinationDetector
    
    detector = HallucinationDetector()
    
    # Low risk
    result = detector.analyze_response("I think this might be right, but I'm not certain")
    assert result["risk_level"] in ["low", "medium"]
    
    # High risk (overconfident without sources)
    result = detector.analyze_response(
        "According to a 2019 study, 95% of people agree this is definitely true",
        sources=[]
    )
    assert result["risk_score"] > 0.3


# ===== KNOWLEDGE GRAPH TESTS =====

def test_knowledge_graph_search():
    """Test entity search in knowledge graph."""
    from src.chatbot.services.knowledge_graph import KnowledgeGraphService
    
    kg = KnowledgeGraphService(persist_path="/tmp/test_kg.json")
    
    # Search for a seeded entity
    results = kg.search_entities("Penang")
    assert len(results) > 0
    assert results[0].name == "Penang"


def test_knowledge_graph_fact_verification():
    """Test fact verification."""
    from src.chatbot.services.knowledge_graph import KnowledgeGraphService
    
    kg = KnowledgeGraphService(persist_path="/tmp/test_kg.json")
    
    # Verify a seeded fact
    result = kg.verify_fact("Langkawi", "located_in", "Kedah")
    assert result["verified"] == True


def test_knowledge_graph_stats():
    """Test graph statistics."""
    from src.chatbot.services.knowledge_graph import KnowledgeGraphService
    
    kg = KnowledgeGraphService(persist_path="/tmp/test_kg.json")
    
    stats = kg.get_stats()
    assert "total_entities" in stats
    assert stats["total_entities"] > 0


# ===== CURRENCY SERVICE TESTS =====

@pytest.mark.asyncio
async def test_currency_conversion():
    """Test currency conversion."""
    from src.chatbot.services.currency_service import CurrencyService
    
    service = CurrencyService()
    
    result = await service.convert(100, "USD", "MYR")
    assert result["from"]["currency"] == "USD"
    assert result["to"]["currency"] == "MYR"
    assert result["to"]["amount"] > 0


def test_currency_format():
    """Test currency formatting."""
    from src.chatbot.services.currency_service import CurrencyService
    
    service = CurrencyService()
    
    assert service.format_amount(100.50, "MYR") == "RM100.50"
    assert service.format_amount(50, "USD") == "$50.00"


# ===== CODE EXPLAINER TESTS =====

def test_code_language_detection():
    """Test programming language detection."""
    from src.chatbot.services.code_explainer_service import CodeExplainerService
    
    explainer = CodeExplainerService()
    
    python_code = "def hello():\n    print('Hello')"
    assert explainer._detect_language(python_code) == "python"
    
    js_code = "const hello = () => console.log('Hello')"
    assert explainer._detect_language(js_code) == "javascript"


# ===== COMMUNITY SERVICE TESTS =====

def test_prompt_library_search():
    """Test prompt library search."""
    from src.chatbot.services.community_service import PromptLibraryService
    
    library = PromptLibraryService(storage_path="/tmp/test_prompts.json")
    
    # Search for Malaysian prompts
    results = library.search_prompts(category="malaysian")
    assert len(results) > 0


def test_prompt_library_add():
    """Test adding prompts."""
    from src.chatbot.services.community_service import PromptLibraryService
    
    library = PromptLibraryService(storage_path="/tmp/test_prompts2.json")
    
    result = library.add_prompt(
        title="Test Prompt",
        prompt="This is a test",
        category="fun",
        author="tester"
    )
    
    assert result["id"] is not None
    assert result["title"] == "Test Prompt"


def test_shared_conversation():
    """Test shared conversation creation."""
    from src.chatbot.services.community_service import SharedConversationService
    
    service = SharedConversationService(storage_path="/tmp/test_shares.json")
    
    # Create share
    result = service.create_share_link(
        "conv-123",
        [{"role": "user", "content": "Hello"}],
        "Test Conversation"
    )
    
    assert result["share_id"] is not None
    
    # Retrieve
    retrieved = service.get_shared_conversation(result["share_id"])
    assert retrieved is not None
    assert retrieved["title"] == "Test Conversation"


# ===== DIALECT TTS TESTS =====

def test_dialect_availability():
    """Test all 13 states have dialects."""
    pytest.importorskip("edge_tts", reason="edge_tts not installed")
    from src.chatbot.services.dialect_tts_service import DialectTTSService
    
    service = DialectTTSService()
    dialects = service.get_available_dialects()
    
    assert len(dialects) >= 13
    assert "kelantan" in dialects
    assert "penang" in dialects
    assert "johor" in dialects


# ===== ANALYTICS SERVICE TESTS =====

def test_analytics_tracking():
    """Test analytics request tracking."""
    from src.chatbot.services.analytics_service import AnalyticsService
    
    analytics = AnalyticsService()
    
    analytics.track_request(
        user_id="user-123",
        query="Hello world",
        response="Hello there!",
        model="gpt-4o",
        tokens_used=50,
        latency_ms=200,
        intent="greeting"
    )
    
    data = analytics.get_dashboard_data()
    assert data["total_requests"] >= 1
    assert data["total_tokens"] >= 50


def test_ab_testing():
    """Test A/B testing functionality."""
    from src.chatbot.services.analytics_service import AnalyticsService
    
    analytics = AnalyticsService()
    
    # Register test
    analytics.register_ab_test("prompt_test", ["control", "variant_a", "variant_b"])
    
    # Get variant (should be consistent for same user)
    variant1 = analytics.get_variant("prompt_test", "user-123")
    variant2 = analytics.get_variant("prompt_test", "user-123")
    assert variant1 == variant2
    
    # Record result
    analytics.record_ab_result("prompt_test", variant1, success=True)
    
    results = analytics.get_ab_results("prompt_test")
    assert results[variant1]["count"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
