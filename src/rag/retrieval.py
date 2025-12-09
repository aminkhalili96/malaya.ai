from typing import List, Dict
import hashlib
import re
from rank_bm25 import BM25Okapi
import numpy as np

class HybridRetriever:
    def __init__(self, docs: List[Dict], vector_dim: int = 256, trusted_domains: List[str] = None, excluded_domains: List[str] = None):
        """
        Initialize with a list of documents (child chunks).
        docs format: [{"content": "...", "metadata": {...}}]
        trusted_domains: List of domains to prioritize (e.g., ["gov.my", "edu.my"])
        excluded_domains: List of domains to exclude (e.g., ["reddit.com"])
        """
        self.docs = docs or []
        self.vector_dim = vector_dim
        self.trusted_domains = trusted_domains or []
        self.excluded_domains = excluded_domains or []
        self.corpus = [d.get("content", "") for d in self.docs]
        
        # Initialize BM25 only if we have docs
        tokenized_corpus = [self._tokenize(doc) for doc in self.corpus]
        has_tokens = any(len(toks) > 0 for toks in tokenized_corpus)
        self.bm25 = BM25Okapi(tokenized_corpus) if self.corpus and has_tokens else None

        # Lightweight deterministic embeddings (hashed bag-of-words) to avoid random results
        self.embeddings = self._build_embeddings(self.corpus)

    def _tokenize(self, text: str):
        return re.findall(r"\b\w+\b", text.lower())

    def _hash_token(self, token: str) -> int:
        return int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % self.vector_dim

    def _embed_text(self, text: str) -> np.ndarray:
        vec = np.zeros(self.vector_dim, dtype=float)
        for tok in self._tokenize(text):
            vec[self._hash_token(tok)] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec

    def _build_embeddings(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        return np.vstack([self._embed_text(text) for text in texts])

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        if scores.size == 0:
            return scores
        if np.allclose(scores, 0):
            return np.zeros_like(scores)
        max_score = scores.max()
        min_score = scores.min()
        if np.isclose(max_score, min_score):
            return np.ones_like(scores)
        return (scores - min_score) / (max_score - min_score)

    def search(self, query: str, k=3) -> List[Dict]:
        """
        Performs Hybrid Search:
        1. BM25 (Keyword)
        2. Vector Search (Semantic) - Mocked
        3. Tavily Web Search (if enabled)
        4. Boost trusted domains
        """
        results = []
        results.extend(self._web_search(query))
        results.extend(self._search_local(query, k))
        
        # Filter excluded domains
        filtered_results = []
        for res in results:
            source = res.get("metadata", {}).get("source", "")
            if not any(ex in source for ex in self.excluded_domains):
                filtered_results.append(res)
        results = filtered_results
        
        # Boost trusted domains
        for res in results:
            metadata = res.get("metadata", {})
            source = metadata.get("source", "")
            if any(domain in source for domain in self.trusted_domains):
                # Boost score by 2x for trusted domains
                if "scores" in metadata:
                    metadata["scores"]["combined"] = metadata["scores"].get("combined", 0) * 2.0
                    metadata["scores"]["boosted"] = True
        
        # Sort by combined score (highest first)
        results.sort(key=lambda x: x.get("metadata", {}).get("scores", {}).get("combined", 0), reverse=True)
        
        return results[:k]

    def _search_local(self, query: str, k: int) -> List[Dict]:
        if not self.docs:
            return []

        bm25_scores = self.bm25.get_scores(self._tokenize(query)) if self.bm25 else np.zeros(len(self.docs))
        vector_scores = self.embeddings @ self._embed_text(query) if self.embeddings.size else np.zeros(len(self.docs))

        bm25_norm = self._normalize_scores(bm25_scores)
        vector_norm = self._normalize_scores(vector_scores)

        combined = 0.6 * bm25_norm + 0.4 * vector_norm
        top_indices = np.argsort(combined)[::-1][:k]

        ranked = []
        for idx in top_indices:
            doc = self.docs[idx].copy()
            meta = doc.get("metadata", {}).copy()
            meta["scores"] = {
                "bm25": float(round(bm25_norm[idx], 3)),
                "semantic": float(round(vector_norm[idx], 3)),
                "combined": float(round(combined[idx], 3)),
            }
            doc["metadata"] = meta
            ranked.append(doc)
        return ranked

    def _web_search(self, query: str) -> List[Dict]:
        import os

        if "TAVILY_API_KEY" not in os.environ:
            print("Warning: TAVILY_API_KEY not set, web search disabled")
            return []

        results = []
        try:
            from tavily import TavilyClient

            tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
            # Enhanced search with advanced depth for better results
            web_res = tavily.search(
                query=query, 
                max_results=5,  # Increased for better coverage
                search_depth="advanced",  # Better quality results
                exclude_domains=self.excluded_domains,
                include_answer=True  # Get a direct answer if available
            )
            
            # If Tavily provides a direct answer, include it first
            if web_res.get("answer"):
                results.append({
                    "content": f"[WEB SUMMARY] {web_res['answer']}",
                    "metadata": {
                        "source": "Tavily AI Summary",
                        "parent_id": "web_summary",
                        "scores": {"combined": 2.0}  # High priority
                    }
                })
            
            for res in web_res.get("results", []):
                # Use raw_content if available for more context
                content = res.get("raw_content", res.get("content", ""))
                if content:
                    # Limit content length to avoid token overflow
                    content = content[:1500] if len(content) > 1500 else content
                    results.append({
                        "content": f"[WEB] {content}",
                        "metadata": {
                            "source": res.get("url", "unknown"), 
                            "title": res.get("title", ""),
                            "parent_id": "web",
                            "scores": {"combined": 1.0}
                        },
                    })
        except Exception as e:
            print(f"Tavily Error: {e}")
        
        print(f"Web search returned {len(results)} results")
        return results

