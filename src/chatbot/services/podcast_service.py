"""
Podcast Service for summarizing articles and generating audio.
Uses Edge TTS for Malaysian voices.
"""
import os
import asyncio
import tempfile
import edge_tts
from typing import Optional
import httpx
from bs4 import BeautifulSoup

class PodcastService:
    # Malaysian voices available in Edge TTS
    VOICES = {
        "malay_female": "ms-MY-YasminNeural",
        "malay_male": "ms-MY-OsmanNeural",
        "english_female": "en-MY-YasminNeural",
        "english_male": "en-MY-OsmanNeural",
    }
    
    def __init__(self, llm=None):
        self.llm = llm  # LangChain LLM for summarization
        
    async def fetch_article(self, url: str) -> dict:
        """
        Fetches and extracts main content from a URL.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        # Try to find article content
        article = soup.find("article") or soup.find("main") or soup.find("body")
        
        # Extract title
        title = soup.find("title")
        title_text = title.get_text().strip() if title else "Untitled"
        
        # Extract paragraphs
        paragraphs = article.find_all("p") if article else []
        content = "\n\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
        
        return {
            "title": title_text,
            "content": content[:10000],  # Limit to ~10k chars
            "url": url
        }
    
    async def summarize(self, content: str, style: str = "casual") -> str:
        """
        Summarizes article content in a podcast-friendly style.
        """
        if not self.llm:
            # Fallback: return first 500 chars
            return content[:500] + "..."
            
        prompt = f"""Summarize this article in a conversational, podcast-friendly style.
Make it engaging and easy to listen to. Use Malaysian English if appropriate.
Keep it under 300 words.

Article:
{content}

Summary:"""
        
        response = await self.llm.ainvoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def generate_audio(
        self, 
        text: str, 
        voice: str = "malay_female",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generates audio from text using Edge TTS.
        
        Returns the path to the generated audio file.
        """
        voice_id = self.VOICES.get(voice, self.VOICES["malay_female"])
        
        if output_path is None:
            # Create temp file
            fd, output_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
        
        communicate = edge_tts.Communicate(text, voice_id)
        await communicate.save(output_path)
        
        return output_path
    
    async def create_podcast(
        self, 
        url: str, 
        voice: str = "malay_female",
        summarize: bool = True
    ) -> dict:
        """
        Full pipeline: Fetch article -> Summarize -> Generate audio
        
        Returns dict with title, summary, and audio_path.
        """
        # Step 1: Fetch
        article = await self.fetch_article(url)
        
        # Step 2: Summarize (optional)
        if summarize:
            summary = await self.summarize(article["content"])
        else:
            summary = article["content"][:1000]
        
        # Step 3: Generate audio
        audio_path = await self.generate_audio(summary, voice)
        
        return {
            "title": article["title"],
            "summary": summary,
            "audio_path": audio_path,
            "url": url
        }
