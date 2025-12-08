import re
import os
import json

try:
    import malaya
except Exception as exc:  # Malaya might be unavailable in some environments
    malaya = None
    MALAYA_IMPORT_ERROR = exc


def _load_shortforms():
    """Load bundled shortforms dictionary from JSON file."""
    try:
        # Get the path to shortforms.json relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        shortforms_path = os.path.join(current_dir, "..", "data", "shortforms.json")
        
        if os.path.exists(shortforms_path):
            with open(shortforms_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("shortforms", {})
    except Exception as e:
        print(f"Warning: Could not load shortforms.json: {e}")
    
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


# Load shortforms once at module level
SHORTFORMS = _load_shortforms()


class TextNormalizer:
    def __init__(self):
        # Load the actual Malaya normalizer when available; fall back gracefully otherwise
        self._malaya_available = False
        self._init_error = None
        self.normalizer = None
        self._shortforms = SHORTFORMS

        if malaya:
            try:
                # Prefer the non-deprecated loader; fall back to the older API if needed
                if hasattr(malaya, "normalizer") and hasattr(malaya.normalizer, "rules"):
                    self.normalizer = malaya.normalizer.rules.load()
                else:
                    self.normalizer = malaya.normalize.normalizer()
                self._malaya_available = True
            except Exception as exc:  # keep running even if model download/setup fails
                self._init_error = exc

    def normalize(self, text: str) -> str:
        """
        Normalizes 'Bahasa Rojak' and 'Manglish' using huseinzol05/Malaya.
        Falls back to bundled 150+ shortforms dictionary if Malaya unavailable.
        """
        text = text.strip()

        if self._malaya_available and self.normalizer:
            try:
                normalized = self.normalizer.normalize(text)
                # Newer Malaya returns a string; older returns a dict
                if isinstance(normalized, dict) and "normalize" in normalized:
                    normalized = normalized["normalize"]
                if isinstance(normalized, str):
                    return normalized
            except Exception as exc:
                # Fall through to lightweight normalization while preserving the init error
                self._init_error = self._init_error or exc

        # Enhanced fallback using bundled shortforms dictionary (150+ terms)
        normalized = text
        for slang, clean in self._shortforms.items():
            # Use word boundary matching to avoid partial replacements
            normalized = re.sub(
                rf"\b{re.escape(slang)}\b", 
                clean, 
                normalized, 
                flags=re.IGNORECASE
            )

        # Clean up extra whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized
    
    def get_shortforms_count(self) -> int:
        """Return the number of shortforms loaded."""
        return len(self._shortforms)
