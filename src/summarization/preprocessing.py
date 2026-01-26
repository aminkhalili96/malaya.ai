"""
preprocessing.py - Malaysian Text Normalization with Dialect Support

This module handles text normalization for Malaysian Manglish, slang, and regional dialects.
It expands shortforms and colloquialisms to standard Malay/English for better LLM understanding.

Enhancements (v2.0):
    - Support for all Malaysian state dialects (Kelantan, Terengganu, Sabah, Sarawak, etc.)
    - Gen-Z/TikTok slang normalization
    - Intensity marker handling (bestttt → best sangat)
    - Colloquialism expansion (tapau → bungkus makanan)
    - Sense-aware slang expansion for ambiguous terms
"""

import re
import os
import json
from typing import Dict, Tuple, Optional

try:
    import malaya
except Exception as exc:
    malaya = None
    MALAYA_IMPORT_ERROR = exc


def _load_raw_dictionary() -> dict:
    """Load the raw dictionary for dialect detection purposes."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        shortforms_path = os.path.join(current_dir, "..", "data", "shortforms.json")
        
        if os.path.exists(shortforms_path):
            with open(shortforms_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _merge_terms(target: Dict[str, str], source: Dict[str, str], skip_keys: set, override: bool = False) -> None:
    for term, expansion in source.items():
        if term.startswith("_"):
            continue
        if term in skip_keys:
            continue
        if not override and term in target:
            continue
        target[term] = expansion


def _build_shortforms(data: dict) -> Dict[str, str]:
    """
    Build a flattened dictionary of all shortforms including dialects.
    Skips ambiguous terms so they can be handled with sense-aware logic.
    """
    ambiguous_terms = set(data.get("ambiguous_terms", {}).keys())
    all_shortforms: Dict[str, str] = {}

    _merge_terms(all_shortforms, data.get("shortforms", {}), ambiguous_terms)

    # Add dialect shortforms (flattened)
    dialects = data.get("dialects", {})
    for dialect_name, dialect_terms in dialects.items():
        if not isinstance(dialect_terms, dict):
            continue
        status = str(dialect_terms.get("_status", "active")).lower()
        if status != "active":
            continue
        _merge_terms(all_shortforms, dialect_terms, ambiguous_terms)

    # Add Gen-Z/TikTok slang
    _merge_terms(all_shortforms, data.get("genz_tiktok", {}), ambiguous_terms)

    # Add intensity markers
    _merge_terms(all_shortforms, data.get("intensity_markers", {}), ambiguous_terms)

    # Add colloquialisms
    _merge_terms(all_shortforms, data.get("colloquialisms", {}), ambiguous_terms)

    if all_shortforms:
        return all_shortforms

    # Minimal fallback if JSON fails to load
    return {
        "xleh": "tak boleh",
        "xbleh": "tak boleh",
        "xde": "tiada",
        "ko": "kau",
        "mcm": "macam",
        "sbb": "sebab",
        "giler": "gila",
        "camne": "macam mana",
    }


def _build_ambiguous_terms(data: dict) -> Dict[str, dict]:
    ambiguous = data.get("ambiguous_terms", {})
    normalized = {}

    for term, payload in ambiguous.items():
        if term.startswith("_"):
            continue
        if not isinstance(payload, dict):
            continue
        default = payload.get("default")
        strategy = payload.get("strategy", "append")
        senses = payload.get("senses", [])
        cleaned_senses = []
        for sense in senses:
            if not isinstance(sense, dict):
                continue
            replacement = sense.get("replacement")
            keywords = sense.get("keywords", [])
            cleaned_senses.append({
                "replacement": replacement,
                "keywords": [str(k).lower() for k in keywords],
                "strategy": sense.get("strategy", strategy),
            })
        normalized[term.lower()] = {
            "default": default,
            "strategy": strategy,
            "senses": cleaned_senses,
        }

    return normalized


def _build_dialect_status(data: dict) -> Dict[str, str]:
    statuses: Dict[str, str] = {}
    for dialect, terms in data.get("dialects", {}).items():
        if isinstance(terms, dict):
            status = terms.get("_status", "active")
        else:
            status = "active"
        statuses[dialect] = str(status).lower()
    return statuses


def _build_dialect_min_matches(data: dict) -> Dict[str, int]:
    min_matches: Dict[str, int] = {}
    for dialect, terms in data.get("dialects", {}).items():
        if isinstance(terms, dict):
            value = terms.get("_min_matches", 1)
        else:
            value = 1
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 1
        if value < 1:
            value = 1
        min_matches[dialect] = value
    return min_matches


# Load shortforms once at module level
RAW_DICTIONARY = _load_raw_dictionary()
DIALECT_STATUS = _build_dialect_status(RAW_DICTIONARY)
DIALECT_MIN_MATCHES = _build_dialect_min_matches(RAW_DICTIONARY)
SHORTFORMS = _build_shortforms(RAW_DICTIONARY)
AMBIGUOUS_TERMS = _build_ambiguous_terms(RAW_DICTIONARY)


class TextNormalizer:
    """
    Normalizes Malaysian Manglish, slang, and regional dialects.
    
    Features:
    - 400+ shortform expansions
    - All Malaysian state dialects
    - Gen-Z/TikTok slang
    - Intensity marker handling
    - Colloquialism expansion
    """
    
    def __init__(self):
        self._malaya_available = False
        self._init_error = None
        self.normalizer = None
        self._shortforms = SHORTFORMS
        self._ambiguous_terms = AMBIGUOUS_TERMS

        if malaya:
            try:
                if hasattr(malaya, "normalizer") and hasattr(malaya.normalizer, "rules"):
                    self.normalizer = malaya.normalizer.rules.load()
                else:
                    self.normalizer = malaya.normalize.normalizer()
                self._malaya_available = True
            except Exception as exc:
                self._init_error = exc

    def normalize(self, text: str) -> str:
        """
        Normalizes 'Bahasa Rojak', Manglish, and regional dialects.
        Backwards-compatible alias for normalize_for_retrieval().
        """
        return self.normalize_for_retrieval(text)

    def normalize_for_retrieval(self, text: str) -> str:
        """
        Normalize text for retrieval while preserving original phrasing for generation.
        Applies Malaya normalization (if available) followed by local slang expansions.
        """
        text = text.strip()
        normalized = text

        # Apply local slang/dialect expansion before Malaya to avoid English drift.
        normalized, _ = self._apply_ambiguous_terms(normalized)
        normalized = self._apply_shortforms(normalized)
        baseline = normalized

        if self._malaya_available and self.normalizer:
            try:
                candidate = self.normalizer.normalize(normalized)
                if isinstance(candidate, dict) and "normalize" in candidate:
                    candidate = candidate["normalize"]
                if isinstance(candidate, str):
                    english_markers = {
                        "the", "too", "bored", "crazy", "what", "why", "how", "when",
                        "where", "who", "with", "without", "slow", "happy", "sad",
                    }
                    candidate_lower = candidate.lower()
                    baseline_lower = normalized.lower()
                    english_hits = sum(1 for word in english_markers if word in candidate_lower)
                    baseline_hits = sum(1 for word in english_markers if word in baseline_lower)
                    # If Malaya normalization introduces English drift, keep local expansion.
                    if english_hits > baseline_hits and english_hits >= 1:
                        candidate = normalized
                    normalized = candidate
                else:
                    normalized = baseline
            except Exception as exc:
                self._init_error = self._init_error or exc
                normalized = baseline

        normalized = self._apply_shortforms(normalized)

        # Clean up extra whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _apply_shortforms(self, text: str) -> str:
        # Sort by length (longest first) to handle multi-word expressions first
        sorted_shortforms = sorted(
            self._shortforms.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )

        normalized = text
        for slang, clean in sorted_shortforms:
            # Use word boundary matching to avoid partial replacements
            normalized = re.sub(
                rf"\b{re.escape(slang)}\b",
                clean,
                normalized,
                flags=re.IGNORECASE,
            )
        return normalized

    def _apply_ambiguous_terms(self, text: str) -> Tuple[str, Dict[str, str]]:
        if not self._ambiguous_terms:
            return text, {}

        tokens = list(re.finditer(r"\b\w+\b", text))
        if not tokens:
            return text, {}

        token_texts = [match.group(0) for match in tokens]
        token_lowers = [token.lower() for token in token_texts]

        pieces = []
        last_index = 0
        applied = {}

        for idx, match in enumerate(tokens):
            token_lower = token_lowers[idx]
            term_info = self._ambiguous_terms.get(token_lower)
            if not term_info:
                continue

            replacement = self._choose_ambiguous_replacement(term_info, token_lowers, idx)
            if not replacement:
                continue

            strategy = term_info.get("strategy", "append")
            if strategy == "append":
                replacement_text = f"{token_texts[idx]} {replacement}"
            else:
                replacement_text = self._preserve_case(token_texts[idx], replacement)

            pieces.append(text[last_index:match.start()])
            pieces.append(replacement_text)
            last_index = match.end()
            applied[token_texts[idx]] = replacement

        if not pieces:
            return text, applied

        pieces.append(text[last_index:])
        return "".join(pieces), applied

    def _choose_ambiguous_replacement(self, term_info: dict, tokens: list, idx: int, window: int = 3) -> Optional[str]:
        start = max(0, idx - window)
        end = min(len(tokens), idx + window + 1)
        context_tokens = set(tokens[start:idx] + tokens[idx + 1:end])

        for sense in term_info.get("senses", []):
            keywords = sense.get("keywords", [])
            if any(keyword in context_tokens for keyword in keywords):
                return sense.get("replacement")

        return term_info.get("default")

    @staticmethod
    def _preserve_case(original: str, replacement: str) -> str:
        if not replacement:
            return replacement
        if original.isupper():
            return replacement.upper()
        if original[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement
    
    def get_shortforms_count(self) -> int:
        """Return the number of shortforms loaded."""
        return len(self._shortforms)
    
    def get_categories_count(self) -> dict:
        """Return count of terms by category."""
        raw = RAW_DICTIONARY
        dialects = raw.get("dialects", {})
        dialect_count = 0
        for dialect_name, terms in dialects.items():
            if DIALECT_STATUS.get(dialect_name, "active") != "active":
                continue
            if not isinstance(terms, dict):
                continue
            dialect_count += len({k: v for k, v in terms.items() if not k.startswith("_")})
        return {
            "standard": len(raw.get("shortforms", {})),
            "dialects": dialect_count,
            "genz_tiktok": len({k: v for k, v in raw.get("genz_tiktok", {}).items() if not k.startswith("_")}),
            "intensity_markers": len({k: v for k, v in raw.get("intensity_markers", {}).items() if not k.startswith("_")}),
            "colloquialisms": len({k: v for k, v in raw.get("colloquialisms", {}).items() if not k.startswith("_")}),
            "ambiguous_terms": len({k: v for k, v in raw.get("ambiguous_terms", {}).items() if not k.startswith("_")}),
        }


class DialectDetector:
    """
    Detects Malaysian regional dialects from text.
    
    Supported dialects:
    - Kelantanese (Kelantan)
    - Terengganu
    - Kedah/Perlis (Northern)
    - Perak
    - Negeri Sembilan (Minang influence)
    - Penang (Hokkien influence)
    - Sabah (East Malaysia)
    - Sarawak (East Malaysia)
    - Additional draft dialects are listed in docs/dialects.md
    """
    
    DIALECT_INDICATORS = {
        "kelantanese": [
            "gok", "make", "mok", "ambo", "kawe", "demo", "ore", "kito",
            "gapo", "guano", "guane", "nok", "dok", "takdok", "toksey",
            "toksah", "bekwoh", "budu", "kelate", "maghi", "molek",
            "buleh", "pitis", "pitih", "aghi", "ghoyak", "oyak", "tubik",
            "sokmo", "napok", "bilo", "mano", "sapo", "apo"
        ],
        "terengganu": [
            "deh", "wak", "moh", "mung", "dok", "nok", "kekgi", "dunung", "ning", "ganu",
            "tranung", "ghalik", "gedebe", "cakak", "nawok", "pahit",
            "lebong", "ambe"
        ],
        "kedah_perlis": [
            "hang", "depa", "hampa", "awat", "pasaipa", "kot", "mai",
            "habaq", "habak", "hamboih", "cekeding", "loqlaq", "gedegak",
            "pulon", "pungkoq", "paloq", "toksah", "takdak", "satgi", "teman"
        ],
        "perak": [
            "den", "kome", "ghoyat", "ngape", "nape", "toksey",
            "awok", "ceghita", "kelako"
        ],
        "negeri_sembilan": [
            "den", "ghomeh", "bona", "poi", "ontah", "dek",
            "tako", "bodosing", "suko", "ado", "tokdo", "cito", "kojo"
        ],
        "penang": [
            "lu", "gua", "wa", "tarak", "tada", "hampalang", "kasi",
            "cincai", "jiak", "ho seh", "ho liao", "siao", "kiasu",
            "kiasi", "lampah", "angmoh", "leng lui", "leng zai",
            "beh tahan", "bo jio"
        ],
        "sabah": [
            "bah", "sia", "bilang", "nda", "ndak", "tida", "pigi",
            "buli", "tinguk", "santik", "inda", "gia", "palui",
            "basar", "kicil"
        ],
        "sarawak": [
            "kitak", "kamek", "sik", "nang", "dolok", "kelak", "maok",
            "mok", "polah", "madah", "juak", "tok", "sidak", "balit",
            "berik"
        ],
        "johor_riau": [],
        "melaka": [],
        "pahang": [],
        "selangor_kl": [],
        "kedah": [],
        "perlis": [],
        "labuan": [],
        "brunei_malay": ["biskita", "bisai", "banar", "ganya"],
        "banjar": ["ulun", "ikam", "pian", "kada", "handak"],
        "minangkabau": ["urang", "indak", "bana", "dima", "samo"],
        "baba_malay": ["lu punya", "gua punya"],
        "chitty_malay": [],
        "bazaar_malay": ["bikin", "tarak"],
        "patani_malay": []
    }
    
    # Dialect display names
    DIALECT_NAMES = {
        "kelantanese": "Kelantanese (Kelantan)",
        "terengganu": "Terengganu",
        "kedah_perlis": "Kedah/Perlis (Northern)",
        "perak": "Perak",
        "negeri_sembilan": "Negeri Sembilan (Minang)",
        "penang": "Penang (Hokkien-Malay)",
        "sabah": "Sabah (East Malaysia)",
        "sarawak": "Sarawak (East Malaysia)",
        "johor_riau": "Johor-Riau (Southern Malay)",
        "melaka": "Melaka",
        "pahang": "Pahang (East Coast)",
        "selangor_kl": "Selangor/Klang Valley",
        "kedah": "Kedah (Northern Malay)",
        "perlis": "Perlis (Northern Malay)",
        "labuan": "Labuan (Borneo)",
        "brunei_malay": "Brunei Malay (Borneo)",
        "banjar": "Banjar Malay",
        "minangkabau": "Minangkabau",
        "baba_malay": "Baba Malay (Peranakan)",
        "chitty_malay": "Chitty Malay (Peranakan)",
        "bazaar_malay": "Bazaar/Pasar Malay",
        "patani_malay": "Patani/Thai-Malay",
        "standard": "Standard Malay/Manglish"
    }

    def _combined_indicators(self) -> Dict[str, list]:
        """Merge static indicators with lexicon-driven dialect terms."""
        combined = {dialect: list(terms) for dialect, terms in self.DIALECT_INDICATORS.items()}
        raw_dialects = RAW_DICTIONARY.get("dialects", {})
        if isinstance(raw_dialects, dict):
            for dialect, payload in raw_dialects.items():
                if not isinstance(payload, dict):
                    continue
                combined.setdefault(dialect, [])
                for term in payload.keys():
                    if str(term).startswith("_"):
                        continue
                    combined[dialect].append(str(term).lower())
        # De-duplicate while preserving order
        for dialect, terms in combined.items():
            seen = set()
            uniq = []
            for term in terms:
                if term in seen:
                    continue
                seen.add(term)
                uniq.append(term)
            combined[dialect] = uniq
        return combined
    
    def detect(self, text: str) -> Tuple[str, float, list]:
        """
        Detect the dialect of the input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (dialect_code, confidence, matched_words)
        """
        text_lower = text.lower()
        words = re.findall(r"\b\w+\b", text_lower)
        
        indicators = self._combined_indicators()
        active_dialects = {
            dialect: terms
            for dialect, terms in indicators.items()
            if DIALECT_STATUS.get(dialect, "active") == "active" and terms
        }
        if not active_dialects:
            return "standard", 0.0, []

        scores = {}
        matches = {}

        for dialect, indicators in active_dialects.items():
            matched = []
            for indicator in indicators:
                if " " in indicator:
                    if indicator in text_lower:
                        matched.append(indicator)
                elif indicator in words:
                    matched.append(indicator)
            min_required = DIALECT_MIN_MATCHES.get(dialect, 1)
            if len(matched) < min_required:
                matched = []
            scores[dialect] = (len(matched), sum(len(term) for term in matched))
            matches[dialect] = matched
        
        # Find best match
        if scores and max(score[0] for score in scores.values()) > 0:
            best_dialect = max(scores, key=scores.get)
            # Confidence based on ratio of dialect words to total words
            confidence = min(scores[best_dialect][0] / max(len(words), 1), 1.0)
            return best_dialect, confidence, matches[best_dialect]
        
        return "standard", 0.0, []
    
    def get_dialect_name(self, dialect_code: str) -> str:
        """Get the human-readable name for a dialect code."""
        return self.DIALECT_NAMES.get(dialect_code, dialect_code)
    
    def get_all_dialects(self, include_draft: bool = False) -> list:
        """Get list of dialect codes (active by default)."""
        if include_draft:
            return list(self.DIALECT_INDICATORS.keys())
        return [
            dialect
            for dialect in self.DIALECT_INDICATORS.keys()
            if DIALECT_STATUS.get(dialect, "active") == "active"
        ]


class ParticleAnalyzer:
    """
    Analyzes Malaysian discourse particles for sentiment and intent.
    
    Particles are words that add emotional nuance without direct translations:
    - lah: emphasis, softener, persuasion
    - meh: skepticism, doubt
    - lor: resignation, acceptance
    - kan: seeking confirmation
    - weh/wei: attention getter
    etc.
    """
    
    # (particle, sentiment_modifier, intent)
    PARTICLES = {
        "lah": ("softener", "emphasis"),
        "la": ("softener", "casual"),
        "meh": ("skeptical", "doubt"),
        "mah": ("assertive", "explanation"),
        "lor": ("resigned", "acceptance"),
        "loh": ("resigned", "acceptance"),
        "leh": ("seeking_permission", "question"),
        "kan": ("seeking_confirmation", "question"),
        "weh": ("attention", "addressing"),
        "wei": ("attention", "addressing"),
        "woii": ("attention", "strong_addressing"),
        "woi": ("attention", "addressing"),
        "geh": ("assertive", "certainty"),
        "ge": ("assertive", "certainty"),
        "hor": ("seeking_agreement", "question"),
        "ar": ("questioning", "softener"),
        "ah": ("questioning", "softener"),
        "one": ("emphasis", "assertion"),
        "sia": ("exclamation", "emphasis"),
        "bah": ("affirmation", "emphasis"),  # Sabahan
        "deh": ("emphasis", "assertion"),  # Terengganu
    }
    
    # Sentiment mapping
    SENTIMENT_MAP = {
        "softener": "friendly",
        "skeptical": "doubtful",
        "resigned": "accepting",
        "assertive": "confident",
        "seeking_confirmation": "uncertain",
        "seeking_agreement": "uncertain",
        "seeking_permission": "polite",
        "attention": "neutral",
        "questioning": "curious",
        "emphasis": "strong",
        "exclamation": "excited",
        "affirmation": "positive",
    }
    
    def analyze(self, text: str) -> dict:
        """
        Analyze particles in the text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with particles found, overall sentiment, and analysis
        """
        text_lower = text.lower()
        found_particles = []
        
        for particle, (sentiment, intent) in self.PARTICLES.items():
            # Check various positions where particles appear
            patterns = [
                rf"^{re.escape(particle)}[\s,!?]",  # Start of text
                rf"^{re.escape(particle)}$",        # Only token
                rf"\s{re.escape(particle)}$",      # End of text
                rf"\s{re.escape(particle)}\s",     # Middle of text
                rf"\s{re.escape(particle)}[,.]",   # Before punctuation
                rf"\s{re.escape(particle)}[!?]",   # Before exclamation/question
            ]
            
            for pattern in patterns:
                if re.search(pattern, text_lower) or text_lower.endswith(f" {particle}"):
                    found_particles.append({
                        "particle": particle,
                        "sentiment": sentiment,
                        "intent": intent,
                        "sentiment_label": self.SENTIMENT_MAP.get(sentiment, "neutral")
                    })
                    break
        
        # Determine overall sentiment
        overall_sentiment = "neutral"
        if found_particles:
            sentiments = [p["sentiment"] for p in found_particles]
            if "skeptical" in sentiments:
                overall_sentiment = "doubtful"
            elif "resigned" in sentiments:
                overall_sentiment = "accepting"
            elif "assertive" in sentiments:
                overall_sentiment = "confident"
            elif "softener" in sentiments:
                overall_sentiment = "friendly"
            elif "exclamation" in sentiments:
                overall_sentiment = "excited"
            elif "affirmation" in sentiments:
                overall_sentiment = "positive"
        
        return {
            "particles": found_particles,
            "overall_sentiment": overall_sentiment,
            "particle_count": len(found_particles),
            "has_particles": len(found_particles) > 0
        }
    
    def get_response_hint(self, analysis: dict) -> str:
        """
        Generate a hint for LLM response based on particle analysis.
        
        Args:
            analysis: Output from analyze() method
            
        Returns:
            String hint for LLM prompt enhancement
        """
        if not analysis["has_particles"]:
            return ""
        
        particles = [p["particle"] for p in analysis["particles"]]
        sentiment = analysis["overall_sentiment"]
        
        hints = {
            "doubtful": "User seems skeptical. Address their doubt with evidence or reassurance.",
            "accepting": "User seems resigned/accepting. Be supportive and understanding.",
            "confident": "User is being assertive. Match their confident tone.",
            "friendly": "User is being casual and friendly. Keep the conversation warm.",
            "excited": "User seems excited! Match their energy.",
            "neutral": "User is using casual Malaysian speech patterns.",
        }
        
        base_hint = hints.get(sentiment, hints["neutral"])
        
        return f"""
