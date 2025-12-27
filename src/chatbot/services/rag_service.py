from typing import List, Dict, Optional, Any
import logging
from ..rag.retriever import HybridRetriever

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
            docs=[], # Docs can be loaded dynamically or passed here if needed
            trusted_domains=trusted_domains,
            excluded_domains=excluded_domains
        )
        self.logger.info("RAGService initialized.")

    def search(self, query: str, k: int = 5) -> str:
        """
        Perform a hybrid search (Vector + Keyword + Web).
        
        Args:
            query: The user's search query.
            k: Number of results to return.
            
        Returns:
            Formatted context string.
        """
        return self.retriever.retrieve(query, k=k)

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
