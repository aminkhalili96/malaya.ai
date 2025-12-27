"""
voice.py - Malaysian TTS (Text-to-Speech) and STT (Speech-to-Text) Module

This module provides voice capabilities for Malaya LLM:
- TTS: Convert text responses to speech using Edge TTS (Malaysian voices)
- STT: Transcribe voice input to text using Whisper

Malaysian TTS Voices:
- ms-MY-YasminNeural (Female)
- ms-MY-OsmanNeural (Male)

Requirements:
- edge-tts: pip install edge-tts
- openai-whisper: pip install openai-whisper (optional, for local STT)
- openai: pip install openai (for OpenAI Whisper API)
"""

import asyncio
import base64
import io
import os
import tempfile
from typing import Optional, Tuple
from dataclasses import dataclass

# TTS - Edge TTS (Free, Microsoft)
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    edge_tts = None
    EDGE_TTS_AVAILABLE = False

# STT - OpenAI Whisper (API or Local)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

try:
    import whisper
    WHISPER_LOCAL_AVAILABLE = True
except ImportError:
    whisper = None
    WHISPER_LOCAL_AVAILABLE = False


@dataclass
class VoiceConfig:
    """Configuration for voice services."""
    # TTS Settings
    tts_voice_female: str = "ms-MY-YasminNeural"  # Malaysian Female
    tts_voice_male: str = "ms-MY-OsmanNeural"     # Malaysian Male
    tts_default_voice: str = "ms-MY-YasminNeural"
    tts_rate: str = "+0%"      # Speech rate adjustment
    tts_volume: str = "+0%"    # Volume adjustment
    
    # STT Settings
    stt_provider: str = "openai_api"  # "openai_api", "whisper_local"
    stt_model: str = "whisper-1"      # For OpenAI API
    whisper_local_model: str = "base" # For local Whisper: tiny, base, small, medium, large


