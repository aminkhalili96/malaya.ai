"""
Meme Generator Service
Generates Malaysian memes using AI.
"""
import os
from typing import Dict, Optional
from openai import AsyncOpenAI

class MemeGeneratorService:
    """
    Generates memes with Malaysian context.
    Uses DALL-E for image generation.
    """
    
    MEME_TEMPLATES = {
        "reaction": "A funny reaction face with Malaysian elements",
        "comparison": "Side by side comparison meme",
        "expanding_brain": "Expanding brain meme template",
        "drake": "Drake approval/disapproval meme format",
        "distracted_bf": "Distracted boyfriend meme format",
    }
    
    MALAYSIAN_ELEMENTS = [
        "Malaysian food like nasi lemak, teh tarik",
        "Malaysian landmarks like KLCC, Petronas Towers",
        "Malaysian culture elements",
        "Tropical setting with palm trees",
    ]
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def generate_meme(
        self,
        description: str,
        style: str = "cartoon",
        add_malaysian_context: bool = True
    ) -> Dict:
        """
        Generate a meme from description.
        
        Args:
            description: Meme scenario or joke
            style: Art style (cartoon, realistic, anime)
            add_malaysian_context: Add Malaysian elements
        """
        # Build image prompt
        prompt = f"Meme-style {style} illustration: {description}"
        
        if add_malaysian_context:
            prompt += ". Include Malaysian cultural elements."
        
        prompt += " No text in the image, clean meme template format."
        
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt
            
            return {
                "success": True,
                "image_url": image_url,
                "prompt_used": revised_prompt,
                "description": description,
                "style": style
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "description": description
            }
    
    async def generate_meme_text(
        self,
        topic: str,
        llm=None
    ) -> Dict:
        """
        Generate meme text/captions from a topic.
        """
        prompt = f"""Create a funny meme about: {topic}

Requirements:
- Make it relatable to Malaysians
- Use Manglish if appropriate
- Include a setup and punchline
- Keep it short and punchy

Return in format:
TOP TEXT: [text for top of meme]
BOTTOM TEXT: [text for bottom of meme]
EXPLANATION: [brief context if needed]"""

        if llm:
            response = await llm.ainvoke(prompt)
            text = response.content if hasattr(response, 'content') else str(response)
        else:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            text = response.choices[0].message.content
        
        # Parse response
        lines = text.strip().split("\n")
        top_text = ""
        bottom_text = ""
        explanation = ""
        
        for line in lines:
            if line.startswith("TOP TEXT:"):
                top_text = line.replace("TOP TEXT:", "").strip()
            elif line.startswith("BOTTOM TEXT:"):
                bottom_text = line.replace("BOTTOM TEXT:", "").strip()
            elif line.startswith("EXPLANATION:"):
                explanation = line.replace("EXPLANATION:", "").strip()
        
        return {
            "topic": topic,
            "top_text": top_text,
            "bottom_text": bottom_text,
            "explanation": explanation
        }
    
    async def full_meme_generation(
        self,
        topic: str,
        style: str = "cartoon",
        llm=None
    ) -> Dict:
        """
        Full pipeline: Generate text + image for a meme.
        """
        # Generate text
        text_result = await self.generate_meme_text(topic, llm)
        
        # Generate image based on text
        image_description = f"{text_result['top_text']} - {text_result['bottom_text']}"
        image_result = await self.generate_meme(image_description, style)
        
        return {
            "topic": topic,
            "text": text_result,
            "image": image_result
        }


# Global instance
meme_generator = MemeGeneratorService()
