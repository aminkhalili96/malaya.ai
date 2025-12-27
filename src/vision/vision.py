"""
vision.py - Malaysian Image Understanding Module

This module provides vision/image capabilities for Malaya LLM:
- Image analysis with Malaysian context
- Malaysian food recognition
- Signage/text OCR (BM/EN/CN/Tamil)
- Meme understanding

Uses OpenAI GPT-4 Vision (gpt-4o) for image understanding.
"""

import base64
import os
from typing import Optional, List
from dataclasses import dataclass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False


@dataclass
class VisionConfig:
    """Configuration for vision services."""
    model: str = "gpt-4o"  # GPT-4 with vision
    max_tokens: int = 500
    detail: str = "auto"  # "auto", "low", "high"


class MalaysianVisionAnalyzer:
    """
    Malaysian Image Understanding using GPT-4 Vision.
    
    Features:
    - General image analysis with Malaysian context
    - Malaysian food recognition (nasi lemak, roti canai, etc.)
    - Signage/text OCR (Malay, English, Chinese, Tamil)
    - Meme understanding with cultural context
    """
    
    SYSTEM_PROMPT = """You are a Malaysian AI that understands local context.
When analyzing images, consider:
- Malaysian foods (nasi lemak, roti canai, satay, rendang, char kuey teow, etc.)
- Malaysian locations (KLCC, Penang, Melaka, Langkawi, etc.)
- Malaysian signage in multiple languages (Malay, English, Chinese, Tamil)
- Malaysian culture and customs (festivals, traditions, daily life)
- Malaysian products and brands
- Malaysian memes and humor

If you see text in the image, read it and provide translations if not in the user's language.
Always provide culturally relevant context for Malaysian users.
Be casual, friendly, and use Malaysian expressions where appropriate."""

    FOOD_PROMPT = """You are a Malaysian food expert AI.
Identify Malaysian foods in images with:
- Exact dish name (e.g., "Nasi Lemak", "Char Kuey Teow")
- Key ingredients visible
- Regional variations if detectable (e.g., "Penang-style", "Ipoh version")
- Approximate price range if possible
- Best places known for this dish
- Cultural context (when is this typically eaten)"""

    MEME_PROMPT = """You are a Malaysian meme and pop culture expert.
When analyzing Malaysian memes:
- Explain the joke/humor
- Identify any Malaysian celebrities or public figures
- Explain cultural references that non-Malaysians might not understand
- Translate any Malay/Manglish text
- Describe the meme format and its popularity"""

    OCR_PROMPT = """You are a Malaysian OCR specialist.
Extract and translate all text from this image:
- Identify the language(s): Malay, English, Chinese, Tamil, or mixed
- Provide exact transcription
- Translate non-English text to English
- Note any signage, labels, or documents visible
- Identify if this is a government form, advertisement, menu, etc."""

    def __init__(self, config: Optional[VisionConfig] = None):
        self.config = config or VisionConfig()
        self._client = None
        
        if OPENAI_AVAILABLE:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self._client = OpenAI()
    
    @property
    def is_available(self) -> bool:
        return self._client is not None
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_image_url(self, image_input: str) -> dict:
        """
        Get image URL dict for OpenAI API.
        
        Args:
            image_input: Either a file path, base64 string, or URL
            
        Returns:
            Dict with "url" key for OpenAI API
        """
        if image_input.startswith(("http://", "https://")):
            # Already a URL
            return {"url": image_input}
        elif os.path.exists(image_input):
            # File path - encode to base64
            base64_image = self._encode_image(image_input)
            # Detect mime type
            ext = image_input.lower().split(".")[-1]
            mime_type = {
                "jpg": "jpeg",
                "jpeg": "jpeg",
                "png": "png",
                "gif": "gif",
                "webp": "webp"
            }.get(ext, "jpeg")
            return {"url": f"data:image/{mime_type};base64,{base64_image}"}
        else:
            # Assume it's already base64
            return {"url": f"data:image/jpeg;base64,{image_input}"}
    
    def analyze(
        self, 
        image_input: str,
        question: Optional[str] = None,
        mode: str = "general"  # "general", "food", "meme", "ocr"
    ) -> dict:
        """
        Analyze an image with Malaysian context.
        
        Args:
            image_input: File path, URL, or base64 string
            question: Optional specific question about the image
            mode: Analysis mode ("general", "food", "meme", "ocr")
            
        Returns:
            Dict with analysis results
        """
        if not self.is_available:
            return {
                "error": "Vision service not available",
                "available": False
            }
        
        # Select system prompt based on mode
        system_prompts = {
            "general": self.SYSTEM_PROMPT,
            "food": self.FOOD_PROMPT,
            "meme": self.MEME_PROMPT,
            "ocr": self.OCR_PROMPT
        }
        system_prompt = system_prompts.get(mode, self.SYSTEM_PROMPT)
        
        # Build user message
        user_content = []
        
        if question:
            user_content.append({
                "type": "text",
                "text": question
            })
        else:
            # Default questions based on mode
            default_questions = {
                "general": "What do you see in this image?",
                "food": "What Malaysian food is this? Describe it in detail.",
                "meme": "Explain this meme, including any Malaysian cultural references.",
                "ocr": "Extract and translate all text from this image."
            }
            user_content.append({
                "type": "text",
                "text": default_questions.get(mode, "What do you see?")
            })
        
        # Add image
        user_content.append({
            "type": "image_url",
            "image_url": self._get_image_url(image_input)
        })
        
        # Make API call
        try:
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=self.config.max_tokens
            )
            
            return {
                "analysis": response.choices[0].message.content,
                "mode": mode,
                "model": self.config.model,
                "available": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "available": True
            }
    
    def analyze_food(self, image_input: str) -> dict:
        """Analyze Malaysian food in image."""
        return self.analyze(image_input, mode="food")
    
    def analyze_meme(self, image_input: str) -> dict:
        """Analyze Malaysian meme."""
        return self.analyze(image_input, mode="meme")
    
    def extract_text(self, image_input: str) -> dict:
        """Extract and translate text from image."""
        return self.analyze(image_input, mode="ocr")
    
    def compare_images(
        self, 
        images: List[str],
        question: Optional[str] = None
    ) -> dict:
        """
        Compare multiple images.
        
        Args:
            images: List of image paths, URLs, or base64 strings
            question: Comparison question
            
        Returns:
            Dict with comparison results
        """
        if not self.is_available:
            return {"error": "Vision service not available", "available": False}
        
        if len(images) > 3:
            images = images[:3]  # Limit to 3 images
        
        # Build content with multiple images
        user_content = [
            {"type": "text", "text": question or "Compare these images."}
        ]
        
        for img in images:
            user_content.append({
                "type": "image_url",
                "image_url": self._get_image_url(img)
            })
        
        try:
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=self.config.max_tokens
            )
            
            return {
                "comparison": response.choices[0].message.content,
                "image_count": len(images),
                "available": True
            }
        except Exception as e:
            return {"error": str(e), "available": True}


# ============================================================================
# Convenience functions
# ============================================================================

def analyze_malaysian_image(image_input: str, question: Optional[str] = None) -> str:
    """Quick function to analyze an image with Malaysian context."""
    analyzer = MalaysianVisionAnalyzer()
    result = analyzer.analyze(image_input, question)
    return result.get("analysis", result.get("error", "Analysis failed"))


def identify_malaysian_food(image_input: str) -> str:
    """Quick function to identify Malaysian food in an image."""
    analyzer = MalaysianVisionAnalyzer()
    result = analyzer.analyze_food(image_input)
    return result.get("analysis", result.get("error", "Analysis failed"))


# ============================================================================
# Demo
# ============================================================================

if __name__ == "__main__":
    print("Malaysian Vision Module")
    print("="*50)
    
    analyzer = MalaysianVisionAnalyzer()
    print(f"Vision Available: {analyzer.is_available}")
    
    if not analyzer.is_available:
        print("Note: Set OPENAI_API_KEY to enable vision features")
    
    print("\nSupported modes:")
    print("  - general: General image analysis with MY context")
    print("  - food: Malaysian food recognition")
    print("  - meme: Malaysian meme understanding")
    print("  - ocr: Text extraction and translation")
