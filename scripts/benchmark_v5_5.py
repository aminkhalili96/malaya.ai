
import json
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.preprocessor.dialect_adapter import DialectAdapter
from src.router.intent_classifier import IntentClassifier
from src.rag.retrieval import HybridRetriever
from typing import List, Dict
import requests

# CONSTANTS
MODEL_NAME = "qwen2.5:7b"
FACTS_PATH = "data/knowledge/v4_facts.json"
CASES_PATH = "tests/fixtures/expanded_cases.json"
OLLAMA_API = "http://localhost:11434/api/generate"

def query_ollama(prompt, context=None, system_prompt=None):
    if system_prompt is None:
        system_prompt = "You are a helpful Malaysian AI assistant. Answer in Malay. Keep it concise."
    
    full_prompt = f"{system_prompt}\n\n"
    if context:
        full_prompt += f"[CONTEXT]:\n{context}\n\n"
    
    full_prompt += f"[USER]: {prompt}\n[ASSISTANT]:"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9
        }
    }
    
    try:
        response = requests.post(OLLAMA_API, json=payload)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"[Error] Ollama failed: {e}"

def main():
    print(f"🚀 Starting Benchmark V5.5 (Agentic Refinement)...")
    
    # 1. Initialize Components
    adapter = DialectAdapter()
    classifier = IntentClassifier()
    
    # Load Facts and convert to Documents
    with open(FACTS_PATH, 'r') as f:
        raw_facts = json.load(f)
    
    docs = []
    for item in raw_facts:
        # Create a searchable content string: "Fact content. Keywords: k1, k2"
        content = f"{item['fact']} (Keywords: {', '.join(item['keywords'])})"
        docs.append({
            "content": content,
            "metadata": {"source": "local_facts"}
        })
        
    retriever = HybridRetriever(docs)
    
    # 2. Load Cases
    with open(CASES_PATH, 'r') as f:
        cases = json.load(f)
    print(f"📝 Loaded {len(cases)} test cases.")

    results = []
    
    # 3. Run Pipeline
    for i, case in enumerate(cases):
        case_id = case['id']
        original_input = case['input']
        
        print(f"[{i+1}/{len(cases)}] Case {case_id}: {original_input}")
        
        # Step A: Pre-processing (Dialect Adapter)
        # "bakpo mung dop mari" -> "kenapa kamu tidak datang"
        processed_input = adapter.translate(original_input)
        
        # Step B: Intent Classification
        intent = classifier.classify(processed_input)
        
        # Step C: Selective RAG
        context = ""
        context_source = "None"
        
        if intent == "fact":
            # Only run RAG if it's a factual query
            # search returns List[Dict] with 'content' and 'metadata'
            retrieved_items = retriever.search(processed_input, k=3, use_web=True) 
            if retrieved_items:
                context = "\n".join([f"- {item.get('content', '')}" for item in retrieved_items])
                context_source = "HybridRAG"
        else:
            # Skip RAG for chit-chat / slang to prevent poisoning
            context_source = "Skipped (Chit-Chat)"
            
        # Step D: Generation
        # We pass the PROCESSED input to the LLM (it understands standard Malay better)
        # unless it's pure creative writing, but usually standard > dialect for 7B.
        system_instruct = """
You are a helpful Malaysian AI. 
- Answer in Malay.
- If context is provided, USE IT.
- If context is empty, use your own knowledge.
- Be polite and concise.
"""
        response = query_ollama(processed_input, context, system_prompt=system_instruct)
        
        # Store Result
        results.append({
            "id": case_id,
            "input": original_input,
            "processed_input": processed_input,
            "intent": intent,
            "context_source": context_source,
            "response": response
        })
        
        print(f"   -> Intent: {intent} | Source: {context_source}")
        # print(f"   -> Response: {response[:50]}...")

    # 4. Save Logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"reports/v3_benchmark/v5_5_benchmark_{timestamp}.json"
    
    with open(output_filename, 'w') as f:
        json.dump({"metadata": {"model": "Malaya V5.5", "strategy": "Selective RAG + Dialect Adapter"}, "results": results}, f, indent=2)
        
    print(f"\n✅ Benchmark Complete. Saved to {output_filename}")

if __name__ == "__main__":
    main()
