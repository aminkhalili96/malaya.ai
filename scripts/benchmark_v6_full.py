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

# --- V6 Integration: Add project root to path ---
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.rag.retrieval import HybridRetriever
from src.summarization.preprocessing import TextNormalizer
from src.router.intent_classifier import IntentClassifier

# Constants
MODEL_NAME = "qwen2.5:7b"
TEST_CASES_FILE = "tests/fixtures/expanded_cases.json"
OUTPUT_FILE = f"reports/v3_benchmark/v6_full_benchmark_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
DIALECT_FILE = "data/dictionaries/v4_dialects.json"
GENERAL_CONTEXT_FILE = "data/knowledge/general_context.md"
FACTS_FILE = "data/knowledge/v4_facts.json"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT", "180"))
LEXICON_FILE = "data/lexicon_full.json"

OUTPUT_FILE = os.getenv("MALAYA_BENCHMARK_OUTPUT", OUTPUT_FILE)

def load_json(path):
    with open(path, 'r') as f: return json.load(f)

def load_lexicon_map(path):
    if not os.path.exists(path):
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    if not isinstance(data, list):
        return {}
    mapping = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        term = entry.get("term")
        definition = entry.get("definition")
        category = str(entry.get("category", "")).lower()
        if not term or not definition:
            continue
        if category.startswith("stopword") or category.startswith("grammar"):
            continue
        mapping[str(term).lower()] = str(definition).strip()
    return mapping

LEXICON_MAP = load_lexicon_map(LEXICON_FILE)

