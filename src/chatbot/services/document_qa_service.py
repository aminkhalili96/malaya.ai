"""
Document Q&A Service
RAG for PDF and DOCX documents.
"""
import os
import tempfile
from typing import Dict, List, Optional
import hashlib

# Document parsing
try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

class DocumentQAService:
    """
    Document Q&A using RAG.
    Supports PDF and DOCX files.
    """
    
    def __init__(self, llm=None):
        self.llm = llm
        self.document_cache: Dict[str, Dict] = {}  # doc_id -> {text, chunks, metadata}
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF."""
        if not PDF_AVAILABLE:
            raise ImportError("pypdf not installed. Run: pip install pypdf")
        
        reader = PdfReader(file_path)
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX."""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not installed. Run: pip install python-docx")
        
        doc = Document(file_path)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        return "\n\n".join(text_parts)
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > chunk_size * 0.5:
                    end = start + last_period + 1
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    async def ingest_document(
        self, 
        file_path: str = None,
        file_bytes: bytes = None,
        filename: str = None
    ) -> Dict:
        """
        Ingest a document for Q&A.
        
        Returns:
            dict with doc_id, page_count, chunk_count
        """
        # Handle bytes input
        if file_bytes and filename:
            suffix = f".{filename.split('.')[-1]}"
            fd, file_path = tempfile.mkstemp(suffix=suffix)
            with os.fdopen(fd, "wb") as f:
                f.write(file_bytes)
        
        if not file_path:
            raise ValueError("Either file_path or (file_bytes, filename) required")
        
        # Generate doc ID
        with open(file_path, "rb") as f:
            doc_id = hashlib.md5(f.read()[:4096]).hexdigest()[:12]
        
        # Extract text based on file type
        ext = file_path.lower().split(".")[-1]
        if ext == "pdf":
            text = self._extract_pdf(file_path)
        elif ext in ["docx", "doc"]:
            text = self._extract_docx(file_path)
        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        # Chunk text
        chunks = self._chunk_text(text)
        
        # Store in cache
        self.document_cache[doc_id] = {
            "text": text,
            "chunks": chunks,
            "metadata": {
                "filename": filename or os.path.basename(file_path),
                "extension": ext,
                "word_count": len(text.split()),
                "chunk_count": len(chunks)
            }
        }
        
        return {
            "doc_id": doc_id,
            "filename": filename or os.path.basename(file_path),
            "word_count": len(text.split()),
            "chunk_count": len(chunks),
            "status": "ingested"
        }
    
    async def query(
        self, 
        doc_id: str, 
        question: str,
        max_chunks: int = 3
    ) -> Dict:
        """
        Query a document with a question.
        """
        if doc_id not in self.document_cache:
            return {"error": "Document not found. Please upload first."}
        
        doc = self.document_cache[doc_id]
        chunks = doc["chunks"]
        
        # Simple keyword-based retrieval (in production, use embeddings)
        question_words = set(question.lower().split())
        scored_chunks = []
        
        for i, chunk in enumerate(chunks):
            chunk_words = set(chunk.lower().split())
            overlap = len(question_words.intersection(chunk_words))
            scored_chunks.append((overlap, i, chunk))
        
        scored_chunks.sort(reverse=True)
        top_chunks = [c[2] for c in scored_chunks[:max_chunks]]
        
        # Build context
        context = "\n\n---\n\n".join(top_chunks)
        
        # Generate answer
        if self.llm:
            prompt = f"""Answer the question based on the document context below.
If the answer is not in the context, say "I couldn't find this in the document."

Context:
{context}

Question: {question}

Answer:"""
            
            response = await self.llm.ainvoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
        else:
            answer = f"Found {len(top_chunks)} relevant sections. Please configure LLM for full Q&A."
        
        return {
            "doc_id": doc_id,
            "question": question,
            "answer": answer,
            "sources": [c[:200] + "..." for c in top_chunks],
            "source_count": len(top_chunks)
        }
    
    def list_documents(self) -> List[Dict]:
        """List all ingested documents."""
        return [
            {"doc_id": doc_id, **doc["metadata"]}
            for doc_id, doc in self.document_cache.items()
        ]
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from cache."""
        if doc_id in self.document_cache:
            del self.document_cache[doc_id]
            return True
        return False


# Global instance
document_qa = DocumentQAService()
