
import asyncio
import sys
import os
import json
from pathlib import Path

# Add root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.chatbot.engine import MalayaChatbot


def score_response(response, expected_keywords, negative_keywords):
    if not response or response.startswith("Error"):
        return 0
    
    response_lower = response.lower()
    
    # Negative check (Automatic Fail)
    for kw in negative_keywords:
        if kw.lower() in response_lower:
            return 0
            
    # Positive check (At least one must match)
    # If no expected keywords provided, treat as 1 (Manual check needed, but default pass for now if valid answer)
    if not expected_keywords:
        return 1
        
    for kw in expected_keywords:
        if kw.lower() in response_lower:
            return 1
            
    return 0

async def process_single(bot, query, expected_keywords, negative_keywords, timeout=600):
    try:
        # Enforce timeout to prevent hanging (increased to 600s for slow CPU)
        result = await asyncio.wait_for(bot.process_query(query), timeout=timeout)
        answer = result.get("answer", "")
        score = score_response(answer, expected_keywords, negative_keywords)
        return answer, score
    except asyncio.TimeoutError:
        return f"Error: Timeout ({timeout}s)", 0

    except Exception as e:
        return f"Error: {e}", 0

async def run_benchmark():
    # -----------------------------------------------------------------
    # 🚨 COST SAFETY CHECK
    # -----------------------------------------------------------------
    if "OPENAI_API_KEY" in os.environ:
        if os.environ["OPENAI_API_KEY"].strip():
             print("⚠️  OPENAI_API_KEY detected. Disabling it for this benchmark.")
             del os.environ["OPENAI_API_KEY"]

    print("🚀 Running Malaya LLM vs Raw Model Benchmark (100 Cases)")
    print("ℹ️  Mode: STRICTLY LOCAL (Ollama/Qwen) - SEQUENTIAL")
    print("-" * 50)

    # Load 100 cases
    cases_path = ROOT / "tests/fixtures/expanded_cases.json"
    with open(cases_path, "r") as f:
        cases = json.load(f)

    print(f"Loaded {len(cases)} test cases.")

    # 1. Run Raw
    bot_raw = MalayaChatbot()
    # Force Ollama
    if "model" not in bot_raw.config: bot_raw.config["model"] = {}
    bot_raw.config["model"]["provider"] = "ollama"
    bot_raw.config["model"]["name"] = "qwen3:14b"
    if "system_prompts" in bot_raw.config:
        bot_raw.config["system_prompts"]["chatbot"] = "You are a helpful assistant." 
    
    # 2. Run Malaya
    bot_malaya = MalayaChatbot()
    if "model" not in bot_malaya.config: bot_malaya.config["model"] = {}
    bot_malaya.config["model"]["provider"] = "ollama"
    bot_malaya.config["model"]["name"] = "qwen3:14b"

    # Verify provider
    if bot_malaya.config.get("model", {}).get("provider") != "ollama":
        print(f"❌ Aborting: Unexpected provider configuration.")
        return

    # Output file (JSONL for incremental safe keeping)
    report_path = ROOT / "reports/benchmark_100_cases_logs.jsonl"
    
    # RESUME LOGIC: Check for existing entries
    existing_ids = set()
    if report_path.exists():
        print(f"🔄 Found existing log file at {report_path}. Resuming...")
        print(f"🕵️  Checking for TIMEOUTS to retry...")
        with open(report_path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        # ONLY skip if BOTH outputs are valid (no Timeout)
                        r_out = record.get("raw_output", "")
                        m_out = record.get("malaya_output", "")
                        
                        if "Timeout" not in r_out and "Timeout" not in m_out:
                            existing_ids.add(record["id"])
                    except:
                        pass
        print(f"✅ Found {len(existing_ids)} completed (valid) cases. Skipping them.")
    else:
        # Create new if doesn't exist
        with open(report_path, "w") as f:
            pass

    print(f"\nSTARTING BENCHMARK. Logs streaming to {report_path}")
    print(f"{'#':<3} | {'Input (Truncated)':<40} | {'Raw Match?':<10} | {'Malaya Match?'}")
    print("-" * 80)

    results = []
    raw_score_total = 0
    malaya_score_total = 0

    for i, case in enumerate(cases):
        # Skip if done
        if case["id"] in existing_ids:
            continue
            
        query = case["input"]
        exp_kws = case.get("expected_keywords", [])
        neg_kws = case.get("negative_keywords", [])
        
        # Raw run
        ans_raw, score_raw = await process_single(bot_raw, query, exp_kws, neg_kws)
        
        # Malaya run
        ans_malaya, score_malaya = await process_single(bot_malaya, query, exp_kws, neg_kws)
        
        raw_score_total += score_raw
        malaya_score_total += score_malaya
        
        result_entry = {
            "id": case["id"],
            "category": case["category"],
            "input": query,
            "raw_output": ans_raw,
            "raw_score": score_raw,
            "malaya_output": ans_malaya,
            "malaya_score": score_malaya
        }
        results.append(result_entry)
        
        # Incremental Save
        with open(report_path, "a") as f:
            f.write(json.dumps(result_entry) + "\n")
            
        print(f"{case['id']:<3} | {query[:40]:<40} | {score_raw:<10} | {score_malaya}")
        # Small sleep to yield loop
        await asyncio.sleep(0.1)

    # FINAL REPORT GENERATION (Merge existing logs + new results)
    final_results = []
    r_score = 0
    m_score = 0
    
    # Re-read full log to get complete dataset for final JSON
    with open(report_path, "r") as f:
         for line in f:
            if line.strip():
                try:
                    d = json.loads(line)
                    final_results.append(d)
                    r_score += d.get("raw_score", 0)
                    m_score += d.get("malaya_score", 0)
                except:
                    pass

    # Final Summary Save (JSON)
    final_path = ROOT / "reports/benchmark_100_cases_final.json"
    total_c = len(final_results) if final_results else 1
    summary = {
        "total_cases": total_c,
        "raw_accuracy": r_score / total_c,
        "malaya_accuracy": m_score / total_c,
        "details": final_results
    }
    with open(final_path, "w") as f:
        json.dump(summary, f, indent=2)

    
    print(f"\n🎉 Benchmark Complete.")
    print(f"Raw Accuracy: {raw_score_total}/{len(cases)} ({summary['raw_accuracy']:.1%})")
    print(f"Malaya Accuracy: {malaya_score_total}/{len(cases)} ({summary['malaya_accuracy']:.1%})")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
