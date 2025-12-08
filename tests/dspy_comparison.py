"""
DSPy Before/After Comparison Test

This script compares model performance WITH and WITHOUT DSPy enhancement.
It runs the same test cases twice:
1. Without DSPy (use_dspy=False)
2. With DSPy (use_dspy=True)

Then outputs the comparison.
"""

import os
import sys
import json
from typing import List, Dict
from dataclasses import dataclass, asdict

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chatbot.engine import MalayaChatbot


# ============================================================
# QUICK TEST CASES (subset for fast comparison)
# ============================================================

@dataclass
class TestCase:
    id: str
    category: str
    query: str
    expected_understanding: str


QUICK_TEST_CASES = [
    # Shortforms
    TestCase(
        id="short_01",
        category="Shortforms",
        query="xleh la bro, aku xde duit skrg",
        expected_understanding="Cannot bro, I don't have money right now"
    ),
    TestCase(
        id="short_02",
        category="Shortforms",
        query="xtau la bro, aku xphm lgsg",
        expected_understanding="I don't know bro, I don't understand at all"
    ),
    # Particles
    TestCase(
        id="particle_01",
        category="Particles",
        query="best gila siot benda ni!",
        expected_understanding="This thing is extremely awesome!"
    ),
    # Cultural
    TestCase(
        id="culture_01",
        category="Cultural",
        query="lepak mamak jom, aku belanja teh tarik",
        expected_understanding="Let's hang at mamak, I'll treat you to teh tarik"
    ),
    # Manglish
    TestCase(
        id="manglish_01",
        category="Manglish",
        query="that meeting how ah? client happy tak?",
        expected_understanding="How was the meeting? Was the client happy?"
    ),
    # Sentiment
    TestCase(
        id="sentiment_01",
        category="Sentiment",
        query="geram betul la dengan service ni",
        expected_understanding="Really frustrated with this service"
    ),
]


def evaluate_response(query: str, response: str, expected: str) -> Dict:
    """
    Simple evaluation: check if key terms are understood.
    Returns score 1-10 based on presence of expected concepts.
    """
    response_lower = response.lower()
    expected_lower = expected.lower()
    
    # Extract key words from expected understanding
    key_words = [w for w in expected_lower.split() if len(w) > 3]
    
    # Count how many key concepts are reflected in response
    matches = sum(1 for word in key_words if word in response_lower)
    
    score = min(10, max(1, int((matches / max(1, len(key_words))) * 10)))
    
    return {
        "score": score,
        "key_words": key_words,
        "matches": matches
    }


def run_comparison():
    """Run comparison with and without DSPy."""
    
    print("=" * 70)
    print("DSPy Before/After Comparison Test")
    print("=" * 70)
    
    results = {
        "without_dspy": [],
        "with_dspy": []
    }
    
    # Test WITHOUT DSPy
    print("\n[1/2] Testing WITHOUT DSPy...")
    print("-" * 50)
    
    bot_no_dspy = MalayaChatbot(use_dspy=False)
    print(f"DSPy enabled: {bot_no_dspy.use_dspy}")
    
    for tc in QUICK_TEST_CASES:
        print(f"  Testing: {tc.id}...")
        try:
            result = bot_no_dspy.process_query(tc.query)
            response = result.get("answer", "")
            eval_result = evaluate_response(tc.query, response, tc.expected_understanding)
            
            results["without_dspy"].append({
                "id": tc.id,
                "category": tc.category,
                "query": tc.query,
                "response": response[:100] + "..." if len(response) > 100 else response,
                "score": eval_result["score"]
            })
            print(f"    Score: {eval_result['score']}/10")
        except Exception as e:
            print(f"    Error: {e}")
            results["without_dspy"].append({
                "id": tc.id,
                "score": 0,
                "error": str(e)
            })
    
    # Test WITH DSPy
    print("\n[2/2] Testing WITH DSPy...")
    print("-" * 50)
    
    bot_with_dspy = MalayaChatbot(use_dspy=True)
    print(f"DSPy enabled: {bot_with_dspy.use_dspy}")
    
    for tc in QUICK_TEST_CASES:
        print(f"  Testing: {tc.id}...")
        try:
            result = bot_with_dspy.process_query(tc.query)
            response = result.get("answer", "")
            eval_result = evaluate_response(tc.query, response, tc.expected_understanding)
            
            results["with_dspy"].append({
                "id": tc.id,
                "category": tc.category,
                "query": tc.query,
                "response": response[:100] + "..." if len(response) > 100 else response,
                "score": eval_result["score"]
            })
            print(f"    Score: {eval_result['score']}/10")
        except Exception as e:
            print(f"    Error: {e}")
            results["with_dspy"].append({
                "id": tc.id,
                "score": 0,
                "error": str(e)
            })
    
    # Calculate averages
    no_dspy_avg = sum(r["score"] for r in results["without_dspy"]) / len(results["without_dspy"])
    with_dspy_avg = sum(r["score"] for r in results["with_dspy"]) / len(results["with_dspy"])
    
    # Print comparison
    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    
    print(f"\n{'Test Case':<15} {'Without DSPy':<15} {'With DSPy':<15} {'Change':<10}")
    print("-" * 55)
    
    for i, (no_dspy, with_dspy) in enumerate(zip(results["without_dspy"], results["with_dspy"])):
        change = with_dspy["score"] - no_dspy["score"]
        change_str = f"+{change}" if change > 0 else str(change)
        print(f"{no_dspy['id']:<15} {no_dspy['score']}/10{'':<9} {with_dspy['score']}/10{'':<9} {change_str:<10}")
    
    print("-" * 55)
    improvement = with_dspy_avg - no_dspy_avg
    print(f"{'AVERAGE':<15} {no_dspy_avg:.1f}/10{'':<9} {with_dspy_avg:.1f}/10{'':<9} {'+' if improvement > 0 else ''}{improvement:.1f}")
    
    print("\n" + "=" * 70)
    if improvement > 0:
        print(f"✅ DSPy IMPROVED performance by {improvement:.1f} points!")
    elif improvement < 0:
        print(f"⚠️  DSPy decreased performance by {abs(improvement):.1f} points")
    else:
        print("➡️  No change in performance")
    print("=" * 70)
    
    # Save results
    with open("dspy_comparison_results.json", "w") as f:
        json.dump({
            "summary": {
                "without_dspy_avg": no_dspy_avg,
                "with_dspy_avg": with_dspy_avg,
                "improvement": improvement
            },
            "details": results
        }, f, indent=2)
    
    print(f"\nFull results saved to: dspy_comparison_results.json")


if __name__ == "__main__":
    run_comparison()
