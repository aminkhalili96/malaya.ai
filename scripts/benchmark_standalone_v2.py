
import json
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

# Import v2 Services directly (bypassing engine/langchain)
try:
    from src.chatbot.services.malaya_service import MalayaService
    from src.rag.vector_service import VectorRAGService
    from src.chatbot.services.user_memory_service import UserMemoryService
    import ollama
    print("✅ Services and Ollama imported successfully")
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

# Configuration
MODEL_NAME = "qwen2.5:7b"
LOG_FILE = ROOT_DIR / "benchmark-tracker/logs" / f"v2_benchmark_standalone_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
CASES_FILE = ROOT_DIR / "tests/fixtures/expanded_cases.json"

# Ensure log dir exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

class StandaloneV2Pipeline:
    def __init__(self):
        self.malaya = MalayaService()
        self.vector = VectorRAGService()
        self.memory = UserMemoryService()
        
        # Initialize (Mock mode will trigger if env var is set)
        # MalayaService initializes in __init__
        # self.malaya._ensure_initialized()
        self.vector._ensure_initialized()
        
        # System Prompt (from config)
        self.system_prompt = """You are Malaya.ai, a Sovereign AI Copilot for Malaysia.
You understand Malaysian languages, dialects (Kelantanese, Terengganu, Sabahan, Sarawakian), and particles (lah, meh, lor).
STRICT RULES:
1. If user speaks Malay -> Reply in Malay.
2. If user speaks English -> Reply in English.
3. If user speaks Manglish -> Reply in Manglish.
4. Use Malaysian lexicon context if provided.
5. Be helpful, concise, and friendly.
"""

    def process_query(self, user_input: str, user_id: str = "test_user") -> str:
        t0 = time.time()
        
        # 1. Normalize
        normalized = self.malaya.normalize_text(user_input)
        
        # 2. Toxicity
        is_toxic, score, category = self.malaya.check_toxicity(normalized)
        if is_toxic:
            return f"I cannot answer that. (Toxic content detected: {category})"
            
        # 3. Vector RAG Context
        lexicon_context = self.vector.get_context_for_query(normalized)
        
        # 4. User Memory
        user_context = self.memory.get_user_context(user_id)
        
        # 5. Build Final Prompt
        context_str = ""
        if lexicon_context:
            context_str += f"{lexicon_context}\n\n"
        if user_context:
            context_str += f"[User Memory]\n{user_context}\n\n"
            
        full_prompt = f"{self.system_prompt}\n\nContext:\n{context_str}\nUser: {normalized}"
        
        # 6. Generate with Ollama
        try:
            response = ollama.chat(model=MODEL_NAME, messages=[
                {'role': 'user', 'content': full_prompt}
            ])
            content = response['message']['content']
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return "Error generating response."
            
        # 7. Polish Output
        polished = self.malaya.polish_output(content)
        
        t1 = time.time()
        logger.info(f"Processed in {t1-t0:.2f}s")
        return polished

def run_benchmark():
    print(f"🚀 Starting Standalone V2 Benchmark using {MODEL_NAME}")
    print(f"📝 Logging to: {LOG_FILE}")
    
    # Load cases
    if not CASES_FILE.exists():
        print(f"❌ Cases file not found: {CASES_FILE}")
        return

    with open(CASES_FILE, 'r') as f:
        data = json.load(f)
        cases = data if isinstance(data, list) else data.get("test_cases", [])

    pipeline = StandaloneV2Pipeline()
    results = []
    
    with open(LOG_FILE, 'w') as log:
        log.write(f"Benchmark Start: {datetime.now()}\n")
        log.write(f"Model: {MODEL_NAME}\n")
        log.write("-" * 80 + "\n")
        
        for i, case in enumerate(cases):
            q_id = case.get("id", i)
            category = case.get("category", "general")
            query = case.get("input", "")
            expected = case.get("expected_keywords", [])
            
            print(f"Running [{i+1}/{len(cases)}] {category}: {query[:50]}...")
            
            # Run Pipeline
            response = pipeline.process_query(query)
            
            # Evaluate
            passed_keywords = [k for k in expected if k.lower() in response.lower()]
            score = len(passed_keywords) / len(expected) if expected else 1.0
            passed = score >= 0.5 # Simple threshold
            
            # Log
            log_entry = (
                f"\nCase ID: {q_id}\n"
                f"Category: {category}\n"
                f"Input: {query}\n"
                f"Response: {response}\n"
                f"Expected: {expected}\n"
                f"Score: {score:.2f} ({'PASS' if passed else 'FAIL'})\n"
                f"{'-'*40}\n"
            )
            log.write(log_entry)
            print(f"  -> Score: {score:.2f}")
            
            results.append({
                "id": q_id,
                "category": category,
                "score": score,
                "passed": passed
            })
            
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    avg_score = sum(r['score'] for r in results) / total if total else 0
    
    print("\n" + "="*40)
    print("BENCHMARK COMPLETION REPORT")
    print("="*40)
    print(f"Total Cases: {total}")
    print(f"Passed: {passed}")
    print(f"Accuracy: {(passed/total)*100:.1f}%")
    print(f"Avg Score: {avg_score:.2f}")
    print("="*40)

if __name__ == "__main__":
    # Force mock if needed, but try real first? 
    # Let's trust the env var if user set it, otherwise defaults.
    # We set MALAYA_FORCE_MOCK=1 in runner unless we want to try real loading.
    run_benchmark()
