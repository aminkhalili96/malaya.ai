import json
import time
import subprocess
import os
import threading
import queue
from pathlib import Path
import ollama

# Configuration - 4 untested text-focused models (smallest to largest)
MODELS_TO_BENCHMARK = [
    "llama3.2:3b",
    "phi3:14b",
    "deepseek-coder-v2:16b",
    "qwen3:32b",
]

ROOT_DIR = Path(__file__).parent.parent
CASES_PATH = ROOT_DIR / "tests" / "fixtures" / "expanded_cases.json"
REPORTS_DIR = ROOT_DIR / "reports"
BASELINE_REPORT_PATH = REPORTS_DIR / "benchmark_baseline.md"

# Signals
download_queue = queue.Queue()
ready_queue = queue.Queue()

def load_cases():
    with open(CASES_PATH, "r") as f:
        return json.load(f)

def update_markdown_report_table(model_name, total_cases, total_score, accuracy):
    """
    Parses the baseline report and updates the Executive Summary table
    with the new benchmark result.
    """
    if not BASELINE_REPORT_PATH.exists():
        print(f"⚠️ Report file not found at {BASELINE_REPORT_PATH}")
        return

    # Create the markdown row
    # | Model | Valid Cases | Score | Accuracy |
    entry_line = f"| **{model_name}** | {total_cases} | {total_score} | **{accuracy:.1f}%** |"
    
    with open(BASELINE_REPORT_PATH, "r") as f:
        lines = f.readlines()

    # Find the "Executive Summary" table header
    table_start_index = -1
    insertion_index = -1
    header_found = False
    
    for i, line in enumerate(lines):
        if "| Model | Valid Cases | Score | Accuracy |" in line:
            table_start_index = i
            header_found = True
        
        # Look for end of table (after header)
        if header_found and i > table_start_index + 1:
            if not line.strip().startswith("|"):
                insertion_index = i
                break
    
    # Handle case where table is at EOF
    if header_found and insertion_index == -1:
        insertion_index = len(lines)

    if header_found:
        # Check for existing entry to avoid duplicates
        updated = False
        for j in range(table_start_index, insertion_index):
            if f"**{model_name}**" in lines[j] or f" {model_name} " in lines[j]:
                lines[j] = entry_line + "\n"
                print(f"📝 Updated existing entry in report for {model_name}")
                updated = True
                break
        
        if not updated:
            lines.insert(insertion_index, entry_line + "\n")
            print(f"📝 Added new entry to report for {model_name}")
            
        with open(BASELINE_REPORT_PATH, "w") as f:
            f.writelines(lines)
    else:
         print("⚠️ Could not find 'Executive Summary' table in report to update.")

def pull_model(model_name):
    print(f"\n⬇️  [Downloader] Starts pulling {model_name}...")
    start = time.time()
    try:
        # Check if exists (fast check)
        check = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model_name in check.stdout:
             print(f"\n✅ [Downloader] {model_name} already exists. Skipping download.")
             return True

        # Run pull
        subprocess.run(["ollama", "pull", model_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        duration = time.time() - start
        print(f"\n✅ [Downloader] {model_name} Ready! (Took {duration:.1f}s)")
        return True
    except Exception as e:
        print(f"\n❌ [Downloader] Failed to pull {model_name}: {e}")
        return False

def remove_model(model_name):
    print(f"\n🗑️  [Cleaner] Removing {model_name}...")
    try:
        subprocess.run(["ollama", "rm", model_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass 

def score_response(response_text, expected_keywords, negative_keywords):
    response_lower = response_text.lower()
    for neg in negative_keywords:
        if neg.lower() in response_lower: return 0
    for keyword in expected_keywords:
        if keyword.lower() in response_lower: return 1
    return 0

def run_benchmark(model_name, cases):
    print(f"\n🚀 [Runner] Benchmarking {model_name}...")
    results = []
    total_score = 0
    start_time = time.time()
    
    REPORTS_DIR.mkdir(exist_ok=True)
    report_file = REPORTS_DIR / f"benchmark_competitor_{model_name.replace(':', '_').replace('/', '_')}.jsonl"

    for i, case in enumerate(cases):
        try:
            resp = ollama.chat(model=model_name, messages=[{'role': 'user', 'content': case["input"]}])
            output = resp['message']['content']
            score = score_response(output, case["expected_keywords"], case["negative_keywords"])
            total_score += score
            
            entry = {
                "id": case["id"], "model": model_name, 
                "score": score, "output": output, "category": case.get("category", "General")
            }
            results.append(entry)
            with open(report_file, "a") as f: f.write(json.dumps(entry) + "\n")
            
            if i % 10 == 0: print(f"   [Runner] {model_name}: {i}/{len(cases)} cases...", end="\r")

        except Exception as e:
            print(f"   [Runner] Error: {e}")

    total_time = time.time() - start_time
    acc = (total_score / len(cases)) * 100
    print(f"\n🏁 [Runner] Finished {model_name}! Accuracy: {acc}% Time: {total_time:.1f}s")
    
    # Save JSON Summary
    summary = {"model": model_name, "accuracy": acc, "time": total_time}
    with open(REPORTS_DIR / f"summary_{model_name.replace(':', '_').replace('/', '_')}.json", "w") as f:
        json.dump(summary, f, indent=4)

    # Update Markdown Doc
    update_markdown_report_table(model_name, len(cases), total_score, acc)

def download_worker():
    while True:
        model = download_queue.get()
        if model is None: 
            ready_queue.put(None)
            break
        
        success = pull_model(model)
        if success:
            ready_queue.put(model)
        else:
            print(f"⚠️ Skipping {model} due to download failure.")
        
        download_queue.task_done()

def main():
    cases = load_cases()
    print(f"🔥 Starting Pipelined Benchmark for {len(MODELS_TO_BENCHMARK)} models...")
    print("   (Results will be auto-saved to reports/benchmark_baseline.md)")
    
    downloader = threading.Thread(target=download_worker, daemon=True)
    downloader.start()
    
    for m in MODELS_TO_BENCHMARK:
        download_queue.put(m)
    download_queue.put(None)
    
    processed_count = 0
    while processed_count < len(MODELS_TO_BENCHMARK):
        print("\n⏳ [Main] Waiting for next model to be ready...")
        model = ready_queue.get()
        
        if model is None: 
            break
            
        run_benchmark(model, cases)
        remove_model(model)
        
        processed_count += 1
        
    downloader.join()
    print("\n✨ ALL DONE! ✨")

if __name__ == "__main__":
    main()
