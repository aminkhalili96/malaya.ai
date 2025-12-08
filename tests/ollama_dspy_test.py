"""
DSPy Comparison for Local Ollama Models

Tests qwen3:14b and qwen2.5:14b with and without DSPy-enhanced prompts.
Uses 6 quick test cases for fast comparison.
"""

import os
import sys
import json
import requests
from typing import List, Dict
from dataclasses import dataclass

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot.dspy_optimizer import get_enhanced_prompt


# ============================================================
# TEST CASES
# ============================================================

@dataclass
class TestCase:
    id: str
    category: str
    query: str
    expected_understanding: str


QUICK_TEST_CASES = [
    TestCase("short_01", "Shortforms", "xleh la bro, aku xde duit skrg", 
             "Cannot bro, I don't have money right now"),
    TestCase("short_02", "Shortforms", "xtau la bro, aku xphm lgsg", 
             "I don't know bro, I don't understand at all"),
    TestCase("particle_01", "Particles", "best gila siot benda ni!", 
             "This thing is extremely awesome!"),
    TestCase("culture_01", "Cultural", "lepak mamak jom, aku belanja teh tarik", 
             "Let's hang at mamak, I'll treat you to teh tarik"),
    TestCase("manglish_01", "Manglish", "that meeting how ah? client happy tak?", 
             "How was the meeting? Was the client happy?"),
    TestCase("sentiment_01", "Sentiment", "geram betul la dengan service ni", 
             "Really frustrated with this service"),
]


# ============================================================
# PROMPTS
# ============================================================

# Simple prompt (without DSPy)
SIMPLE_PROMPT = """You are a helpful AI assistant that understands Malaysian Malay, English, and Manglish.
When the user writes in Malay or Manglish, respond naturally in their language."""

# DSPy-enhanced prompt (with slang mappings)
DSPY_PROMPT = get_enhanced_prompt()


# ============================================================
# OLLAMA CLIENT
# ============================================================

def call_ollama(query: str, model: str, system_prompt: str, timeout: int = 90) -> str:
    """Call Ollama API with timeout."""
    try:
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                "stream": False
            },
            timeout=timeout
        )
        data = resp.json()
        return data.get("message", {}).get("content", "ERROR: No response")
    except requests.exceptions.Timeout:
        return "ERROR: Timeout"
    except Exception as e:
        return f"ERROR: {e}"


# ============================================================
# EVALUATION (using GPT-4o as judge)
# ============================================================

