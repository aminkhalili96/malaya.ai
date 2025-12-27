"""
Sentiment & Emotion Service
Detects user sentiment and emotion for adaptive responses.
"""
from typing import Dict, Tuple, Optional
import re

class SentimentEmotionService:
    """
    Detects sentiment (positive/negative/neutral) and emotion 
    (happy/sad/angry/frustrated/excited) from user messages.
    Triggers tone adjustments in responses.
    """
    
    # Emotion keywords in English, Malay, Manglish
    EMOTION_KEYWORDS = {
        "angry": [
            "geram", "marah", "bengang", "annoyed", "pissed", "fed up",
            "benci", "hate", "stupid", "bodoh", "sial", "celaka", "damn"
        ],
        "frustrated": [
            "penat", "tired", "give up", "susah", "difficult", "tak jadi",
            "xjd", "xleh", "cannot", "stress", "tension", "frust", "haih"
        ],
        "sad": [
            "sedih", "sad", "kecewa", "disappointed", "lonely", "sunyi",
            "miss", "rindu", "cry", "nangis", "heartbroken", "down"
        ],
        "happy": [
            "happy", "gembira", "best", "awesome", "great", "syok", "shiok",
            "love", "suka", "excited", "yay", "woohoo", "nice", "good"
        ],
        "excited": [
            "excited", "teruja", "cant wait", "x sabar", "omg", "wow",
            "amazing", "incredible", "finally", "akhirnya", "yes"
        ],
        "anxious": [
            "worried", "risau", "nervous", "takut", "scared", "anxious",
            "panic", "stress", "gelisah", "bimbang", "cuak"
        ],
    }
    
    # Sentiment indicators
    POSITIVE_INDICATORS = [
        "thanks", "terima kasih", "tq", "good", "great", "nice", "best",
        "love", "suka", "appreciate", "helpful", "awesome", "bagus"
    ]
    
    NEGATIVE_INDICATORS = [
        "bad", "terrible", "awful", "horrible", "hate", "benci", "stupid",
        "useless", "worst", "poor", "fail", "wrong", "salah", "teruk"
    ]
    
    # Intensity amplifiers
    AMPLIFIERS = [
        "very", "really", "so", "super", "sangat", "gila", "betul",
        "extremely", "totally", "absolutely", "memang", "confirm"
    ]
    
    def detect_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Detect sentiment: positive, negative, or neutral.
        Returns (sentiment, confidence).
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.POSITIVE_INDICATORS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_INDICATORS if word in text_lower)
        
        # Check for amplifiers
        has_amplifier = any(amp in text_lower for amp in self.AMPLIFIERS)
        multiplier = 1.5 if has_amplifier else 1.0
        
        positive_score = positive_count * multiplier
        negative_score = negative_count * multiplier
        
        if positive_score > negative_score and positive_score > 0:
            confidence = min(0.5 + (positive_score * 0.1), 0.95)
            return ("positive", confidence)
        elif negative_score > positive_score and negative_score > 0:
            confidence = min(0.5 + (negative_score * 0.1), 0.95)
            return ("negative", confidence)
        else:
            return ("neutral", 0.6)
    
    def detect_emotion(self, text: str) -> Tuple[str, float]:
        """
        Detect primary emotion from text.
        Returns (emotion, confidence).
        """
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        if not emotion_scores:
            return ("neutral", 0.5)
        
        # Get emotion with highest score
        top_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = min(0.5 + (emotion_scores[top_emotion] * 0.15), 0.95)
        
        return (top_emotion, confidence)
    
    def get_response_adjustment(self, emotion: str, sentiment: str) -> Dict:
        """
        Get response adjustments based on detected emotion/sentiment.
        """
        adjustments = {
            "tone": "neutral",
            "empathy_level": "medium",
            "formality": "casual",
            "suggestions": []
        }
        
        if emotion == "angry" or emotion == "frustrated":
            adjustments["tone"] = "calm"
            adjustments["empathy_level"] = "high"
            adjustments["suggestions"].append("Acknowledge frustration before providing solution")
        
        elif emotion == "sad":
            adjustments["tone"] = "compassionate"
            adjustments["empathy_level"] = "high"
            adjustments["suggestions"].append("Show understanding and support")
        
        elif emotion == "anxious":
            adjustments["tone"] = "reassuring"
            adjustments["empathy_level"] = "high"
            adjustments["suggestions"].append("Provide clear, step-by-step guidance")
        
        elif emotion == "happy" or emotion == "excited":
            adjustments["tone"] = "enthusiastic"
            adjustments["empathy_level"] = "medium"
            adjustments["suggestions"].append("Match energy level")
        
        if sentiment == "negative":
            adjustments["formality"] = "professional"
            adjustments["suggestions"].append("Be extra careful with word choice")
        
        return adjustments
    
    def analyze(self, text: str) -> Dict:
        """
        Full analysis of text for sentiment and emotion.
        """
        sentiment, sentiment_conf = self.detect_sentiment(text)
        emotion, emotion_conf = self.detect_emotion(text)
        adjustments = self.get_response_adjustment(emotion, sentiment)
        
        return {
            "sentiment": sentiment,
            "sentiment_confidence": sentiment_conf,
            "emotion": emotion,
            "emotion_confidence": emotion_conf,
            "adjustments": adjustments
        }


# Global instance
sentiment_service = SentimentEmotionService()
