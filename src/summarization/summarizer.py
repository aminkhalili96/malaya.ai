from typing import Dict

class AdaptiveSummarizer:
    def __init__(self):
        self.context_window = 128000 # Qwen-2.5 128k
        
    def summarize(self, text: str) -> Dict[str, str]:
        """
         adaptive strategy:
         - Short (<128k tokens): Full Context
         - Long (>128k tokens): Map-Reduce (Simulated)
        """
        # Simple token count simulation (1 word approx 1.3 tokens)
        token_count = len(text.split()) * 1.3
        
        strategy = "Long Context (Qwen-2.5)"
        if token_count > self.context_window:
            strategy = "Map-Reduce"
            summary = "Simulated Map-Reduce Summary: [Content too long, summarized by parts...]"
        else:
            summary = f"Simulated Qwen-2.5 Summary: This document discusses {text[:50]}... (grounded in context)."
            
        return {
            "strategy": strategy,
            "summary": summary,
            "token_count": int(token_count)
        }
