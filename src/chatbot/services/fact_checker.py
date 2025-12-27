"""
Hallucination Detection & Fact Checking Service
Detects potential hallucinations and verifies claims against sources.
"""
from typing import Dict, List, Optional, Tuple
import re

class HallucinationDetector:
    """
    Detects potential hallucinations in LLM responses by:
    - Checking for hedging language
    - Detecting conflicting statements
    - Verifying against provided sources
    - Flagging unsupported claims
    """
    
    # Hedging phrases that indicate uncertainty
    HEDGING_PHRASES = [
        "i think", "i believe", "probably", "might be", "could be",
        "possibly", "perhaps", "may be", "not sure", "i'm not certain",
        "as far as i know", "to my knowledge", "mungkin", "agaknya"
    ]
    
    # Confident but potentially problematic phrases
    OVERCONFIDENT_PHRASES = [
        "definitely", "certainly", "always", "never", "everyone knows",
        "it is well known", "100%", "absolutely", "without a doubt"
    ]
    
    # Patterns that suggest fabrication
    FABRICATION_PATTERNS = [
        r"founded in \d{4}",  # Specific founding dates
        r"according to a \d{4} study",  # Fake studies
        r"\d+% of people",  # Made-up statistics
        r"research shows that .{50,}",  # Long unsourced claims
    ]
    
    def detect_hedging(self, text: str) -> Tuple[bool, List[str]]:
        """Detect hedging language."""
        text_lower = text.lower()
        found = [phrase for phrase in self.HEDGING_PHRASES if phrase in text_lower]
        return (len(found) > 0, found)
    
    def detect_overconfidence(self, text: str) -> Tuple[bool, List[str]]:
        """Detect overconfident claims."""
        text_lower = text.lower()
        found = [phrase for phrase in self.OVERCONFIDENT_PHRASES if phrase in text_lower]
        return (len(found) > 0, found)
    
    def detect_fabrication_patterns(self, text: str) -> Tuple[bool, List[str]]:
        """Detect patterns that suggest fabricated information."""
        found = []
        for pattern in self.FABRICATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found.extend(matches)
        return (len(found) > 0, found)
    
    def check_source_support(
        self, 
        claim: str, 
        sources: List[str]
    ) -> Tuple[bool, float]:
        """
        Check if a claim is supported by provided sources.
        Returns (is_supported, confidence).
        """
        if not sources:
            return (False, 0.0)
        
        claim_words = set(claim.lower().split())
        
        best_overlap = 0
        for source in sources:
            source_words = set(source.lower().split())
            overlap = len(claim_words.intersection(source_words))
            overlap_ratio = overlap / len(claim_words) if claim_words else 0
            best_overlap = max(best_overlap, overlap_ratio)
        
        is_supported = best_overlap > 0.3
        return (is_supported, best_overlap)
    
    def analyze_response(
        self, 
        response: str, 
        sources: List[str] = None
    ) -> Dict:
        """
        Full hallucination analysis of a response.
        """
        has_hedging, hedging_phrases = self.detect_hedging(response)
        has_overconfidence, overconfident_phrases = self.detect_overconfidence(response)
        has_fabrication, fabrication_patterns = self.detect_fabrication_patterns(response)
        
        # Calculate hallucination risk score
        risk_score = 0.0
        
        if has_overconfidence and not sources:
            risk_score += 0.3
        
        if has_fabrication:
            risk_score += 0.4
        
        if has_hedging:
            # Hedging is actually good - indicates honest uncertainty
            risk_score -= 0.1
        
        # Clamp to 0-1
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Check source support for key sentences
        unsupported_claims = []
        if sources:
            sentences = re.split(r'[.!?]', response)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 30:  # Only check substantial sentences
                    is_supported, confidence = self.check_source_support(sentence, sources)
                    if not is_supported and confidence < 0.2:
                        unsupported_claims.append(sentence[:100])
        
        return {
            "risk_score": round(risk_score, 2),
            "risk_level": "high" if risk_score > 0.5 else "medium" if risk_score > 0.3 else "low",
            "has_hedging": has_hedging,
            "hedging_phrases": hedging_phrases,
            "has_overconfidence": has_overconfidence,
            "overconfident_phrases": overconfident_phrases,
            "has_fabrication_patterns": has_fabrication,
            "fabrication_matches": fabrication_patterns[:3],
            "unsupported_claims": unsupported_claims[:3],
        }


class FactChecker:
    """
    Verifies factual claims using external knowledge bases.
    """
    
    # Known facts for quick verification (expand as needed)
    KNOWN_FACTS = {
        "malaysia_independence": "1957",
        "malaysia_capital": "Kuala Lumpur",
        "malaysia_king": "Yang di-Pertuan Agong",
        "malaysia_states": "13",
        "klcc_height": "452 meters",
    }
    
    def __init__(self, llm=None):
        self.llm = llm
        self.hallucination_detector = HallucinationDetector()
    
    async def verify_claim(
        self, 
        claim: str, 
        sources: List[str] = None
    ) -> Dict:
        """
        Verify a factual claim.
        """
        # First, check hallucination patterns
        analysis = self.hallucination_detector.analyze_response(claim, sources)
        
        # Check against known facts
        known_verification = None
        for fact_key, fact_value in self.KNOWN_FACTS.items():
            if fact_key.replace("_", " ") in claim.lower():
                if fact_value.lower() in claim.lower():
                    known_verification = {"verified": True, "source": "known_facts"}
                else:
                    known_verification = {"verified": False, "correct_value": fact_value}
                break
        
        return {
            "claim": claim[:200],
            "hallucination_analysis": analysis,
            "known_fact_check": known_verification,
            "recommendation": "verify" if analysis["risk_level"] != "low" else "likely_accurate"
        }


# Global instances
hallucination_detector = HallucinationDetector()
fact_checker = FactChecker()
