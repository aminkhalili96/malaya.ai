"""
Voice Service - v2 Phase 2: Speech-to-Text (ASR)
=================================================
Provides Malaysian speech recognition using malaya-speech.
Supports multiple dialects and accents.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Voice input service using malaya-speech for Malaysian ASR.
    Supports Malay, English, and dialectal speech recognition.
    """
    
    def __init__(self):
        self._asr_model = None
        self._vad_model = None
        self._initialized = False
        self._malaya_speech = None
        
    def _ensure_initialized(self):
        """Lazy initialization of malaya-speech models."""
        if self._initialized:
            return
            
        import os
        if os.environ.get("MALAYA_FORCE_MOCK") == "1":
            self._use_mock()
            self._initialized = True
            return

        try:
            import malaya_speech
            self._malaya_speech = malaya_speech
            
            # Load ASR model (Whisper-based for Malaysian)
            logger.info("Loading ASR model (this may take a moment)...")
            self._asr_model = malaya_speech.stt.deep_transducer(model='conformer-medium')
            
            # Load VAD for speech detection
            logger.info("Loading VAD model...")
            self._vad_model = malaya_speech.vad.deep_model(model='vggvox-v2')
            
            self._initialized = True
            logger.info("VoiceService initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import malaya_speech: {e}")
            logger.info("Install with: pip install malaya-speech")
            raise
        except Exception as e:
            logger.error(f"VoiceService initialization failed: {e}")
            raise
    
    def _use_mock(self):
        """Initialize mock objects for testing when malaya-speech is unavailable."""
        logger.warning("Initializing VoiceService in MOCK MODE.")
        
        class MockASR:
            def predict(self, audio): return ["This is a mock transcription because malaya-speech is missing."]
            
        class MockVAD:
            def predict(self, audio): return []
            
        self._asr_model = MockASR()
        self._vad_model = MockVAD()
        
    def transcribe_audio(self, audio_path: str) -> Tuple[str, float]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (wav, mp3, etc.)
            
        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        self._ensure_initialized()
        
        try:
            import librosa
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Run ASR
            result = self._asr_model.predict([y])
            
            if result and len(result) > 0:
                text = result[0]
                confidence = 0.85  # Default confidence (model doesn't always return it)
                return text, confidence
            
            return "", 0.0
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return f"Error: {e}", 0.0
    
    def transcribe_bytes(self, audio_bytes: bytes, format: str = "wav") -> Tuple[str, float]:
        """
        Transcribe audio from bytes.
        
        Args:
            audio_bytes: Raw audio bytes
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        try:
            return self.transcribe_audio(temp_path)
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def detect_speech_segments(self, audio_path: str) -> list:
        """
        Detect speech segments in audio using VAD.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of (start_time, end_time) tuples for speech segments
        """
        self._ensure_initialized()
        
        try:
            import librosa
            
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Run VAD
            result = self._vad_model.predict(y)
            
            # Parse segments
            segments = []
            if result:
                for segment in result:
                    if hasattr(segment, 'start') and hasattr(segment, 'end'):
                        segments.append((segment.start, segment.end))
            
            return segments
            
        except Exception as e:
            logger.error(f"VAD failed: {e}")
            return []
    
    def get_supported_languages(self) -> list:
        """Return list of supported languages."""
        return [
            "malay",
            "english", 
            "manglish",
            "kelantanese",
            "terengganu",
            "sabahan",
            "sarawakian"
        ]


class TextToSpeechService:
    """
    Text-to-Speech service for Malaysian voices.
    Uses Edge TTS for high-quality synthesis.
    """
    
    def __init__(self):
        self._default_voice = "ms-MY-OsmanNeural"  # Malaysian Malay voice
        self._voices = {
            "malay_male": "ms-MY-OsmanNeural",
            "malay_female": "ms-MY-YasminNeural",
            "english_male": "en-MY-OsmanNeural",
            "english_female": "en-MY-YasminNeural"
        }
    
    async def synthesize(self, text: str, voice: Optional[str] = None, output_path: Optional[str] = None) -> bytes:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            voice: Voice ID (default: ms-MY-OsmanNeural)
            output_path: Optional path to save audio file
            
        Returns:
            Audio bytes
        """
        try:
            import edge_tts
            
            voice_id = voice or self._default_voice
            communicate = edge_tts.Communicate(text, voice_id)
            
            if output_path:
                await communicate.save(output_path)
                with open(output_path, 'rb') as f:
                    return f.read()
            else:
                # Return bytes directly
                audio_bytes = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_bytes += chunk["data"]
                return audio_bytes
                
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise
    
    def get_available_voices(self) -> Dict[str, str]:
        """Return available voices."""
        return self._voices.copy()


# Singleton instances
_voice_service: Optional[VoiceService] = None
_tts_service: Optional[TextToSpeechService] = None


def get_voice_service() -> VoiceService:
    """Get or create singleton VoiceService."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service


def get_tts_service() -> TextToSpeechService:
    """Get or create singleton TextToSpeechService."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TextToSpeechService()
    return _tts_service
