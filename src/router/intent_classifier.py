
class IntentClassifier:
    def __init__(self):
        base_fact_keywords = [
            "bila", "siapa", "dimana", "di mana", "berapa", "harga",
            "latest", "terkini", "2024", "2025", "next",
            "winner", "pemenang", "keputusan", "result",
            "perdana menteri", "pm", "agong", "tarikh",
            "syarat", "permohonan", "apply", "how to", "cara",
            "lokasi", "alamat", "where", "mana", "nearby",
            "maksud", "apa itu", "apa maksud", "meaning",
        ]
        self.fact_keywords = base_fact_keywords + self._load_fact_keywords()
        self.slang_keywords = self._load_slang_keywords()
        self.dialect_keywords = self._load_dialect_keywords()

    def _load_fact_keywords(self):
        """Load fact-trigger keywords from local knowledge base."""
        try:
            import json
            with open("data/knowledge/v4_facts.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            keywords = set()
            for item in data:
                for key in item.get("keywords", []):
                    if key:
                        keywords.add(str(key).lower())
            return sorted(keywords)
        except Exception:
            return []

    def _load_dialect_keywords(self):
        """Load dialect markers from unified lexicon if available."""
        try:
            import json
            with open("src/data/shortforms.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            dialects = data.get("dialects", {})
            markers = set()
            for payload in dialects.values():
                if not isinstance(payload, dict):
                    continue
                for term in payload.keys():
                    if str(term).startswith("_"):
                        continue
                    markers.add(str(term).lower())
            return sorted(markers)
        except Exception:
            return []

    def _load_slang_keywords(self):
        """Load slang/shortform markers from unified lexicon if available."""
        try:
            import json
            with open("src/data/shortforms.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            markers = set()
            for section in ["shortforms", "colloquialisms", "genz_tiktok", "intensity_markers"]:
                block = data.get(section, {})
                if isinstance(block, dict):
                    for term in block.keys():
                        if str(term).startswith("_"):
                            continue
                        markers.add(str(term).lower())
            return sorted(markers)
        except Exception:
            return []

    def classify(self, text):
        """
        Returns 'fact' or 'chat'.
        Decides if RAG is necessary.
        """
        text_lower = text.lower()
        words = text_lower.split()

        # Special-case: car turn signal context should stay chat, not telco signal.
        if "signal" in text_lower and any(k in text_lower for k in ["driver", "kereta", "jalan", "lane", "memandu", "moto", "lorry"]):
            return "chat"
        
        # 1. Strong Fact Indicators (Override everything)
        if any(k in text_lower for k in self.fact_keywords):
            return "fact"
            
        # 2. Chit-Chat Indicators
        # If it's short (< 6 words) AND contains slang/emotional markers
        if len(words) < 8:
            if any(s in text_lower for s in self.slang_keywords):
                return "chat"
            if any(d in text_lower for d in self.dialect_keywords):
                return "chat"
            if not any(k in text_lower for k in self.fact_keywords):
                return "chat"
                
        # 3. Default to Fact (RAG) for safety
        return "fact"

if __name__ == "__main__":
    classifier = IntentClassifier()
    print(f"sukan sea next kat mana? -> {classifier.classify('sukan sea next kat mana?')}")
    print(f"dia tu acah je -> {classifier.classify('dia tu acah je')}")
