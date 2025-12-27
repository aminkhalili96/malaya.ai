"""
Cache Service - Response caching with TTL and PII awareness
"""
import hashlib
import json
import time
from typing import Optional, Any, Dict
from functools import lru_cache
import re

# PII patterns
PII_PATTERNS = [
    r'\b\d{12}\b',  # Malaysian IC
    r'\b\d{10,11}\b',  # Phone numbers
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    r'\b\d{16}\b',  # Credit card
]

class CacheService:
    """
    Intelligent response caching with:
    - TTL-based expiration
    - PII detection (skip caching if PII present)
    - Semantic key generation
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, query: str, model: str, context_hash: str = "") -> str:
        """Generate cache key from query and context."""
        normalized = query.lower().strip()
        key_input = f"{model}:{normalized}:{context_hash}"
        return hashlib.sha256(key_input.encode()).hexdigest()[:32]
    
    def _contains_pii(self, text: str) -> bool:
        """Check if text contains PII."""
        for pattern in PII_PATTERNS:
            if re.search(pattern, text):
                return True
        return False
    
    def _is_cacheable(self, query: str, response: str) -> bool:
        """Determine if a query/response pair should be cached."""
        # Don't cache if PII present
        if self._contains_pii(query) or self._contains_pii(response):
            return False
        
        # Don't cache very short responses (likely errors) - skip in test mode
        if len(response) < 10:
            return False
        
        # Don't cache time-sensitive queries
        time_keywords = ["now", "today", "current", "latest", "sekarang", "hari ini"]
        if any(kw in query.lower() for kw in time_keywords):
            return False
        
        return True
    
    def get(self, query: str, model: str, context_hash: str = "") -> Optional[str]:
        """Retrieve cached response if valid."""
        key = self._generate_key(query, model, context_hash)
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry["expires_at"]:
                self.hits += 1
                return entry["response"]
            else:
                # Expired, remove
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(
        self,
        query: str,
        response: str,
        model: str,
        context_hash: str = "",
        ttl: Optional[int] = None
    ) -> bool:
        """Cache a response."""
        if not self._is_cacheable(query, response):
            return False
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache, key=lambda k: self.cache[k]["created_at"])
            del self.cache[oldest_key]
        
        key = self._generate_key(query, model, context_hash)
        self.cache[key] = {
            "response": response,
            "created_at": time.time(),
            "expires_at": time.time() + (ttl or self.default_ttl),
            "model": model,
        }
        return True
    
    def invalidate(self, pattern: Optional[str] = None):
        """Invalidate cache entries matching pattern, or all if no pattern."""
        if pattern is None:
            self.cache.clear()
        else:
            keys_to_remove = [k for k in self.cache if pattern in k]
            for k in keys_to_remove:
                del self.cache[k]
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total * 100 if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
        }


# Global instance
cache = CacheService()
