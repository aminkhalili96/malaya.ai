
import json
import re

class DialectAdapter:
    def __init__(self, dictionary_path="src/data/shortforms.json"):
        self.dictionary_path = dictionary_path
        self.replacements = self._load_replacements()

    def _load_replacements(self):
        try:
            with open(self.dictionary_path, 'r') as f:
                data = json.load(f)

            flat_map = {}

            # Schema-based lexicon
            if isinstance(data, dict) and "dialects" in data:
                dialects = data.get("dialects", {})
                for _, payload in dialects.items():
                    if not isinstance(payload, dict):
                        continue
                    for term, definition in payload.items():
                        if str(term).startswith("_"):
                            continue
                        clean_def = str(definition).split('(')[0].strip()
                        flat_map[str(term).lower()] = clean_def
            # Legacy v4_dialects.json format
            elif isinstance(data, dict):
                for dialect, terms in data.items():
                    if dialect == "dialects":
                        continue
                    if not isinstance(terms, dict):
                        continue
                    for term, definition in terms.items():
                        clean_def = str(definition).split('(')[0].strip()
                        flat_map[str(term).lower()] = clean_def

            return flat_map
        except Exception as e:
            print(f"Warning: DialectAdapter failed to load dict: {e}")
            return {}

    def translate(self, text):
        """
        Replaces dialect words with standard Malay equivalents.
        """
        if not text:
            return text

        normalized = text
        # Replace multi-word phrases first
        terms = sorted(self.replacements.items(), key=lambda x: len(x[0]), reverse=True)
        for term, replacement in terms:
            normalized = re.sub(
                rf"\\b{re.escape(term)}\\b",
                replacement,
                normalized,
                flags=re.IGNORECASE,
            )
        return normalized

if __name__ == "__main__":
    # Test
    adapter = DialectAdapter()
    print(adapter.translate("bakpo mung dop mari semalam"))
    print(adapter.translate("dia tu acah je"))
