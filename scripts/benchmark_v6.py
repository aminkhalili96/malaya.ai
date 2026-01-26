import requests
import json
import os
import re
import datetime
import sys
from pathlib import Path

# Project Paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Constants
MODEL_NAME = "qwen2.5:7b"
TEST_CASES_FILE = "tests/fixtures/expanded_cases.json"
OUTPUT_FILE = f"reports/benchmark_competitor_{MODEL_NAME}.jsonl"

def load_json(path):
    with open(path, 'r') as f: return json.load(f)

def generate_response(input_text):
    system_prompt = (
        "You are Malaya AI, a specialized Malaysian Local LLM. "
        "Answer in accurate, natural Malay or Manglish using your training knowledge. "
        "If asked about dialects (Kelantan, Sarawak, Sabah), use your internal knowledge to translate or reply appropriately."
        "\nIMPORTANT: Do not hallucinate. If you don't know, say 'Maaf'."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text}
    ]
    
    try:
        response = requests.post('http://localhost:11434/api/chat', json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 4096}
        }).json()
        return response['message']['content']
    except Exception as e:
        return f"Error: {e}"

def run_benchmark():
    print(f"Running Benchmark on `{MODEL_NAME}` (Pure SFT Mode)...")
    cases = load_json(TEST_CASES_FILE)
    if not cases: return
    
    # Check if exists to avoid overwrite? No, overwrite for clean run.
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        total = len(cases)
        for i, case in enumerate(cases):
            print(f"[{i+1}/{total}] Case {case['id']}...")
            
            raw_response = generate_response(case['input'])
            
            # JSONL Format for Grader
            record = {
                "id": case['id'],
                "input": case['input'],
                "response": raw_response,
                "model": MODEL_NAME
            }
            f.write(json.dumps(record) + "\n")
            f.flush() # Live write
            
    print(f"Done. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_benchmark()
