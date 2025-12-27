"""
Multi-Model Router Service
Routes queries to appropriate models based on complexity and type.
"""
from typing import Dict, Tuple, Optional
import re

class ModelRouterService:
    """
    Intelligently routes queries to the best model based on:
    - Query complexity
    - Task type (code, creative, factual)
    - Cost optimization
    """
    
    # Model capabilities
    MODELS = {
        "gpt-4o": {
            "speed": "slow",
            "cost": "high",
            "capabilities": ["complex", "code", "creative", "vision", "reasoning"],
            "max_tokens": 128000
        },
        "gpt-4o-mini": {
            "speed": "fast",
            "cost": "low",
            "capabilities": ["simple", "factual", "translation"],
            "max_tokens": 128000
        },
        "claude-3-5-sonnet": {
            "speed": "medium",
            "cost": "medium",
            "capabilities": ["complex", "code", "creative", "long-form"],
            "max_tokens": 200000
        },
        "ollama:qwen3:14b": {
            "speed": "fast",
            "cost": "free",
            "capabilities": ["simple", "malay", "chat"],
            "max_tokens": 32000
        }
    }
    
    # Keywords indicating complexity
    COMPLEX_KEYWORDS = [
        "explain", "analyze", "compare", "why", "how does",
        "step by step", "in detail", "comprehensive", "terangkan"
    ]
    
    CODE_KEYWORDS = [
        "code", "function", "class", "bug", "error", "debug",
        "python", "javascript", "sql", "api", "script"
    ]
    
    CREATIVE_KEYWORDS = [
        "write", "create", "generate", "story", "poem", "letter",
        "email", "draft", "compose", "tulis", "cipta"
    ]
    
    SIMPLE_KEYWORDS = [
        "what is", "who is", "when", "where", "apa", "siapa",
        "bila", "mana", "define", "list"
    ]
    
    def analyze_query(self, query: str) -> Dict:
        """
        Analyze query to determine routing parameters.
        """
        query_lower = query.lower()
        
        # Determine complexity
        is_complex = any(kw in query_lower for kw in self.COMPLEX_KEYWORDS)
        is_code = any(kw in query_lower for kw in self.CODE_KEYWORDS)
        is_creative = any(kw in query_lower for kw in self.CREATIVE_KEYWORDS)
        is_simple = any(kw in query_lower for kw in self.SIMPLE_KEYWORDS)
        
        # Check query length
        word_count = len(query.split())
        is_long_query = word_count > 100
        
        # Determine task type
        if is_code:
            task_type = "code"
        elif is_creative:
            task_type = "creative"
        elif is_complex:
            task_type = "reasoning"
        else:
            task_type = "factual"
        
        # Determine complexity level
        if is_complex or is_long_query:
            complexity = "high"
        elif is_simple and word_count < 20:
            complexity = "low"
        else:
            complexity = "medium"
        
        return {
            "task_type": task_type,
            "complexity": complexity,
            "word_count": word_count,
            "requires_vision": False,  # Can be enhanced with image detection
        }
    
    def route(
        self, 
        query: str, 
        prefer_fast: bool = False,
        prefer_cheap: bool = False,
        available_models: list = None
    ) -> Tuple[str, str]:
        """
        Route query to best model.
        Returns (model_name, reason).
        """
        analysis = self.analyze_query(query)
        available = available_models or list(self.MODELS.keys())
        
        # Filter to available models
        candidates = {k: v for k, v in self.MODELS.items() if k in available}
        
        if not candidates:
            return ("gpt-4o-mini", "fallback")
        
        # Scoring
        scores = {}
        for model, specs in candidates.items():
            score = 0
            
            # Task type matching
            if analysis["task_type"] in specs["capabilities"]:
                score += 3
            if "complex" in specs["capabilities"] and analysis["complexity"] == "high":
                score += 2
            if "simple" in specs["capabilities"] and analysis["complexity"] == "low":
                score += 2
            
            # Speed preference
            if prefer_fast:
                if specs["speed"] == "fast":
                    score += 2
                elif specs["speed"] == "slow":
                    score -= 1
            
            # Cost preference
            if prefer_cheap:
                if specs["cost"] == "free":
                    score += 3
                elif specs["cost"] == "low":
                    score += 2
                elif specs["cost"] == "high":
                    score -= 1
            
            scores[model] = score
        
        # Select best model
        best_model = max(scores, key=scores.get)
        
        # Generate reason
        if analysis["complexity"] == "low" and "mini" in best_model:
            reason = "Simple query → fast model"
        elif analysis["task_type"] == "code":
            reason = "Code task → specialized model"
        elif analysis["complexity"] == "high":
            reason = "Complex reasoning → powerful model"
        else:
            reason = "Balanced selection"
        
        return (best_model, reason)
    
    def get_routing_stats(self, queries: list) -> Dict:
        """
        Analyze routing distribution for a list of queries.
        """
        distribution = {}
        for query in queries:
            model, _ = self.route(query)
            distribution[model] = distribution.get(model, 0) + 1
        
        return distribution


# Global instance
router = ModelRouterService()
