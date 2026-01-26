import requests
import json
import os
import re
import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env immediately
load_dotenv()

# --- V5 Integration: Add project root to path ---
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.rag.retrieval import HybridRetriever
from src.summarization.preprocessing import TextNormalizer
from src.router.intent_classifier import IntentClassifier

# Constants
MODEL_NAME = "qwen2.5:7b"
TEST_CASES_FILE = "tests/fixtures/expanded_cases.json"
OUTPUT_FILE = f"reports/v3_benchmark/v5_benchmark_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
DIALECT_FILE = "data/dictionaries/v4_dialects.json"
GENERAL_CONTEXT_FILE = "data/knowledge/general_context.md"
FACTS_FILE = "data/knowledge/v4_facts.json"

def load_json(path):
    with open(path, 'r') as f: return json.load(f)

# --- V5: Initialization ---
# Load Dialects
dialect_map = load_json(DIALECT_FILE)
normalizer = TextNormalizer()
classifier = IntentClassifier()

# Load & Chunk General Context
try:
    with open(GENERAL_CONTEXT_FILE, "r") as f:
        general_context_text = f.read()
    
    chunks = []
    current_chunk = []
    for line in general_context_text.split('\n'):
        if line.startswith("## "):
            if current_chunk:
                chunks.append({"content": "\n".join(current_chunk), "metadata": {"source": "general_context.md"}})
            current_chunk = [line]
        else:
            current_chunk.append(line)
    if current_chunk:
        chunks.append({"content": "\n".join(current_chunk), "metadata": {"source": "general_context.md"}})
        
    print(f"Loaded {len(chunks)} context chunks.")
    
except Exception as e:
    print(f"Warning: Could not load general context: {e}")
    chunks = []

# Load Fact Snippets
try:
    facts = load_json(FACTS_FILE)
    for item in facts:
        fact_text = item.get("fact")
        keywords = item.get("keywords", [])
        if fact_text:
            chunks.append({
                "content": f"{fact_text} (Keywords: {', '.join(keywords)})",
                "metadata": {"source": "v4_facts.json"},
            })
except Exception as e:
    print(f"Warning: Could not load facts: {e}")

# Initialize Production Retriever (With Web Search)
retriever = HybridRetriever(
    docs=chunks,
    vector_dim=384, # Default for MiniLM
    reranker_enabled=False, 
    web_timeout_seconds=5.0
)

def retrieve_dialect_context(text):
    text_lower = text.lower()
    matches = []
    
    def add_match(term, dialect, mapping):
        if term in text_lower:
            clean = str(mapping).split('(')[0].strip()
            matches.append(f"{term} ({dialect}): {clean}")

    if "dialects" in dialect_map:
        for dialect, data in dialect_map["dialects"].items():
            terms = data.get("keywords", {}) if isinstance(data, dict) else {}
            for term, mapping in terms.items():
                add_match(term, dialect, mapping)
    else:
        for dialect, terms in dialect_map.items():
            if not isinstance(terms, dict):
                continue
            for term, mapping in terms.items():
                add_match(term, dialect, mapping)
    
    return "\n".join(matches) if matches else None

def retrieve_fact(query):
    if classifier.classify(query) == "chat":
        return None
    # V5 Logic: Hybrid + Web
    # Check triggers for web search
    use_web = False
    triggers = ["current", "latest", "terkini", "2024", "price", "harga", "result", "keputusan", "winner", "pemenang"]
    if any(t in query.lower() for t in triggers):
        use_web = True
    
    normalized_query = normalizer.normalize_for_retrieval(query)
    # Perform Search
    # Note: HybridRetriever requires TAVILY_API_KEY in env for web search
    results = retriever.search(normalized_query, k=3, use_web=use_web)
    
    if not results:
        return None
        
    context_str = ""
    for r in results:
        source = r['metadata'].get('source', 'unknown')
        content = r['content']
        context_str += f"[Source: {source}]\n{content}\n\n"
    
    return context_str.strip()

# --- V5: Critic Loop ---
def verify_response(query, response):
    query_lower = query.lower()
    response_lower = response.lower()
    
    # Rule 1: Lists
    if "list" in query_lower or "senarai" in query_lower or "contoh" in query_lower:
        if response.count("\n-") < 3 and response.count("\n1.") < 3 and "," not in response:
             return False, "User asked for a list. Please provide at least 3 distinct examples."
             
    # Rule 2: Synonyms (Help Centre -> Customer Service)
    if "cancel" in query_lower or "scam" in query_lower or "report" in query_lower:
        if "help centre" in response_lower and "customer service" not in response_lower:
             return False, "Use 'Customer Service' instead of just 'Help Centre' for better clarity."

    # Rule 3: Comparisons
    if "vs" in query_lower or "beza" in query_lower:
        if "beza" not in response_lower and "percanggahan" not in response_lower and "manakala" not in response_lower:
            return False, "User asked for comparison. Explicitly state the differences."

    return True, "OK"

def generate_v5_response(input_text):
    # 1. Retrieve
    fact_context = retrieve_fact(input_text)
    dialect_context = retrieve_dialect_context(input_text)
    
    # 2. Prompt Construction
    system_prompt = "You are Malaya-V5, an advanced Malaysian AI assistant. "
    
    if fact_context:
        system_prompt += f"\n[KNOWLEDGE BASE]\n{fact_context}\n[END KNOWLEDGE BASE]\n"
        system_prompt += "CRITICAL: Answer using [KNOWLEDGE BASE] info. Do not hallucinate."
    
    if dialect_context:
        system_prompt += f"\n[DIALECT NOTES]\n{dialect_context}\n[END DIALECT NOTES]\n"
        
    system_prompt += "\nAnswer in natural Malay/Manglish. "
    system_prompt += "FORMATTING: 1. Lists must have 3+ items. 2. Comparisons must be explicit."
    system_prompt += "Use <thought> tags to plan."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text}
    ]
    
    # 3. Generate
    response = requests.post('http://localhost:11434/api/chat', json={
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096}
    }).json()
    
    initial_answer = response['message']['content']
    
    # 4. Critic Loop
    is_valid, critique = verify_response(input_text, initial_answer)
    if not is_valid:
        print(f"   [Correcting] {critique}")
        messages.append({"role": "assistant", "content": initial_answer})
        messages.append({"role": "user", "content": f"Correction: {critique}. Rewrite answer."})
        
        response_v2 = requests.post('http://localhost:11434/api/chat', json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1}
        }).json()
        return response_v2['message']['content']
        
    return initial_answer

def run_benchmark():
    print(f"Running V5 Benchmark (Agnt+RAG+Web)...")
    cases = load_json(TEST_CASES_FILE)
    if not cases: return
    
    results = []
    total = len(cases)
    
    # Ensure output dir exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    for i, case in enumerate(cases):
        print(f"[{i+1}/{total}] Case {case['id']}...")
        try:
            response = generate_v5_response(case['input'])
            clean_response = re.sub(r'<thought>.*?</thought>', '', response, flags=re.DOTALL).strip()
            
            results.append({
                "id": case['id'],
                "input": case['input'],
                "response": clean_response,
                "raw_response": response,
                "category": case['category']
            })
        except Exception as e:
            print(f"Error processing case {case['id']}: {e}")
            
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({"model": "Malaya-V5", "results": results}, f, indent=4, ensure_ascii=False)
    print(f"Done. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_benchmark()
