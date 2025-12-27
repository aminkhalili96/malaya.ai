import re
import uuid
from typing import List, Dict, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Presidio can be heavy to initialize and requires its spaCy model; fall back gracefully if unavailable
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
except Exception:
    AnalyzerEngine = None
    AnonymizerEngine = None

class PIIRedactor:
    def __init__(self):
        self.available = False
        self._init_error = None
        if AnalyzerEngine and AnonymizerEngine:
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                self.available = True
            except Exception as exc:
                # Keep running with regex fallback if Presidio fails to boot (e.g., missing spaCy model)
                self._init_error = exc

    def redact(self, text: str) -> str:
        """
        Redacts PII from text using Microsoft Presidio.
        Falls back to lightweight regex masking when Presidio is unavailable.
        """
        if self.available:
            try:
                results = self.analyzer.analyze(
                    text=text,
                    entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "PERSON"],
                    language="en",
                )
                anonymized_result = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=results,
                )
                return anonymized_result.text
            except Exception as exc:
                # Fall back instead of breaking ingestion
                self._init_error = self._init_error or exc

        return self._regex_redact(text)

    def _regex_redact(self, text: str) -> str:
        """Simple fallback masking for email, phone numbers, and capitalized names."""
        redacted = re.sub(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            "[EMAIL]",
            text,
        )
        redacted = re.sub(
            r"\+?\d[\d\-\s]{7,}\d",
            "[PHONE]",
            redacted,
        )
        redacted = re.sub(
            r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b",
            "[PERSON]",
            redacted,
        )
        return redacted

class ParentChildIndexer:
    def __init__(self, parent_chunk_size=2000, child_chunk_size=400):
        self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=parent_chunk_size, chunk_overlap=200)
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=child_chunk_size, chunk_overlap=50)
        self.redactor = PIIRedactor()
        self.store = {} # Mock store: {doc_id: parent_content}

    def process_document(self, text: str) -> Tuple[List[Dict], Dict[str, str]]:
        """
        1. Redact PII
        2. Split into Parents
        3. Split Parents into Children
        4. Return child chunks with Parent ID references and the parent store
        """
        # Step 1: Redaction (Defense in Depth)
        clean_text = self.redactor.redact(text)
        
        # Step 2: Parent Splitting
        parents = self.parent_splitter.split_text(clean_text)
        docs_to_index = []
        
        for parent in parents:
            parent_id = str(uuid.uuid4())
            self.store[parent_id] = parent # Store full parent context
            
            # Step 3: Child Splitting
            children = self.child_splitter.split_text(parent)
            for child in children:
                docs_to_index.append({
                    "content": child,
                    "metadata": {"parent_id": parent_id}
                })
                
        return docs_to_index, self.store
