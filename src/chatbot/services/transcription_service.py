"""
Transcription Service
Audio transcription using OpenAI Whisper API.
"""
import os
import tempfile
from typing import Optional
from openai import AsyncOpenAI

class TranscriptionService:
    """
    Audio transcription service using Whisper API.
    Supports multiple audio formats and languages.
    """
    
    SUPPORTED_FORMATS = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "whisper-1"
    
    async def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> dict:
        """
        Transcribe an audio file.
        
        Args:
            file_path: Path to audio file
            language: Optional ISO language code (e.g., "ms" for Malay)
            prompt: Optional prompt to guide transcription
            
        Returns:
            dict with text, language, duration
        """
        with open(file_path, "rb") as audio_file:
            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                prompt=prompt or "Malaysian conversation with English, Malay, and Manglish",
                response_format="verbose_json"
            )
        
        return {
            "text": response.text,
            "language": response.language,
            "duration": response.duration,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text
                }
                for seg in (response.segments or [])
            ]
        }
    
    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.mp3",
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio from bytes.
        """
        # Save to temp file
        suffix = f".{filename.split('.')[-1]}"
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(audio_bytes)
            
            return await self.transcribe_file(temp_path, language)
        finally:
            os.unlink(temp_path)
    
    async def summarize_meeting(
        self,
        transcription: str,
        llm=None
    ) -> dict:
        """
        Summarize a meeting transcription.
        
        Returns:
            dict with summary, action_items, key_points
        """
        if llm is None:
            # Use OpenAI directly
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a meeting summarizer. Given a meeting transcription, provide:
1. A brief summary (2-3 sentences)
2. Key discussion points (bullet list)
3. Action items with owners if mentioned
4. Decisions made

Format in markdown."""
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this meeting:\n\n{transcription}"
                    }
                ],
                max_tokens=1000
            )
            summary_text = response.choices[0].message.content
        else:
            prompt = f"""Summarize this meeting transcription:

{transcription}

Provide:
1. Brief summary (2-3 sentences)
2. Key discussion points
3. Action items with owners
4. Decisions made"""
            
            response = await llm.ainvoke(prompt)
            summary_text = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "summary": summary_text,
            "word_count": len(transcription.split()),
            "estimated_duration_minutes": len(transcription.split()) / 150  # ~150 wpm
        }


# Global instance
transcription_service = TranscriptionService()