class TextToSpeech:
    """
    Malaysian Text-to-Speech using Edge TTS.
    
    Features:
    - Malaysian female voice (Yasmin)
    - Malaysian male voice (Osman)
    - Rate and volume control
    - Async and sync interfaces
    """
    
    # Available Malaysian voices
    VOICES = {
        "female": "ms-MY-YasminNeural",
        "male": "ms-MY-OsmanNeural",
        "yasmin": "ms-MY-YasminNeural",
        "osman": "ms-MY-OsmanNeural",
    }
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self._available = EDGE_TTS_AVAILABLE
        
        if not self._available:
            print("Warning: edge-tts not installed. Run: pip install edge-tts")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    async def synthesize_async(
        self, 
        text: str, 
        voice: str = "female",
        output_file: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
        Convert text to speech asynchronously.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use ("female", "male", "yasmin", "osman")
            output_file: Optional file path to save audio
            rate: Speech rate (e.g., "+10%", "-20%")
            volume: Volume adjustment (e.g., "+10%", "-10%")
            
        Returns:
            Tuple of (audio_bytes, output_path)
        """
        if not self._available:
            raise RuntimeError("edge-tts not available")
        
        # Resolve voice name
        voice_name = self.VOICES.get(voice.lower(), self.config.tts_default_voice)
        rate = rate or self.config.tts_rate
        volume = volume or self.config.tts_volume
        
        # Create communicator
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice_name,
            rate=rate,
            volume=volume
        )
        
        # Determine output path
        temp_output = None
        if output_file:
            output_path = output_file
        else:
            # Use temp file (auto-cleaned)
            fd, output_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            temp_output = output_path
        
        try:
            # Generate and save audio
            await communicate.save(output_path)

            # Read audio bytes
            with open(output_path, "rb") as f:
                audio_bytes = f.read()
        finally:
            if temp_output and os.path.exists(temp_output):
                os.remove(temp_output)

        return audio_bytes, output_path
    
    def synthesize(
        self, 
        text: str, 
        voice: str = "female",
        output_file: Optional[str] = None,
        **kwargs
    ) -> Tuple[bytes, str]:
        """
        Convert text to speech (synchronous wrapper).
        
        Args:
            text: Text to convert to speech
            voice: Voice to use ("female", "male", "yasmin", "osman")
            output_file: Optional file path to save audio
            
        Returns:
            Tuple of (audio_bytes, output_path)
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError("synthesize() cannot run inside an event loop; use synthesize_async().")

        return asyncio.run(self.synthesize_async(text, voice, output_file, **kwargs))
    
    def synthesize_to_base64(
        self, 
        text: str, 
        voice: str = "female",
        **kwargs
    ) -> str:
        """
        Convert text to speech and return as base64.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use
            
        Returns:
            Base64 encoded audio string
        """
        audio_bytes, _ = self.synthesize(text, voice, **kwargs)
        return base64.b64encode(audio_bytes).decode("utf-8")
    
    async def list_voices_async(self) -> list:
        """List all available Edge TTS voices."""
        if not self._available:
            return []
        
        voices = await edge_tts.list_voices()
        return voices
    
    def list_malaysian_voices(self) -> list:
        """List available Malaysian voices."""
        return [
            {"name": "ms-MY-YasminNeural", "gender": "Female", "description": "Malaysian Female"},
            {"name": "ms-MY-OsmanNeural", "gender": "Male", "description": "Malaysian Male"},
        ]


class SpeechToText:
    """
    Malaysian Speech-to-Text using OpenAI Whisper.
    
    Features:
    - OpenAI Whisper API (cloud)
    - Local Whisper model (offline)
    - Malaysian language support
    """
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self._openai_client = None
        self._whisper_model = None
        
        # Initialize based on provider
        if self.config.stt_provider == "openai_api" and OPENAI_AVAILABLE:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self._openai_client = OpenAI()
        
        if self.config.stt_provider == "whisper_local" and WHISPER_LOCAL_AVAILABLE:
            self._whisper_model = whisper.load_model(self.config.whisper_local_model)
    
    @property
    def is_available(self) -> bool:
        if self.config.stt_provider == "openai_api":
            return self._openai_client is not None
        elif self.config.stt_provider == "whisper_local":
            return self._whisper_model is not None
        return False
    
    def transcribe(
        self, 
        audio_data: bytes,
        language: str = "ms",  # Malaysian/Malay
        prompt: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Audio bytes (mp3, wav, m4a, etc.)
            language: ISO language code ("ms" for Malay, "en" for English)
            prompt: Optional prompt to guide transcription
            
        Returns:
            Dict with "text" and metadata
        """
        if self.config.stt_provider == "openai_api":
            return self._transcribe_openai(audio_data, language, prompt)
        elif self.config.stt_provider == "whisper_local":
            return self._transcribe_local(audio_data, language, prompt)
        else:
            raise RuntimeError("No STT provider available")
    
    def _transcribe_openai(
        self, 
        audio_data: bytes,
        language: str,
        prompt: Optional[str]
    ) -> dict:
        """Transcribe using OpenAI Whisper API."""
        if not self._openai_client:
            raise RuntimeError("OpenAI client not available")
        
        # Create a file-like object from bytes
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.mp3"  # OpenAI needs a filename
        
        # Build request
        kwargs = {
            "model": self.config.stt_model,
            "file": audio_file,
        }
        
        # Add optional parameters
        if language:
            kwargs["language"] = language
        if prompt:
            kwargs["prompt"] = prompt
        
        # Transcribe
        response = self._openai_client.audio.transcriptions.create(**kwargs)
        
        return {
            "text": response.text,
            "language": language,
            "provider": "openai_api"
        }
    
    def _transcribe_local(
        self, 
        audio_data: bytes,
        language: str,
        prompt: Optional[str]
    ) -> dict:
        """Transcribe using local Whisper model."""
        if not self._whisper_model:
            raise RuntimeError("Local Whisper model not loaded")
        
        # Save audio to temp file (Whisper needs file path)
        fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(audio_data)
            
            # Transcribe
            result = self._whisper_model.transcribe(
                temp_path,
                language=language if language else None,
                initial_prompt=prompt
            )
            
            return {
                "text": result["text"],
                "language": result.get("language", language),
                "segments": result.get("segments", []),
                "provider": "whisper_local"
            }
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def transcribe_file(
        self, 
        file_path: str,
        language: str = "ms",
        prompt: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio from file path.
        
        Args:
            file_path: Path to audio file
            language: ISO language code
            prompt: Optional prompt to guide transcription
            
        Returns:
            Dict with "text" and metadata
        """
        with open(file_path, "rb") as f:
            audio_data = f.read()
        
        return self.transcribe(audio_data, language, prompt)


class VoiceAssistant:
    """
    High-level voice assistant combining TTS and STT.
    
    Provides a simple interface for voice-based interactions.
    """
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self.tts = TextToSpeech(config)
        self.stt = SpeechToText(config)
    
    @property
    def tts_available(self) -> bool:
        return self.tts.is_available
    
    @property
    def stt_available(self) -> bool:
        return self.stt.is_available
    
    def get_status(self) -> dict:
        """Get status of voice services."""
        return {
            "tts": {
                "available": self.tts_available,
                "voices": self.tts.list_malaysian_voices()
            },
            "stt": {
                "available": self.stt_available,
                "provider": self.config.stt_provider
            }
        }
    
    def voice_to_text(
        self, 
        audio_data: bytes,
        language: str = "ms"
    ) -> str:
        """
        Convert voice input to text.
        
        Args:
            audio_data: Audio bytes
            language: Language code
            
        Returns:
            Transcribed text
        """
        if not self.stt_available:
            raise RuntimeError("STT not available")
        
        result = self.stt.transcribe(audio_data, language)
        return result["text"]
    
    def text_to_voice(
        self, 
        text: str,
        voice: str = "female"
    ) -> bytes:
        """
        Convert text to voice.
        
        Args:
            text: Text to speak
            voice: Voice to use
            
        Returns:
            Audio bytes
        """
        if not self.tts_available:
            raise RuntimeError("TTS not available")
        
        audio_bytes, _ = self.tts.synthesize(text, voice)
        return audio_bytes
    
    async def voice_to_text_async(
        self, 
        audio_data: bytes,
        language: str = "ms"
    ) -> str:
        """Async version of voice_to_text."""
        # STT is synchronous, wrap in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.voice_to_text(audio_data, language)
        )
    
    async def text_to_voice_async(
        self, 
        text: str,
        voice: str = "female"
    ) -> bytes:
        """Async version of text_to_voice."""
        audio_bytes, _ = await self.tts.synthesize_async(text, voice)
        return audio_bytes


# ============================================================================
# Convenience functions
# ============================================================================

def synthesize_malaysian(text: str, voice: str = "female") -> bytes:
    """Quick function to synthesize Malaysian speech."""
    tts = TextToSpeech()
    audio_bytes, _ = tts.synthesize(text, voice)
    return audio_bytes


def transcribe_to_malay(audio_data: bytes) -> str:
    """Quick function to transcribe audio to Malay text."""
    stt = SpeechToText()
    result = stt.transcribe(audio_data, language="ms")
    return result["text"]


# ============================================================================
# Demo
# ============================================================================

if __name__ == "__main__":
    print("Malaysian Voice Module Demo")
    print("="*50)
    
    # Check availability
    assistant = VoiceAssistant()
    status = assistant.get_status()
    
    print(f"\nTTS Available: {status['tts']['available']}")
    print(f"STT Available: {status['stt']['available']}")
    
    if status['tts']['available']:
        print("\nAvailable TTS Voices:")
        for voice in status['tts']['voices']:
            print(f"  - {voice['name']} ({voice['gender']})")
        
        # Demo TTS
        print("\nGenerating sample speech...")
        try:
            audio, path = TextToSpeech().synthesize(
                "Selamat pagi! Saya Malaya AI, pembantu AI untuk rakyat Malaysia.",
                voice="female"
            )
            print(f"Audio saved to: {path}")
            print(f"Audio size: {len(audio)} bytes")
        except Exception as e:
            print(f"TTS Error: {e}")
    
    print("\n" + "="*50)