def load_existing_results(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data.get("results", []) if isinstance(data, dict) else []
    except Exception:
        return []

def save_results(path, results):
    with open(path, 'w') as f:
        json.dump({"model": "Malaya-V6-Full", "results": results}, f, indent=4, ensure_ascii=False)

# --- V6: Initialization (Same as V5) ---
dialect_map = load_json(DIALECT_FILE)
normalizer = TextNormalizer()
classifier = IntentClassifier()

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
    vector_dim=384, 
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

def _extract_candidate_terms(text):
    candidates = []
    quoted = re.findall(r"[\"'“”‘’]([^\"'“”‘’]+)[\"'“”‘’]", text)
    for item in quoted:
        term = item.strip()
        if term:
            candidates.append(term)
    lowered = text.lower()
    if "maksud" in lowered or "meaning" in lowered:
        tokens = re.findall(r"\b\w+\b", lowered)
        for idx, tok in enumerate(tokens):
            if tok in {"maksud", "meaning"} and idx + 1 < len(tokens):
                candidates.append(tokens[idx + 1])
    return list(dict.fromkeys(candidates))

def retrieve_lexicon_context(text):
    if not LEXICON_MAP:
        return None
    candidates = _extract_candidate_terms(text)
    hits = []
    for cand in candidates:
        key = cand.lower()
        if key in LEXICON_MAP:
            hits.append(f"{cand}: {LEXICON_MAP[key]}")
    if not hits:
        tokens = set(re.findall(r"\b\w+\b", text.lower()))
        for token in tokens:
            if token in LEXICON_MAP:
                hits.append(f"{token}: {LEXICON_MAP[token]}")
    if not hits:
        return None
    return "\n".join(hits[:5])

def retrieve_fact(query):
    if classifier.classify(query) == "chat":
        return None
    # Triggers for web search
    use_web = False
    triggers = ["current", "latest", "terkini", "2024", "price", "harga", "result", "keputusan", "winner", "pemenang"]
    if any(t in query.lower() for t in triggers):
        use_web = True
    
    normalized_query = normalizer.normalize_for_retrieval(query)
    results = retriever.search(normalized_query, k=3, use_web=use_web)
    
    if not results:
        return None

    def _filter_results_by_keywords(results_list):
        query_tokens = set(re.findall(r"\b\w+\b", query.lower()))
        filtered = []
        for item in results_list:
            content = item.get("content", "")
            match = re.search(r"Keywords:\s*([^)]+)\)", content, flags=re.IGNORECASE)
            if match:
                keywords = {k.strip().lower() for k in match.group(1).split(",") if k.strip()}
                if query_tokens & keywords:
                    filtered.append(item)
            else:
                filtered.append(item)
        return filtered or results_list

    results = _filter_results_by_keywords(results)
        
    context_str = ""
    for r in results:
        source = r['metadata'].get('source', 'unknown')
        content = r['content']
        context_str += f"[Source: {source}]\n{content}\n\n"
    
    return context_str.strip()

# --- V5: Critic Loop (Preserved) ---
def verify_response(query, response):
    query_lower = query.lower()
    response_lower = response.lower()
    
    if "list" in query_lower or "senarai" in query_lower or "contoh" in query_lower:
        if response.count("\n-") < 3 and response.count("\n1.") < 3 and "," not in response:
             return False, "User asked for a list. Please provide at least 3 distinct examples."
             
    if "cancel" in query_lower or "scam" in query_lower or "report" in query_lower:
        if "help centre" in response_lower and "customer service" not in response_lower:
             return False, "Use 'Customer Service' instead of just 'Help Centre' for better clarity."

    if "maksud" in query_lower or "meaning" in query_lower or "apa itu" in query_lower:
        if not any(t in response_lower for t in ["ungkapan", "slang", "dialek", "maksudnya", "erti"]):
            return False, "Add a short usage tag (e.g., 'ungkapan sakit/terkejut', 'slang remaja')."

    if any(t in query_lower for t in ["xleh", "xbleh", "xde"]) and not any(t in response_lower for t in ["tak boleh", "tidak boleh", "tak ada", "tiada", "cannot", "no money"]):
        return False, "Rewrite using standard Malay shortform expansions like 'tak boleh' / 'tak ada'."

    if "signal" in query_lower and any(t in query_lower for t in ["driver", "kereta", "memandu", "jalan", "lane", "lorry", "moto"]):
        if not any(t in response_lower for t in ["bahaya", "hati-hati", "dangerous"]):
            return False, "Mention that not giving signal is dangerous and advise to be careful."

    if "vs" in query_lower or "beza" in query_lower:
        if "beza" not in response_lower and "percanggahan" not in response_lower and "manakala" not in response_lower:
            return False, "User asked for comparison. Explicitly state the differences."

    return True, "OK"

def generate_v6_full_response(input_text):
    # 1. Retrieve
    fact_context = retrieve_fact(input_text)
    dialect_context = retrieve_dialect_context(input_text)
    lexicon_context = retrieve_lexicon_context(input_text)
    normalized_query = normalizer.normalize_for_retrieval(input_text)
    safety_context = None
    lower_text = input_text.lower()
    if "signal" in lower_text and any(t in lower_text for t in ["driver", "kereta", "memandu", "jalan", "lane", "lorry", "moto"]):
        safety_context = (
            "Tidak bagi signal semasa memandu itu bahaya. "
            "Nasihatkan agar lebih berhati-hati dan sebutkan 'bahaya' atau 'hati-hati'."
        )
    
    # 2. Prompt Construction
    system_prompt = "You are Malaya-V6 (Full), an advanced Malaysian AI assistant. "
    
    if fact_context:
        system_prompt += f"\n[KNOWLEDGE BASE]\n{fact_context}\n[END KNOWLEDGE BASE]\n"
        system_prompt += (
            "CRITICAL: Answer using [KNOWLEDGE BASE] info. Do not hallucinate. "
            "Include key entities/numbers from the knowledge base when relevant."
        )
    
    if dialect_context:
        system_prompt += f"\n[DIALECT NOTES]\n{dialect_context}\n[END DIALECT NOTES]\n"

    if lexicon_context:
        system_prompt += f"\n[LEXICON]\n{lexicon_context}\n[END LEXICON]\n"

    if safety_context:
        system_prompt += f"\n[SAFETY NOTE]\n{safety_context}\n[END SAFETY NOTE]\n"

    if normalized_query.strip() and normalized_query.strip().lower() != input_text.strip().lower():
        system_prompt += f"\n[NORMALIZED INPUT]\n{normalized_query}\n[END NORMALIZED INPUT]\n"
        
    system_prompt += (
        "\nLanguage: Mirror the user's input. If the input is English-only, answer in English. "
        "Otherwise, answer in natural Malay/Manglish. "
    )
    system_prompt += (
        "First sentence: paraphrase the [NORMALIZED INPUT] in standard Malay "
        "(or English if English-only). "
    )
    system_prompt += (
        "If slang/shortforms appear, add one supportive cue or brief follow-up in the same language. "
        "If the user asks for meaning/maksud, include a short usage tag "
        "(e.g., 'ungkapan sakit/terkejut', 'slang remaja'). "
        "If dialect is detected, append a short standard Malay gloss (e.g., 'Maksudnya: ...'). "
    )
    system_prompt += "FORMATTING: 1. Lists must have 3+ items. 2. Comparisons must be explicit."
    system_prompt += "Do not output analysis or labels like Thoughts/Reasoning."

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
    }, timeout=REQUEST_TIMEOUT_SECONDS).json()
    
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
        }, timeout=REQUEST_TIMEOUT_SECONDS).json()
        return response_v2['message']['content']
        
    return initial_answer

def run_benchmark():
    print(f"Running V6 Benchmark (Full Capability: SFT+RAG+Web)...")
    cases = load_json(TEST_CASES_FILE)
    if not cases: return
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    results = load_existing_results(OUTPUT_FILE)
    completed_ids = {str(r.get("id")) for r in results if isinstance(r, dict)}
    total = len(cases)
    
    for i, case in enumerate(cases):
        if str(case.get("id")) in completed_ids:
            continue
        print(f"[{i+1}/{total}] Case {case['id']}...")
        try:
            response = generate_v6_full_response(case['input'])
            clean_response = re.sub(r'<thought>.*?</thought>', '', response, flags=re.DOTALL).strip()
            
            results.append({
                "id": case['id'],
                "input": case['input'],
                "response": clean_response,
                "raw_response": response,
                "category": case['category']
            })
            save_results(OUTPUT_FILE, results)
        except Exception as e:
            print(f"Error processing case {case['id']}: {e}")
            
    print(f"Done. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_benchmark()
