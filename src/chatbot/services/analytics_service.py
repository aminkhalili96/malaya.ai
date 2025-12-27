"""
Analytics Service - Langfuse Integration + Custom Metrics
Tracks LLM calls, user behavior, and system performance.
"""
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Langfuse for LLM tracing
try:
    from langfuse import Langfuse
    from langfuse.callback import CallbackHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

class AnalyticsService:
    """
    Unified analytics service for LLM tracing, user metrics, and A/B testing.
    """
    
    def __init__(self):
        self.langfuse = None
        if LANGFUSE_AVAILABLE and os.getenv("LANGFUSE_PUBLIC_KEY"):
            self.langfuse = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            )
        
        # In-memory metrics (for quick access, persist to DB for production)
        self.metrics = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_latency_ms": 0,
            "intents": {},
            "models_used": {},
            "errors": 0,
            "hallucination_flags": 0,
        }
        
        # A/B test variants
        self.ab_tests = {}
        
    def get_langfuse_handler(self, trace_id: Optional[str] = None) -> Optional[Any]:
        """Get Langfuse callback handler for LangChain."""
        if not LANGFUSE_AVAILABLE or not self.langfuse:
            return None
        return CallbackHandler(trace_id=trace_id)
    
    def track_request(
        self,
        user_id: str,
        query: str,
        response: str,
        model: str,
        tokens_used: int,
        latency_ms: float,
        intent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Track a chat request for analytics."""
        self.metrics["total_requests"] += 1
        self.metrics["total_tokens"] += tokens_used
        self.metrics["total_latency_ms"] += latency_ms
        
        # Track model usage
        self.metrics["models_used"][model] = self.metrics["models_used"].get(model, 0) + 1
        
        # Track intents
        if intent:
            self.metrics["intents"][intent] = self.metrics["intents"].get(intent, 0) + 1
        
        # Log to Langfuse if available
        if self.langfuse:
            self.langfuse.trace(
                name="chat_request",
                user_id=user_id,
                input=query,
                output=response,
                metadata={
                    "model": model,
                    "tokens": tokens_used,
                    "latency_ms": latency_ms,
                    "intent": intent,
                    **(metadata or {})
                }
            )
    
    def track_error(self, error_type: str, message: str, trace_id: Optional[str] = None):
        """Track errors for monitoring."""
        self.metrics["errors"] += 1
        if self.langfuse and trace_id:
            self.langfuse.event(
                trace_id=trace_id,
                name="error",
                metadata={"type": error_type, "message": message}
            )
    
    def track_hallucination(self, query: str, response: str, confidence: float):
        """Track potential hallucinations."""
        self.metrics["hallucination_flags"] += 1
        if self.langfuse:
            self.langfuse.event(
                name="hallucination_detected",
                metadata={
                    "query": query[:200],
                    "response": response[:200],
                    "confidence": confidence
                }
            )
    
    def get_dashboard_data(self) -> Dict:
        """Get data for analytics dashboard."""
        avg_latency = (
            self.metrics["total_latency_ms"] / self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0 else 0
        )
        
        return {
            "total_requests": self.metrics["total_requests"],
            "total_tokens": self.metrics["total_tokens"],
            "average_latency_ms": round(avg_latency, 2),
            "error_rate": (
                self.metrics["errors"] / self.metrics["total_requests"] * 100
                if self.metrics["total_requests"] > 0 else 0
            ),
            "top_intents": sorted(
                self.metrics["intents"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "models_distribution": self.metrics["models_used"],
            "hallucination_rate": (
                self.metrics["hallucination_flags"] / self.metrics["total_requests"] * 100
                if self.metrics["total_requests"] > 0 else 0
            ),
        }
    
    # --- A/B Testing ---
    
    def register_ab_test(self, test_name: str, variants: list):
        """Register an A/B test."""
        self.ab_tests[test_name] = {
            "variants": variants,
            "results": {v: {"count": 0, "success": 0} for v in variants}
        }
    
    def get_variant(self, test_name: str, user_id: str) -> str:
        """Get consistent variant for a user."""
        if test_name not in self.ab_tests:
            return "control"
        
        # Simple hash-based assignment
        variants = self.ab_tests[test_name]["variants"]
        idx = hash(f"{test_name}:{user_id}") % len(variants)
        return variants[idx]
    
    def record_ab_result(self, test_name: str, variant: str, success: bool):
        """Record A/B test result."""
        if test_name in self.ab_tests:
            self.ab_tests[test_name]["results"][variant]["count"] += 1
            if success:
                self.ab_tests[test_name]["results"][variant]["success"] += 1
    
    def get_ab_results(self, test_name: str) -> Dict:
        """Get A/B test results."""
        if test_name not in self.ab_tests:
            return {}
        
        results = {}
        for variant, data in self.ab_tests[test_name]["results"].items():
            success_rate = data["success"] / data["count"] * 100 if data["count"] > 0 else 0
            results[variant] = {
                "count": data["count"],
                "success": data["success"],
                "success_rate": round(success_rate, 2)
            }
        return results


# Global instance
analytics = AnalyticsService()
