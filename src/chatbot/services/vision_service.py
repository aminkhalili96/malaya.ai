"""
Vision Service - v2 Phase 2: Image Understanding
=================================================
Provides image analysis using vision-language models.
Supports Qwen-VL or LLaVA for multimodal understanding.
"""

import logging
import base64
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class VisionService:
    """
    Vision service for image understanding using VLM models.
    Supports multiple backends: Ollama (LLaVA), Qwen-VL.
    """
    
    def __init__(self, provider: str = "ollama", model: str = "llava:7b"):
        """
        Initialize vision service.
        
        Args:
            provider: Model provider ("ollama" or "qwen")
            model: Model name (e.g., "llava:7b", "qwen3-vl:8b")
        """
        self.provider = provider
        self.model = model
        self._client = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """Lazy initialization of vision model client."""
        if self._initialized:
            return
            
        if self.provider == "ollama":
            try:
                import ollama
                self._client = ollama
                self._initialized = True
                logger.info(f"VisionService initialized with Ollama ({self.model})")
            except ImportError:
                logger.error("Ollama package not installed. pip install ollama")
                raise
        else:
            logger.error(f"Unsupported provider: {self.provider}")
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def analyze_image(
        self, 
        image_path: str, 
        prompt: str = "Describe this image in detail.",
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Analyze an image and return description.
        
        Args:
            image_path: Path to image file
            prompt: Question or instruction about the image
            language: Response language (english, malay, manglish)
            
        Returns:
            Dict with 'description', 'objects', 'text_detected', etc.
        """
        self._ensure_initialized()
        
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}
        
        # Add language instruction
        if language == "malay":
            prompt = f"Jawab dalam Bahasa Melayu. {prompt}"
        elif language == "manglish":
            prompt = f"Reply in Manglish (Malaysian English). {prompt}"
        
        try:
            if self.provider == "ollama":
                response = self._client.chat(
                    model=self.model,
                    messages=[{
                        "role": "user",
                        "content": prompt,
                        "images": [image_path]
                    }]
                )
                
                return {
                    "description": response["message"]["content"],
                    "model": self.model,
                    "provider": self.provider
                }
                
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {"error": str(e)}
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from image (OCR).
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict with 'text' field containing extracted text
        """
        prompt = """Extract ALL text visible in this image. 
        Return the text exactly as it appears, preserving formatting.
        If there's no text, say 'No text detected'."""
        
        result = self.analyze_image(image_path, prompt)
        
        if "error" not in result:
            return {"text": result.get("description", "")}
        return result
    
    def detect_objects(self, image_path: str) -> Dict[str, Any]:
        """
        Detect and list objects in image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict with 'objects' list
        """
        prompt = """List all objects you can see in this image.
        Format as a simple list, one object per line.
        Be specific (e.g., 'red car' not just 'car')."""
        
        result = self.analyze_image(image_path, prompt)
        
        if "error" not in result:
            description = result.get("description", "")
            # Parse list from response
            objects = [line.strip().strip("-").strip("•").strip() 
                      for line in description.split("\n") 
                      if line.strip() and not line.startswith("#")]
            return {"objects": objects}
        return result
    
    def answer_question(
        self, 
        image_path: str, 
        question: str,
        language: str = "english"
    ) -> str:
        """
        Answer a question about an image.
        
        Args:
            image_path: Path to image file
            question: Question about the image
            language: Response language
            
        Returns:
            Answer string
        """
        result = self.analyze_image(image_path, question, language)
        
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("description", "Unable to answer")
    
    def get_available_models(self) -> List[str]:
        """Return list of supported vision models."""
        return [
            "llava:7b",
            "llava:13b",
            "llava:34b",
            "qwen3-vl:8b",
            "bakllava:7b"
        ]


# Singleton instance
_vision_service: Optional[VisionService] = None


def get_vision_service(provider: str = "ollama", model: str = "llava:7b") -> VisionService:
    """Get or create singleton VisionService."""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService(provider=provider, model=model)
    return _vision_service
