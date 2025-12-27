from typing import List, Dict
import hashlib
import re
from rank_bm25 import BM25Okapi
import numpy as np
from datetime import datetime, timezone
import time

INJECTION_PATTERN = re.compile(
    r"("
    r"ignore (all|any|previous) instructions|"
    r"disregard (all|any|previous) instructions|"
    r"system prompt|developer message|"
    r"you are (chatgpt|an ai)|act as|"
    r"follow these instructions|do not follow|"
    r"begin (system|instructions|prompt)|end (system|instructions|prompt)"
    r")",
    re.IGNORECASE,
)

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception:
    SentenceTransformer = None
    CrossEncoder = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class HybridRetriever:
    def __init__(
        self,
        docs: List[Dict],
        vector_dim: int = 256,
        trusted_domains: List[str] = None,
        excluded_domains: List[str] = None,
        embedding_provider: str = "hash",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        reranker_enabled: bool = False,
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        reranker_top_k: int = 5,
        freshness_weight: float = 0.2,
        web_timeout_seconds: float = 6.0,
        web_failure_threshold: int = 3,
        web_cooldown_seconds: int = 60,
    ):
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
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        self.reranker_enabled = reranker_enabled
        self.reranker_model = reranker_model
        self.reranker_top_k = reranker_top_k
        self.freshness_weight = freshness_weight
        self.web_timeout_seconds = float(web_timeout_seconds)
        self.web_failure_threshold = int(web_failure_threshold)
        self.web_cooldown_seconds = int(web_cooldown_seconds)
        self._web_failure_count = 0
        self._web_circuit_until = 0.0
        
        # Initialize BM25 only if we have docs
        tokenized_corpus = [self._tokenize(doc) for doc in self.corpus]
        has_tokens = any(len(toks) > 0 for toks in tokenized_corpus)
        self.bm25 = BM25Okapi(tokenized_corpus) if self.corpus and has_tokens else None

        # Embeddings
        self._encoder = None
        if embedding_provider == "sentence_transformer" and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self._encoder = SentenceTransformer(embedding_model)
            except Exception:
                self._encoder = None
        self.embeddings = self._build_embeddings(self.corpus)

        # Optional reranker
        self._reranker = None
        if reranker_enabled and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self._reranker = CrossEncoder(reranker_model)
            except Exception:
                self._reranker = None

    def _tokenize(self, text: str):
        return re.findall(r"\b\w+\b", text.lower())

    def _hash_token(self, token: str) -> int:
        return int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % self.vector_dim

    def _embed_text(self, text: str) -> np.ndarray:
        if self._encoder is not None:
            embedding = np.array(self._encoder.encode([text])[0], dtype=float)
            norm = np.linalg.norm(embedding)
            return embedding / norm if norm else embedding
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

    def _sanitize_web_content(self, content: str) -> str:
        if not content:
            return ""

        cleaned = re.sub(r"<[^>]+>", " ", content)
        cleaned = cleaned.replace("\x00", " ")

        lines = []
        for line in cleaned.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if INJECTION_PATTERN.search(stripped):
                continue
            lines.append(stripped)

        cleaned = "\n".join(lines)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned

    def _freshness_score(self, metadata: Dict) -> float:
        raw_date = metadata.get("published") or metadata.get("date") or metadata.get("published_date")
        if not raw_date:
            return 0.0
        try:
            if isinstance(raw_date, (int, float)):
                published = datetime.fromtimestamp(raw_date, tz=timezone.utc)
            else:
                published = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
            age_days = max(0.0, (datetime.now(tz=timezone.utc) - published).total_seconds() / 86400)
            decay = max(0.0, 1.0 - (age_days / 30.0))
            return decay
        except Exception:
            return 0.0

    def search(self, query: str, k=3, use_web: bool = True) -> List[Dict]:
        """
        Performs Hybrid Search:
        1. BM25 (Keyword)
        2. Vector Search (Semantic) - Mocked
        3. Tavily Web Search (if enabled)
        4. Boost trusted domains
        """
        results = []
        if use_web:
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

        # Apply freshness score
        for res in results:
            metadata = res.get("metadata", {})
            freshness = self._freshness_score(metadata)
            if "scores" in metadata:
                metadata["scores"]["freshness"] = round(freshness, 3)
                metadata["scores"]["combined"] = metadata["scores"].get("combined", 0) + (self.freshness_weight * freshness)
        
        # Sort by combined score (highest first)
        results.sort(key=lambda x: x.get("metadata", {}).get("scores", {}).get("combined", 0), reverse=True)

        # Optional reranker on top-k
        if self._reranker and results:
            top_k = max(1, min(len(results), self.reranker_top_k))
            rerank_candidates = results[:top_k]
            try:
                pairs = [(query, item.get("content", "")) for item in rerank_candidates]
                scores = self._reranker.predict(pairs)
                for item, score in zip(rerank_candidates, scores):
                    metadata = item.get("metadata", {})
                    metadata.setdefault("scores", {})
                    metadata["scores"]["rerank"] = float(round(score, 3))
                    metadata["scores"]["combined"] = metadata["scores"].get("combined", 0) + float(score)
                results.sort(key=lambda x: x.get("metadata", {}).get("scores", {}).get("combined", 0), reverse=True)
            except Exception:
                pass
        
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

        if time.time() < self._web_circuit_until:
            print("Warning: web search circuit open, skipping.")
            return []

        if "TAVILY_API_KEY" not in os.environ:
            print("Warning: TAVILY_API_KEY not set, web search disabled")
            return []

        results = []
        try:
            from tavily import TavilyClient

            tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
            # Enhanced search with advanced depth for better results
            search_kwargs = {
                "query": query,
                "max_results": 5,
                "search_depth": "advanced",
                "exclude_domains": self.excluded_domains,
                "include_answer": True,
                "timeout": self.web_timeout_seconds,
            }
            try:
                web_res = tavily.search(**search_kwargs)
            except TypeError:
                search_kwargs.pop("timeout", None)
                web_res = tavily.search(**search_kwargs)
            
            # If Tavily provides a direct answer, include it first
            if web_res.get("answer"):
                summary = self._sanitize_web_content(web_res.get("answer", ""))
                if summary:
                    results.append({
                        "content": f"[WEB SUMMARY] {summary}",
                        "metadata": {
                            "source": "Tavily AI Summary",
                            "parent_id": "web_summary",
                            "source_type": "web_summary",
                            "scores": {"combined": 2.0}  # High priority
                        }
                    })
            
            for res in web_res.get("results", []):
                # Use raw_content if available for more context
                content = res.get("raw_content", res.get("content", ""))
                if content:
                    content = self._sanitize_web_content(content)
                    if not content:
                        continue
                    # Limit content length to avoid token overflow
                    content = content[:1500] if len(content) > 1500 else content
                    results.append({
                        "content": f"[WEB] {content}",
                        "metadata": {
                            "source": res.get("url", "unknown"), 
                            "title": res.get("title", ""),
                            "parent_id": "web",
                            "source_type": "web",
                            "scores": {"combined": 1.0}
                        },
                    })
            self._web_failure_count = 0
        except Exception as e:
            print(f"Tavily Error: {e}")
            self._web_failure_count += 1
            if self._web_failure_count >= self.web_failure_threshold:
                self._web_circuit_until = time.time() + self.web_cooldown_seconds
                self._web_failure_count = 0
        
        print(f"Web search returned {len(results)} results")
        return results
