from typing import Dict, Any
from ..summarization.preprocessing import (
    TextNormalizer,
    DialectDetector,
    ParticleAnalyzer,
    MalaysianSentimentAnalyzer,
)

class LanguageService:
    """
    Service for handling Malaysian language processing.
    Aggregates Normalizer, Dialect Detector, Particle Analyzer, and Sentiment Analyzer.
    """
    
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.dialect_detector = DialectDetector()
        self.particle_analyzer = ParticleAnalyzer()
        self.sentiment_analyzer = MalaysianSentimentAnalyzer()

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive language analysis on the input text.
        """
        # 1. Detect Dialect
        dialect, dialect_confidence, dialect_words = self.dialect_detector.detect(text)
        
        # 2. Analyze Particles (Emotion/Nuance)
        particle_analysis = self.particle_analyzer.analyze(text)
        
        # 3. Analyze Sentiment
        sentiment_analysis = self.sentiment_analyzer.analyze(text)
        
        # 4. Normalize (for retrieval)
        normalized_text = self.normalizer.normalize_for_retrieval(text)
        
        return {
            "original_text": text,
            "normalized_text": normalized_text,
            "detected_dialect": dialect,
            "dialect_confidence": dialect_confidence,
            "dialect_words": dialect_words,
            "particle_analysis": particle_analysis,
            "sentiment_analysis": sentiment_analysis
        }
