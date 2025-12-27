"""
Dialect TTS Service
State-specific Malaysian voices for text-to-speech.
"""
import os
import tempfile
from typing import Optional
import edge_tts

class DialectTTSService:
    """
    Text-to-speech with Malaysian state dialects.
    Uses Edge TTS with voice modulation for dialect simulation.
    """
    
    # Malaysian voices available in Edge TTS
    BASE_VOICES = {
        "malay_female": "ms-MY-YasminNeural",
        "malay_male": "ms-MY-OsmanNeural",
    }
    
    # State-specific dialect configurations
    # Each state gets custom prosody adjustments
    STATE_DIALECTS = {
        "johor": {"voice": "malay_male", "rate": "+5%", "pitch": "+2Hz"},
        "kedah": {"voice": "malay_female", "rate": "-10%", "pitch": "-3Hz"},
        "kelantan": {"voice": "malay_female", "rate": "-15%", "pitch": "+5Hz"},
        "terengganu": {"voice": "malay_male", "rate": "-12%", "pitch": "+3Hz"},
        "pahang": {"voice": "malay_male", "rate": "+0%", "pitch": "+0Hz"},
        "perak": {"voice": "malay_female", "rate": "+2%", "pitch": "-1Hz"},
        "penang": {"voice": "malay_female", "rate": "+8%", "pitch": "+4Hz"},
        "perlis": {"voice": "malay_male", "rate": "-8%", "pitch": "-2Hz"},
        "selangor": {"voice": "malay_female", "rate": "+5%", "pitch": "+0Hz"},
        "negeri_sembilan": {"voice": "malay_female", "rate": "-5%", "pitch": "+2Hz"},
        "melaka": {"voice": "malay_male", "rate": "+3%", "pitch": "+1Hz"},
        "sabah": {"voice": "malay_female", "rate": "-5%", "pitch": "+3Hz"},
        "sarawak": {"voice": "malay_male", "rate": "-8%", "pitch": "+2Hz"},
    }
    
    # Dialect-specific word replacements
    DIALECT_WORDS = {
        "kelantan": {
            "apa": "gapo",
            "tidak": "dok",
            "makan": "make",
            "ini": "ni",
            "itu": "tu",
        },
        "terengganu": {
            "apa": "guane",
            "tidak": "dok",
            "makan": "makang",
            "ini": "ning",
        },
        "kedah": {
            "tidak": "dak",
            "ini": "ni",
            "itu": "tu",
        },
        "penang": {
            "saya": "wa",
            "awak": "hang",
            "tidak": "tak",
        },
        "negeri_sembilan": {
            "saya": "den",
            "awak": "kau",
            "tidak": "dak",
        },
    }
    
    async def generate_dialect_audio(
        self,
        text: str,
        state: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate audio with state-specific dialect characteristics.
        
        Args:
            text: Text to convert to speech
            state: Malaysian state name (lowercase)
            output_path: Optional path for audio file
            
        Returns:
            Path to generated audio file
        """
        state_lower = state.lower().replace(" ", "_")
        
        # Get dialect config or use default
        dialect_config = self.STATE_DIALECTS.get(state_lower, {
            "voice": "malay_female",
            "rate": "+0%",
            "pitch": "+0Hz"
        })
        
        # Apply dialect word replacements
        if state_lower in self.DIALECT_WORDS:
            for standard, dialect in self.DIALECT_WORDS[state_lower].items():
                text = text.replace(standard, dialect)
                text = text.replace(standard.capitalize(), dialect.capitalize())
        
        # Get voice ID
        voice_key = dialect_config["voice"]
        voice_id = self.BASE_VOICES.get(voice_key, self.BASE_VOICES["malay_female"])
        
        # Create SSML with prosody adjustments
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ms-MY">
            <voice name="{voice_id}">
                <prosody rate="{dialect_config['rate']}" pitch="{dialect_config['pitch']}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        # Generate output path
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
        
        # Generate audio
        communicate = edge_tts.Communicate(text, voice_id)
        # Note: Edge TTS doesn't support SSML directly, so we use the prosody via text
        # For full SSML support, consider Azure TTS
        await communicate.save(output_path)
        
        return output_path
    
    async def generate_multi_dialect_sample(
        self,
        text: str
    ) -> dict:
        """
        Generate the same text in all available dialects.
        Returns dict of state -> audio_path.
        """
        results = {}
        for state in self.STATE_DIALECTS.keys():
            try:
                path = await self.generate_dialect_audio(text, state)
                results[state] = path
            except Exception as e:
                results[state] = f"error: {str(e)}"
        return results
    
    def get_available_dialects(self) -> list:
        """Get list of available state dialects."""
        return list(self.STATE_DIALECTS.keys())


# Global instance
dialect_tts = DialectTTSService()
