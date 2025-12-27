"""
Code Explainer Service
Explains code in Manglish style.
"""
from typing import Dict, Optional

class CodeExplainerService:
    """
    Explains code in a friendly, Malaysian style.
    """
    
    LANGUAGE_EMOJIS = {
        "python": "🐍",
        "javascript": "🟨",
        "typescript": "💙",
        "java": "☕",
        "sql": "🗃️",
        "html": "🌐",
        "css": "🎨",
        "go": "🐹",
        "rust": "🦀",
        "c": "⚙️",
        "cpp": "⚙️",
    }
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def explain(
        self,
        code: str,
        language: str = "auto",
        style: str = "manglish"
    ) -> Dict:
        """
        Explain code in the specified style.
        
        Args:
            code: Code to explain
            language: Programming language (or "auto" to detect)
            style: Explanation style ("manglish", "formal", "simple")
        """
        # Detect language if not specified
        if language == "auto":
            language = self._detect_language(code)
        
        emoji = self.LANGUAGE_EMOJIS.get(language.lower(), "💻")
        
        # Build prompt based on style
        if style == "manglish":
            style_instruction = """Explain like you're a Malaysian programmer chatting with a friend.
Use Manglish (mix of English and Malay slang).
Use phrases like "eh bro", "macam ni la", "senang je", "confirm boleh punya".
Keep it casual but accurate."""
        elif style == "formal":
            style_instruction = "Explain in clear, professional English."
        else:  # simple
            style_instruction = "Explain like I'm a beginner. Use simple words and analogies."
        
        prompt = f"""Explain this {language} code:

```{language}
{code}
```

{style_instruction}

Provide:
1. What the code does (1-2 sentences)
2. Line by line explanation (brief bullet points)
3. Any potential issues or improvements

Keep the explanation concise and practical."""

        if self.llm:
            response = await self.llm.ainvoke(prompt)
            explanation = response.content if hasattr(response, 'content') else str(response)
        else:
            explanation = "LLM not configured. Please set up the language model."
        
        return {
            "language": language,
            "emoji": emoji,
            "style": style,
            "explanation": explanation,
            "lines_of_code": len(code.strip().split("\n"))
        }
    
    def _detect_language(self, code: str) -> str:
        """Simple language detection based on keywords."""
        code_lower = code.lower()
        
        patterns = {
            "python": ["def ", "import ", "print(", "if __name__"],
            "javascript": ["const ", "let ", "function ", "=>", "console.log"],
            "typescript": ["interface ", ": string", ": number", "type "],
            "java": ["public class", "public static", "System.out"],
            "sql": ["select ", "from ", "where ", "join "],
            "html": ["<html", "<div", "<body", "<!doctype"],
            "css": ["{", "}", "color:", "margin:", "padding:"],
            "go": ["func ", "package ", "import (", ":="],
            "rust": ["fn ", "let mut", "impl ", "use "],
        }
        
        for lang, keywords in patterns.items():
            matches = sum(1 for kw in keywords if kw in code_lower)
            if matches >= 2:
                return lang
        
        return "unknown"
    
    async def suggest_improvements(self, code: str, language: str = "auto") -> Dict:
        """
        Suggest improvements for the code.
        """
        if language == "auto":
            language = self._detect_language(code)
        
        prompt = f"""Review this {language} code and suggest improvements:

```{language}
{code}
```

Focus on:
1. Code quality and readability
2. Performance optimizations
3. Security concerns
4. Best practices

Keep suggestions practical and actionable."""

        if self.llm:
            response = await self.llm.ainvoke(prompt)
            suggestions = response.content if hasattr(response, 'content') else str(response)
        else:
            suggestions = "LLM not configured."
        
        return {
            "language": language,
            "suggestions": suggestions
        }


# Global instance
code_explainer = CodeExplainerService()
