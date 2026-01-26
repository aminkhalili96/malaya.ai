
import logging
import os
from .native_malaya import NativeMalaya

logger = logging.getLogger(__name__)

class MalayaService:
    """
    Wrapper for Native Malaya V2 NLP services.
    Provides Normalization, Toxicity, Sentiment, and Grammar capabilities.
    """
    
    def __init__(self, toxicity_threshold: float = 0.7, normalize_shortforms: bool = True):
        logger.info("Initializing MalayaService (Native V2)...")
        try:
            self.native = NativeMalaya()
            self._available = True
        except Exception as e:
            logger.error(f"Failed to initialize NativeMalaya: {e}")
            self.native = None
            self._available = False
        self.toxicity_threshold = float(toxicity_threshold)
        self.normalize_shortforms = bool(normalize_shortforms)

    def normalize_text(self, text: str) -> str:
        """
        Normalize informal Malay text (Shortforms/Slang).
        e.g. 'xleh' -> 'tidak boleh'
        """
        if not self._available:
            return text
        try:
            norm = self.native.normalize(text)
            # Enhance with True Casing
            norm = self.native.true_case(norm)
            return norm
        except Exception as e:
            logger.error(f"Normalization error: {e}")
            return text

    def check_toxicity(self, text: str):
        """
        Check if text contains toxic content.
        Returns (is_toxic, score, label).
        """
        if not self._available:
            return False, 0.0, "clean"
        try:
            return self.native.check_toxicity(text)
        except Exception as e:
            logger.error(f"Toxicity check error: {e}")
            return False, 0.0, "error"

    def analyze_sentiment(self, text: str) -> str:
        if not self._available:
            return "neutral"
        return self.native.analyze_sentiment(text)

    def polish_output(self, text: str) -> str:
        """
        Polish LLM output (TrueCasing + optional Paraphrasing).
        """
        if not self._available:
            return text
        try:
             # Just TrueCase for now to be safe
             return self.native.true_case(text)
        except: return text

    def generate_paraphrases(self, text: str, n=2):
        if not self._available:
            return [text]
        return self.native.paraphrase(text, num_return_sequences=n)

    def process_input(self, text: str):
        """
        Normalize user input and check toxicity.
        Returns (normalized_text, blocked, reason).
        """
        normalized = text
        if self.normalize_shortforms:
            normalized = self.normalize_text(text)
        is_toxic, score, label = self.check_toxicity(text)
        blocked = bool(is_toxic and score >= self.toxicity_threshold)
        reason = f"toxicity:{label}:{score:.2f}" if blocked else ""
        return normalized, blocked, reason


_SERVICE_INSTANCE = None


def get_malaya_service(config: dict = None):
    """Singleton accessor for MalayaService with optional config."""
    global _SERVICE_INSTANCE
    if _SERVICE_INSTANCE is None:
        config = config or {}
        settings = config.get("malaya_v2", {}) if isinstance(config, dict) else {}
        threshold = settings.get("toxicity_threshold", 0.7)
        normalize_shortforms = settings.get("normalize_shortforms", True)
        _SERVICE_INSTANCE = MalayaService(
            toxicity_threshold=threshold,
            normalize_shortforms=normalize_shortforms,
        )
    return _SERVICE_INSTANCE
