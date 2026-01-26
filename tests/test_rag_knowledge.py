
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use local Malaya LLM path
sys.path.append(os.getcwd())

from src.chatbot.services.rag_service import RAGService

def test_rag():
    print("Testing RAG Knowledge Base...")
    
    config = {
        "rag": {
            "trusted_domains": ["gov.my"],
            "excluded_domains": []
        }
    }
    
    rag = RAGService(config)
    
    # Test Queries
    queries = [
        "Sekolah Menengah Kebangsaan",
        "Hospital Kuala Lumpur",
        "Parlimen Malaysia",
        "George Town"
    ]
    
    for q in queries:
        print(f"\nQuery: {q}")
    for q in queries:
        print(f"\nQuery: {q}")
        result_str = rag.search(q, k=3)
        print(result_str)
            
    # Check if we actually loaded documents
            
    # Check if we actually loaded documents
    total_docs = len(rag.retriever.docs)
    print(f"\nTotal Indexed Documents: {total_docs}")
    if total_docs > 1000:
        print("✅ RAG Knowledge Base Loaded Successfully!")
    else:
        print("❌ Warning: Low document count. Extraction might have failed.")

if __name__ == "__main__":
    test_rag()
