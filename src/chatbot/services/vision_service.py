"""
Vision Service for Snap & Translate feature.
Uses GPT-4o Vision to OCR and translate images.
"""
import base64
import os
from openai import AsyncOpenAI

class VisionService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
    
    async def translate_image(
        self, 
        image_base64: str, 
        target_language: str = "English",
        include_context: bool = True
    ) -> dict:
        """
        Translates text in an image to the target language.
        
        Args:
            image_base64: Base64 encoded image string
            target_language: Language to translate to (default: English)
            include_context: Whether to include cultural context
            
        Returns:
            dict with 'original_text', 'translated_text', 'context'
        """
        system_prompt = f"""You are a translation assistant for Malaysian signboards, menus, and documents.
Your task is to:
1. Read ALL text visible in the image (Chinese, Jawi, Malay, Tamil, etc.)
2. Translate it to {target_language}
3. Provide cultural context if relevant

Respond in this JSON format:
{{
    "original_text": "The exact text you see in the image",
    "language_detected": "Chinese/Jawi/Tamil/Malay/etc",
    "translated_text": "Translation in {target_language}",
    "context": "Brief cultural explanation (if applicable, otherwise null)"
}}
"""
        
        # Handle data URL prefix if present
        if image_base64.startswith("data:"):
            # Extract base64 part after the comma
            image_base64 = image_base64.split(",")[1]
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Translate the text in this image:"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result

    async def analyze_menu(self, image_base64: str) -> dict:
        """
        Analyzes a menu image and extracts items with prices.
        """
        system_prompt = """You are a menu reader for Malaysian restaurants.
Extract all menu items with their prices. Identify any dietary info (halal, vegetarian, spicy level).

Respond in JSON format:
{
    "restaurant_type": "Chinese/Malay/Indian/Western/etc",
    "items": [
        {"name": "Item name", "price": "RM X.XX", "description": "Brief description", "dietary": ["halal", "spicy"]}
    ],
    "recommendations": "Your top 3 picks and why"
}
"""
        if image_base64.startswith("data:"):
            image_base64 = image_base64.split(",")[1]
            
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this menu:"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