def evaluate_with_gpt4o(query: str, response: str, expected: str) -> Dict:
    """Use GPT-4o to evaluate response quality."""
    from langchain_openai import ChatOpenAI
    
    prompt = f"""Evaluate how well this AI model understood a Malaysian Malay/Manglish query.

Query: {query}
Expected Understanding: {expected}

Model's Response:
{response}

Score from 1-10:
1-2 = Completely misunderstood
3-4 = Partially understood
5-6 = Moderate understanding
7-8 = Good understanding
9-10 = Excellent, fully understood

Respond with JSON: {{"score": <1-10>, "reasoning": "<brief>"}}"""

    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        result = llm.invoke(prompt)
        
        import re
        json_match = re.search(r'\{.*\}', result.content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Eval error: {e}")
    
    return {"score": 0, "reasoning": "Failed to evaluate"}


# ============================================================
# RUN COMPARISON
# ============================================================

def run_model_comparison(model: str):
    """Run DSPy comparison for a single Ollama model."""
    
    print(f"\n{'='*70}")
    print(f"Testing: {model}")
    print(f"{'='*70}")
    
    results = {"without_dspy": [], "with_dspy": []}
    
    # Test WITHOUT DSPy
    print(f"\n[1/2] Testing {model} WITHOUT DSPy...")
    print("-" * 50)
    
    for tc in QUICK_TEST_CASES:
        print(f"  {tc.id}: ", end="", flush=True)
        response = call_ollama(tc.query, model, SIMPLE_PROMPT)
        
        if response.startswith("ERROR"):
            print(f"{response}")
            results["without_dspy"].append({"id": tc.id, "score": 0, "error": response})
        else:
            eval_result = evaluate_with_gpt4o(tc.query, response, tc.expected_understanding)
            print(f"{eval_result['score']}/10")
            results["without_dspy"].append({
                "id": tc.id,
                "category": tc.category,
                "response": response[:100],
                "score": eval_result["score"],
                "reasoning": eval_result.get("reasoning", "")
            })
    
    # Test WITH DSPy
    print(f"\n[2/2] Testing {model} WITH DSPy...")
    print("-" * 50)
    
    for tc in QUICK_TEST_CASES:
        print(f"  {tc.id}: ", end="", flush=True)
        response = call_ollama(tc.query, model, DSPY_PROMPT)
        
        if response.startswith("ERROR"):
            print(f"{response}")
            results["with_dspy"].append({"id": tc.id, "score": 0, "error": response})
        else:
            eval_result = evaluate_with_gpt4o(tc.query, response, tc.expected_understanding)
            print(f"{eval_result['score']}/10")
            results["with_dspy"].append({
                "id": tc.id,
                "category": tc.category,
                "response": response[:100],
                "score": eval_result["score"],
                "reasoning": eval_result.get("reasoning", "")
            })
    
    return results


def print_comparison(model: str, results: Dict):
    """Print comparison table."""
    
    no_dspy_scores = [r["score"] for r in results["without_dspy"]]
    with_dspy_scores = [r["score"] for r in results["with_dspy"]]
    
    no_dspy_avg = sum(no_dspy_scores) / len(no_dspy_scores) if no_dspy_scores else 0
    with_dspy_avg = sum(with_dspy_scores) / len(with_dspy_scores) if with_dspy_scores else 0
    improvement = with_dspy_avg - no_dspy_avg
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {model}")
    print(f"{'='*70}")
    
    print(f"\n{'Test Case':<15} {'Without DSPy':<15} {'With DSPy':<15} {'Change':<10}")
    print("-" * 55)
    
    for no_d, with_d in zip(results["without_dspy"], results["with_dspy"]):
        change = with_d["score"] - no_d["score"]
        change_str = f"+{change}" if change > 0 else str(change)
        if change > 0:
            change_str += " ⬆️"
        elif change < 0:
            change_str += " ⬇️"
        print(f"{no_d['id']:<15} {no_d['score']}/10{'':<9} {with_d['score']}/10{'':<9} {change_str}")
    
    print("-" * 55)
    improvement_str = f"+{improvement:.1f}" if improvement > 0 else f"{improvement:.1f}"
    print(f"{'AVERAGE':<15} {no_dspy_avg:.1f}/10{'':<9} {with_dspy_avg:.1f}/10{'':<9} {improvement_str}")
    
    return {
        "model": model,
        "without_dspy_avg": no_dspy_avg,
        "with_dspy_avg": with_dspy_avg,
        "improvement": improvement
    }


def main():
    """Run comparison for all local models."""
    
    print("=" * 70)
    print("DSPy Comparison Test for Local Ollama Models")
    print("=" * 70)
    print("Models to test: qwen3:14b, qwen2.5:14b, llama3.2:3b")
    print("Test cases: 6")
    print("Judge: GPT-4o")
    
    all_results = {}
    summaries = []
    
    # Test all 3 models
    for model in ["qwen3:14b", "qwen2.5:14b", "llama3.2:3b"]:
        results = run_model_comparison(model)
        all_results[model] = results
        summary = print_comparison(model, results)
        summaries.append(summary)
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"\n{'Model':<20} {'Without DSPy':<15} {'With DSPy':<15} {'Improvement':<12}")
    print("-" * 62)
    
    for s in summaries:
        imp_str = f"+{s['improvement']:.1f}" if s['improvement'] > 0 else f"{s['improvement']:.1f}"
        conclusion = "✅" if s['improvement'] > 0 else ("➡️" if s['improvement'] == 0 else "⚠️")
        print(f"{s['model']:<20} {s['without_dspy_avg']:.1f}/10{'':<9} {s['with_dspy_avg']:.1f}/10{'':<9} {imp_str} {conclusion}")
    
    # Save results
    with open("ollama_dspy_comparison.json", "w") as f:
        json.dump({
            "summaries": summaries,
            "details": all_results
        }, f, indent=2)
    
    print(f"\nResults saved to: ollama_dspy_comparison.json")


if __name__ == "__main__":
    main()
