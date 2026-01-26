from typing import List, Dict, Optional, Any
import logging
from src.rag.retrieval import HybridRetriever

class RAGService:
    """
    Service for Handling Retrieval Augmented Generation (RAG) operations.
    Decouples retrieval logic from the main chatbot engine.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Retriever
        trusted_domains = self.config.get("rag", {}).get("trusted_domains", [])
        excluded_domains = self.config.get("rag", {}).get("excluded_domains", [])
        
        self.retriever = HybridRetriever(
            docs=self._load_knowledge_base(), 
            trusted_domains=trusted_domains,
            excluded_domains=excluded_domains
        )
        self.logger.info("RAGService initialized.")

    def _load_knowledge_base(self) -> List[Dict]:
        """Load extracted Malaya knowledge from data/knowledge/*.json"""
        import os
        import json
        import glob
        
        docs = []
        knowledge_dir = "data/knowledge"
        
        if not os.path.exists(knowledge_dir):
            self.logger.warning(f"Knowledge directory {knowledge_dir} not found.")
            return []
            
        json_files = glob.glob(os.path.join(knowledge_dir, "*.json"))
        for fpath in json_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Strategy: Flatten different structures into 'content' strings
                    filename = os.path.basename(fpath)
                    
                    # 1. Locations / Places / Schools / Medical
                    if "places" in data or "entities" in data:
                        items = data.get("places") or data.get("entities")
                        for item in items:
                            # If it's a string (location name)
                            if isinstance(item, str):
                                docs.append({
                                    "content": f"{item} is a known location/entity in Malaysia.",
                                    "metadata": {"source": filename, "type": "entity"}
                                })
                            # If it's an object? (Not in current extraction script, but good for future)
                    
                    # 2. Politics (Parliament)
                    elif "parliament_seats" in data:
                        for seat in data["parliament_seats"]:
                            # seat is {"seat": "P.123 Name"}
                            name = seat.get("seat", "")
                            docs.append({
                                "content": f"{name} is a Parliament seat in Malaysia.",
                                "metadata": {"source": filename, "type": "politics"}
                            })
                            
                    # 3. Geography (States/Countries)
                    elif "states" in data:
                        for s in data["states"]:
                            docs.append({
                                "content": f"{s} is a state/territory in Malaysia.",
                                "metadata": {"source": filename, "type": "geography"}
                            })
                    
                    # 4. Cities
                    elif "cities" in data:
                        for c in data["cities"]:
                            docs.append({
                                "content": f"{c} is a city in Malaysia.",
                                "metadata": {"source": filename, "type": "geography"}
                            })
                            
            except Exception as e:
                self.logger.error(f"Failed to load knowledge {fpath}: {e}")
                
        self.logger.info(f"Loaded {len(docs)} documents from knowledge base.")
        return docs

    # Stopwords/slang that should NOT trigger RAG location search
    RAG_BLACKLIST = {
        # Particles
        "lah", "la", "meh", "lor", "hor", "geh", "kan", "kan", "leh", "weh", "wei",
        "bah", "gok", "mung", "dok", "dah", "doh", "nah", "tu", "ni", "ye", "ya",
        # Slang/Exclamations
        "gila", "siot", "best", "power", "steady", "gempak", "syok", "shiok", "swee",
        "terror", "fuyoh", "fulamak", "walao", "wah", "eh", "oi", "bro", "sis",
        # Common words
        "aku", "kau", "awak", "saya", "dia", "mereka", "kami", "kita",
        "tak", "tidak", "tiada", "ada", "boleh", "xleh", "xde", "xnak",
        "nak", "mau", "mahu", "pergi", "datang", "buat", "jadi", "tahu",
        "gembira", "sedih", "marah", "takut", "suka", "happy", "sad",
        # Slang/Dialect markers to avoid context poisoning
        "acah", "pishang", "koyak", "ape", "cer", "tokene", "bakpo", "mung",
        "dop", "mat", "weh", "wei", "bro", "sis",
        # Filler
        "macam", "mcm", "camne", "camana", "ok", "okay", "okey", "alright",
    }
    
    # Keywords that SHOULD trigger factual/location RAG
    FACTUAL_KEYWORDS = {
        "mana", "dimana", "di mana", "where", "alamat", "address", "lokasi", "location",
        "sekolah", "hospital", "klinik", "universiti", "kolej", "masjid", "gereja", "kuil",
        "parlimen", "dun", "kawasan", "daerah", "negeri", "bandar", "kampung", "taman",
        "jalan", "lorong", "how to get", "directions", "route", "dekat", "nearby",
        "cari", "find", "search", "recommend", "cadang", "suggest",
        # Added for 95% acc
        "siapa", "sape", "who", "pm", "perdana", "menteri", "minister",
        "harga", "kos", "price", "cost", "bayar", "pay", "fee", "yuran",
        "bila", "when", "tarikh", "date", "cuti", "holiday",
        "cara", "how", "step", "guide", "panduan", "syarat", "requirement",
        "resipi", "resepi", "recipe", "menu",
    }

    def _is_factual_query(self, query: str) -> bool:
        """
        Determine if the query is asking for factual/location information.
        Returns True if RAG should be used, False for casual chat.
        """
        query_lower = query.lower()
        words = set(query_lower.split())
        
        # Check for factual keywords
        for keyword in self.FACTUAL_KEYWORDS:
            if keyword in query_lower:
                return True
        
        # Check if query is mostly blacklisted words (casual chat)
        non_blacklist = words - self.RAG_BLACKLIST
        if len(non_blacklist) <= 2:  # Very short meaningful content = casual
            return False
        
        # Check for question patterns about locations
        question_patterns = ["apa", "berapa", "siapa", "bila", "bagaimana", "mengapa", "what", "who", "when", "how", "why"]
        has_question = any(q in query_lower for q in question_patterns)
        
        # If it's a question with substance, might be factual
        if has_question and len(non_blacklist) > 3:
            return True
            
        return False

    def should_search(self, query: str) -> bool:
        """Public gate for RAG usage."""
        return self._is_factual_query(query)

    def search_raw(self, query: str, k: int = 5, use_web: bool = True) -> List[Dict]:
        """
        Return raw search results, applying intent gating.
        """
        if not self._is_factual_query(query):
            self.logger.info(f"RAG skipped (casual chat detected): {query[:50]}...")
            return []
        return self.retriever.search(query, k=k, use_web=use_web)

    def search(self, query: str, k: int = 5, use_web: bool = True) -> str:
        """
        Perform a hybrid search (Vector + Keyword + Web).
        Now with Intent Gate: only retrieves for factual queries.
        
        Args:
            query: The user's search query.
            k: Number of results to return.
            
        Returns:
            Formatted context string.
        """
        # Intent Gate: Skip RAG for casual chat
        results = self.search_raw(query, k=k, use_web=use_web)
        
        # Format results into a context block
        if not results:
            return ""
            
        context_parts = []
        for i, res in enumerate(results, 1):
            content = res.get("content", "").strip()
            source = res.get("metadata", {}).get("source", "unknown")
            if content:
                context_parts.append(f"[{i}] {content} (Source: {source})")
                
        return "\n\n".join(context_parts)

    def add_documents(self, documents: List[str]):
        """
        Add documents to the retriever index.
        """
        if hasattr(self.retriever, 'add_documents'):
             self.retriever.add_documents(documents)
        else:
            self.logger.warning("Retriever does not support dynamic document addition.")

    def get_retriever(self):
        """Return the underlying retriever instance if needed."""
        return self.retriever

def get_rag_service(config: Dict[str, Any] = None):
    """Singleton accessor for RAGService."""
    if config is None:
        # Load default config if none provided (simplified)
        config = {
            "rag": {
                "trusted_domains": ["gov.my", "edu.my"],
                "excluded_domains": ["reddit.com", "ycombinator.com"],
                # Add reasonable defaults
                "k": 5
            }
        }
    return RAGService(config)
