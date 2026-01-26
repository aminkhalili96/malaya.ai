"""
Vector RAG Service - FAISS-based Semantic Search
=================================================
Provides semantic search over Malaysian lexicon definitions.
Uses Malaya embeddings + FAISS for similarity search.
"""

import json
import logging
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorRAGService:
    """
    FAISS-based vector search for Malaysian lexicon.
    Enables semantic queries like "What is reversing?" -> "Gostan"
    """
    
    def __init__(self, lexicon_path: Optional[str] = None):
        self._embedding_model = None
        self._faiss_index = None
        self._lexicon: List[Dict] = []
        self._initialized = False
        
        # Default lexicon path
        full_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'lexicon_full.json')
        legacy_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'lexicon.json')
        if lexicon_path:
            self.lexicon_path = lexicon_path
        else:
            self.lexicon_path = full_path if os.path.exists(full_path) else legacy_path
    
    def _ensure_initialized(self):
        """Lazy initialization of embeddings and FAISS."""
        if self._initialized:
            return
            
        import os
        if os.environ.get("MALAYA_FORCE_MOCK") == "1":
            self._use_mock()
            self._initialized = True
            return

        try:
            # import malaya # Malaya is no longer used for embeddings
            import faiss
            import numpy as np
            
            # self._malaya = malaya # Malaya is no longer used for embeddings
            self._faiss = faiss
            self._np = np
            
            # Load embedding model (Native Mode)
            logger.info("Loading RAG Embeddings (paraphrase-multilingual-MiniLM-L12-v2)...")
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self._np = np
            self._faiss = faiss
            
            # Load lexicon
            self._load_lexicon()
            
            # Build FAISS index
            self._build_index()
            
            self._initialized = True
            logger.info(f"VectorRAGService initialized with {len(self._lexicon)} terms")
            
        except ImportError as e:
            logger.error(f"Failed to import required libraries: {e}")
            raise
        except Exception as e:
            logger.error(f"VectorRAGService initialization failed: {e}")
            raise
    
    def _use_mock(self):
        """Initialize LIGHTWEIGHT implementations (Lite Mode) without Malaya/FAISS."""
        logger.warning("Initializing VectorRAGService in LITE MODE (No TensorFlow).")
        
        # Load lexicon (real logic)
        self._load_lexicon()
        
        # Use simple KEYWORD (Intersection) search for Lite Mode
        # This removes dependency on rank_bm25 and fixes small-corpus issues
        class LiteVectorSearch:
            def __init__(self, lexicon):
                self.lexicon = lexicon
                import re
                self.re = re
                # Pre-tokenize corpus for speed
                self.corpus_tokens = []
                for e in lexicon:
                    text = f"{e['term']} {e['definition']}"
                    # Use set for fast intersection
                    tokens = set(self.re.findall(r"\w+", text.lower()))
                    self.corpus_tokens.append(tokens)
                logger.info(f"LiteVectorSearch (Keyword) initialized with {len(lexicon)} entries")
            
            def search(self, query, top_k=3):
                q_tokens = set(self.re.findall(r"\w+", query.lower()))
                # logger.info(f"Query Tokens: {q_tokens}")
                if not q_tokens: return []
                
                scored_results = []
                for idx, doc_tokens in enumerate(self.corpus_tokens):
                    intersection = len(q_tokens & doc_tokens)
                    # logger.info(f"MATCH Doc {idx}: {self.lexicon[idx]['term']} | Score {intersection}")
                    if intersection > 0:
                        score = float(intersection)
                        term = self.lexicon[idx]['term'].lower()
                        if term in q_tokens:
                            score += 2.0
                        elif term in query.lower():
                             score += 0.5
                             
                        scored_results.append((score, self.lexicon[idx]))
                
                # Sort by score descending
                scored_results.sort(key=lambda x: x[0], reverse=True)
                
                results = []
                for score, entry in scored_results[:top_k]:
                    res = entry.copy()
                    res['score'] = score
                    results.append(res)
                return results

        self._lite_search = LiteVectorSearch(self._lexicon)
        
        # Override search method dynamically for this instance
        self.search = self._lite_search.search
        
        # Dummy objects to satisfy type checkers if needed
        self._embedding_model = None
        self._faiss_index = None
    
    def _load_lexicon(self):
        """Load lexicon from JSON file."""
        lexicon_file = Path(self.lexicon_path)
        
        if lexicon_file.exists():
            try:
                with open(lexicon_file, 'r', encoding='utf-8') as f:
                    self._lexicon = json.load(f)
                logger.info(f"Loaded {len(self._lexicon)} lexicon entries from {lexicon_file}")
            except Exception as e:
                logger.warning(f"Failed to load lexicon: {e}")
                self._lexicon = self._get_default_lexicon()
        else:
            logger.info("No lexicon file found, using default lexicon")
            self._lexicon = self._get_default_lexicon()
            # Save default lexicon
            self._save_lexicon()
    
    def _get_default_lexicon(self) -> List[Dict]:
        """Default Malaysian lexicon with common slang terms."""
        return [
            {"term": "gostan", "definition": "Reverse or move backward (driving). From British nautical term 'go astern'.", "category": "slang"},
            {"term": "tapau", "definition": "Takeaway food. From Cantonese 打包 (dá bāo).", "category": "slang"},
            {"term": "mamak", "definition": "Indian-Muslim restaurant or person. Popular 24-hour eateries in Malaysia.", "category": "culture"},
            {"term": "jalan-jalan", "definition": "Walk around, stroll, go out for leisure.", "category": "phrase"},
            {"term": "makan angin", "definition": "Go on vacation, literally 'eat wind'. Taking a break.", "category": "phrase"},
            {"term": "kopi-o", "definition": "Black coffee without milk. 'O' from Hokkien for black.", "category": "food"},
            {"term": "cincai", "definition": "Whatever, anything, casual. From Hokkien.", "category": "slang"},
            {"term": "kantoi", "definition": "Caught in the act, busted, exposed.", "category": "slang"},
            {"term": "syok", "definition": "Feeling good, enjoyable, satisfying.", "category": "slang"},
            {"term": "lepak", "definition": "Hang out, chill, relax with friends.", "category": "slang"},
            {"term": "yumcha", "definition": "Meet up for drinks/food, from Cantonese 'drink tea'.", "category": "slang"},
            {"term": "potong stim", "definition": "Kill the mood, buzzkill.", "category": "slang"},
            {"term": "bapak", "definition": "Very, extremely (intensifier). Also means father.", "category": "slang"},
            {"term": "gila", "definition": "Crazy, but often used as intensifier for 'very'.", "category": "slang"},
            {"term": "terror", "definition": "Awesome, skilled, impressive.", "category": "slang"},
            {"term": "power", "definition": "Great, excellent, impressive.", "category": "slang"},
            {"term": "steady", "definition": "Cool, reliable, can handle it.", "category": "slang"},
            {"term": "satu malaysia", "definition": "One Malaysia - national unity concept.", "category": "culture"},
            {"term": "roti canai", "definition": "Flaky flatbread, popular Malaysian breakfast.", "category": "food"},
            {"term": "nasi lemak", "definition": "Coconut rice with sambal, Malaysia's national dish.", "category": "food"},
        ]
    
    def _save_lexicon(self):
        """Save lexicon to JSON file."""
        lexicon_file = Path(self.lexicon_path)
        lexicon_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(lexicon_file, 'w', encoding='utf-8') as f:
                json.dump(self._lexicon, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved lexicon to {lexicon_file}")
        except Exception as e:
            logger.error(f"Failed to save lexicon: {e}")
    
    def _build_index(self):
        """Build FAISS index from lexicon embeddings."""
        if not self._lexicon:
            logger.warning("No lexicon entries to index")
            return
        
        try:
            # Create embeddings for all terms + definitions
            texts = [f"{entry['term']}: {entry['definition']}" for entry in self._lexicon]
            embeddings = self._embedding_model.encode(texts)
            
            # Convert to numpy array
            embeddings_np = self._np.array(embeddings).astype('float32')
            
            # Create FAISS index
            dimension = embeddings_np.shape[1]
            self._faiss_index = self._faiss.IndexFlatL2(dimension)
            self._faiss_index.add(embeddings_np)
            
            logger.info(f"Built FAISS index with {len(texts)} entries, dimension={dimension}")
            
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")
            self._faiss_index = None
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for similar terms in the lexicon.
        Returns top-k most similar entries.
        """
        self._ensure_initialized()
        
        # Delegate to Lite Search if active (Lite Mode)
        if hasattr(self, '_lite_search'):
             return self._lite_search.search(query, top_k)
        
        self._ensure_initialized()
        
        if self._faiss_index is None or not self._lexicon:
            return []
        
        try:
            # Get query embedding
            query_embedding = self._embedding_model.encode([query])
            query_np = self._np.array(query_embedding).astype('float32')
            
            # Search FAISS index
            distances, indices = self._faiss_index.search(query_np, top_k)
            
            # Return matching entries with scores
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self._lexicon):
                    entry = self._lexicon[idx].copy()
                    entry['score'] = float(1.0 / (1.0 + distances[0][i]))  # Convert distance to similarity
                    results.append(entry)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def add_term(self, term: str, definition: str, category: str = "custom") -> bool:
        """Add a new term to the lexicon and rebuild index."""
        self._ensure_initialized()
        
        # Check if term already exists
        for entry in self._lexicon:
            if entry['term'].lower() == term.lower():
                logger.info(f"Term '{term}' already exists, updating definition")
                entry['definition'] = definition
                entry['category'] = category
                self._save_lexicon()
                self._build_index()
                return True
        
        # Add new term
        self._lexicon.append({
            "term": term,
            "definition": definition,
            "category": category
        })
        self._save_lexicon()
        self._build_index()
        return True
    
    def get_context_for_query(self, query: str, top_k: int = 3) -> str:
        """
        Get relevant lexicon context for a query.
        Returns formatted context string for LLM injection.
        """
        results = self.search(query, top_k)
        
        if not results:
            return ""
        
        context_parts = ["[Malaysian Lexicon Context]"]
        for entry in results:
            context_parts.append(f"- {entry['term']}: {entry['definition']}")
        
        return "\n".join(context_parts)


# Singleton instance
_vector_service: Optional[VectorRAGService] = None


def get_vector_service() -> VectorRAGService:
    """Get or create the singleton VectorRAGService instance."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorRAGService()
    return _vector_service