PARTICLE ANALYSIS:
- Particles detected: {', '.join(particles)}
- User tone: {sentiment}
- Suggestion: {base_hint}
- Mirror their casual style. Use appropriate particles in response (lah, kan, etc.).
"""


class MalaysianSentimentAnalyzer:
    """
    Analyzes sentiment in Malaysian text, handling local expressions.
    
    Challenges addressed:
    - Expletives as intensifiers (gila babi = very, not negative)
    - Sarcasm detection
    - Malaysian exclamations
    """
    
    POSITIVE_INTENSIFIERS = [
        "best", "power", "gempak", "terbaik", "syok", "mantap", 
        "hebat", "terror", "steady", "cantik", "sedap", "padu",
        "superb", "awesome", "amazing", "nice", "good", "great"
    ]
    
    NEGATIVE_INTENSIFIERS = [
        "teruk", "bodoh", "bengap", "sial", "hampeh", "fail",
        "malap", "hambar", "boring", "bad", "terrible", "worst",
        "suck", "sucks", "hate", "benci"
    ]
    
    # These are context-dependent - can be positive OR negative
    NEUTRAL_EXPLETIVES = [
        "siot", "gila", "babi", "celaka", "cibai", "damn", "hell"
    ]
    
    POSITIVE_EXCLAMATIONS = [
        "pergh", "fuyo", "fuyoh", "wah", "wahlao", "woohoo", 
        "yay", "yes", "wow", "omg"
    ]
    
    NEGATIVE_EXCLAMATIONS = [
        "haih", "aih", "aduh", "alamak", "aiya", "aiyo", "ish", "cis"
    ]
    
    def analyze(self, text: str) -> dict:
        """
        Analyze sentiment of Malaysian text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with sentiment, confidence, and analysis details
        """
        text_lower = text.lower()
        
        # Count indicators
        positive_score = sum(
            1 for word in self.POSITIVE_INTENSIFIERS 
            if word in text_lower
        )
        positive_score += sum(
            0.5 for word in self.POSITIVE_EXCLAMATIONS 
            if word in text_lower
        )
        
        negative_score = sum(
            1 for word in self.NEGATIVE_INTENSIFIERS 
            if word in text_lower
        )
        negative_score += sum(
            0.5 for word in self.NEGATIVE_EXCLAMATIONS 
            if word in text_lower
        )
        
        # Handle expletives (context-dependent)
        for expletive in self.NEUTRAL_EXPLETIVES:
            if expletive in text_lower:
                # "gila best" = positive, "gila bodoh" = negative
                if any(pos in text_lower for pos in self.POSITIVE_INTENSIFIERS):
                    positive_score += 0.5
                elif any(neg in text_lower for neg in self.NEGATIVE_INTENSIFIERS):
                    negative_score += 0.5
        
        # Determine sentiment
        if positive_score > negative_score:
            sentiment = "positive"
            confidence = min(0.5 + (positive_score * 0.1), 0.95)
        elif negative_score > positive_score:
            sentiment = "negative"
            confidence = min(0.5 + (negative_score * 0.1), 0.95)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_score": positive_score,
            "negative_score": negative_score,
            "analysis": {
                "positive_words": [w for w in self.POSITIVE_INTENSIFIERS if w in text_lower],
                "negative_words": [w for w in self.NEGATIVE_INTENSIFIERS if w in text_lower],
                "expletives": [w for w in self.NEUTRAL_EXPLETIVES if w in text_lower]
            }
        }
    
    def get_response_hint(self, analysis: dict) -> str:
        """Generate LLM hint based on sentiment analysis."""
        sentiment = analysis["sentiment"]
        
        if sentiment == "positive":
            return "\n\nNOTE: User seems happy/excited. Match their positive energy!"
        elif sentiment == "negative":
            return "\n\nNOTE: User seems frustrated or unhappy. Be empathetic and helpful."
        else:
            return ""
