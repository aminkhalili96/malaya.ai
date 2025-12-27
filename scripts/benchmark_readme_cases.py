
import asyncio
import sys
import os
import json
from pathlib import Path

# Add root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.chatbot.engine import MalayaChatbot

async def process_single(bot, query, timeout=120):
    try:
        # Enforce timeout to prevent hanging
        result = await asyncio.wait_for(bot.process_query(query), timeout=timeout)
        return result.get("answer", "")
    except asyncio.TimeoutError:
        return "Error: Timeout (120s)"
    except Exception as e:
        return f"Error: {e}"

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
    # Clear old logs
    with open(report_path, "w") as f:
        pass

    print(f"\nSTARTING BENCHMARK. Logs streaming to {report_path}")
    print(f"{'#':<3} | {'Input (Truncated)':<40} | {'Status'}")
    print("-" * 60)

    results = []

    for i, case in enumerate(cases):
        query = case["input"]
        
        # Raw run
        ans_raw = await process_single(bot_raw, query)
        
        # Malaya run
        ans_malaya = await process_single(bot_malaya, query)
        
        result_entry = {
            "id": case["id"],
            "category": case["category"],
            "input": query,
            "raw_output": ans_raw,
            "malaya_output": ans_malaya
        }
        results.append(result_entry)
        
        # Incremental Save
        with open(report_path, "a") as f:
            f.write(json.dumps(result_entry) + "\n")
            
        print(f"{case['id']:<3} | {query[:40]:<40} | ✅ Done")
        # Small sleep to yield loop
        await asyncio.sleep(0.1)

    # Final Summary Save (JSON)
    final_path = ROOT / "reports/benchmark_100_cases_final.json"
    with open(final_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n🎉 Benchmark Complete. Full JSON saved to {final_path}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
