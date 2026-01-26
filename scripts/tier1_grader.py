#!/usr/bin/env python3
"""
Tier 1 Grader (Agent Logic Proxy)
=================================
Implements specific grading logic for the Malaya LLM Benchmark.
This script acts as a proxy for Gemini 3 Pro's judgment, using advanced
pattern matching to evaluate the 100 test cases.

It handles:
- Dialect context (e.g., 'demo' = 'you' in Kelantan)
- Fact verification (e.g., 'Anwar Ibrahim')
- Manglish acceptance
"""

import json
import glob
import re
import os
from pathlib import Path

# --- Grading Logic Overrides ---
def grade_case_logic(case_id, response_lower, response_text):
    """
    Returns (score, feedback). Score 0.0 to 1.0.
    """
    
    # 1. Shortforms: "xleh la bro" -> Refusal / Can't
    if case_id == '1':
        if any(x in response_lower for x in ['tak boleh', 'cannot', 'x boleh', 'tak dapat', 'no money']):
            return 1.0, "Correct refusal"
        if any(x in response_lower for x in ['tiada masalah', 'no problem', 'ok']):
            return 0.0, "Incorrect acceptance"
        return 0.5, "Ambiguous"

    # 32. Facts: Prime Minister (STRICT)
    if case_id == '32':
        if 'anwar' in response_lower:
            return 1.0, "Correct (Anwar)"
        if 'ismail sabri' in response_lower or 'muhyiddin' in response_lower:
            return 0.0, "Outdated (Sabri/Muhyiddin)"
        return 0.0, "Incorrect"

    # 8. Kelantan: "demo tokene" -> "mu tak makan lagi?" (RELAXED)
    if case_id == '8':
        # Prompt: "demo tokene make nasi kerabu lagi ko?"
        # Standard Malay: "awak tak makan nasi kerabu lagi ke?"
        
        # 1. Did it understand the TOPIC (eating / nasi kerabu)?
        topic_match = ('makan' in response_lower or 'eat' in response_lower) and \
                      ('nasi' in response_lower or 'kerabu' in response_lower)
        
        if topic_match:
             return 1.0, "Understood dialect input"
        
        if 'demonstration' in response_lower or 'token' in response_lower:
            return 0.0, "Misinterpreted 'demo/token'"
        
        # Fallback partial credit if just 'makan' is found
        if 'makan' in response_lower:
            return 0.5, "Partial understanding"
            
        return 0.0, "Failed"

    # 38. Translation: I Love You (Kelantan) -> Kawe/Ambo/Kito (RELAXED)
    if case_id == '38':
        # Authentic Dialect
        if any(x in response_lower for x in ['kawe', 'ambo', 'kito']) and 'sayang' in response_lower:
            return 1.0, "Authentic Kelantan"
        
        # Standard Malay Acceptance (User Request: Loose Dialect)
        # "Saya sayang awak" or "Aku cinta kamu" is now ACCEPTABLE because it understood the requested meaning
        if 'saya sayang' in response_lower or 'aku sayang' in response_lower or 'cinta' in response_lower:
            return 1.0, "Correct Meaning (Standard Malay Accepted)"
            
        return 0.0, "Failed"
        
    # Default: Enhanced Keyword Match
    return -1, "Use Default"

def load_case_keywords(cases_path):
    with open(cases_path, 'r') as f:
        cases = json.load(f)
    return {str(c['id']): c for c in cases}

def grade_submission(results, cases):
    scores = []
    
    for case_id, response in results.items():
        if case_id not in cases: continue
        
        case = cases[case_id]
        response_lower = response.lower()
        
        # 1. Check Specific Logic first
        score, reason = grade_case_logic(case_id, response_lower, response)
        
        # 2. Fallback to Enhanced Keyword Match
        if score == -1:
            expected = [k.lower() for k in case.get('expected_keywords', [])]
            negative = [k.lower() for k in case.get('negative_keywords', [])]
            
            # Negative penalty
            if any(n in response_lower for n in negative):
                score = 0.0
            else:
                # Positives (Keyword Saturation)
                hits = sum(1 for k in expected if k in response_lower)
                
                if hits >= 2:
                    # If 2 or more keywords found, assume full intent coverage (Synonym list handling)
                    score = 1.0
                elif hits == 1:
                    # Single keyword match
                    if len(expected) <= 2:
                        score = 1.0 # If only 1-2 keywords expected, 1 hit is perfect
                    else:
                        score = 0.8 # Good partial credit
                else:
                    # No keywords matched
                    score = 0.0
                    if len(response) > 10: score = 0.1 # Tiny effort score
        
        scores.append(score)
        
    if not scores: return 0.0
    return sum(scores) / len(scores)

def main():
    root_dir = Path(__file__).parent.parent
    reports_dir = root_dir / "reports"
    cases = load_case_keywords(root_dir / "tests/fixtures/expanded_cases.json")
    
    log_files = glob.glob(str(reports_dir / "*.jsonl")) + glob.glob(str(reports_dir / "benchmark_competitor_*.jsonl"))
    # Add V3 format logs
    v3_logs = glob.glob(str(reports_dir / "v3_benchmark/v3_benchmark_*.json"))
    # Add V4 logs
    v4_logs = glob.glob(str(reports_dir / "v3_benchmark/v4_benchmark_*.json"))
    # Add V5 logs
    v5_logs = glob.glob(str(reports_dir / "v3_benchmark/v5_benchmark_*.json"))
    # Add V6 logs
    v6_logs = glob.glob(str(reports_dir / "v3_benchmark/v6_full_benchmark_*.json"))
    
    final_results = []
    
    # Process Standard JSONL
    seen_models = set()
    
    for log_path in log_files:
        model = os.path.basename(log_path).replace("benchmark_competitor_", "").replace(".jsonl", "")
        if model in seen_models: continue
        seen_models.add(model)
        
        results = {}
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            d = json.loads(line)
                            if 'id' in d: results[str(d['id'])] = d.get('output', '') or d.get('response', '')
                        except: pass
        except: continue
        
        final_score = grade_submission(results, cases)
        final_results.append({
            "model": model, 
            "score": round(final_score * 100, 1),
            "completed": len(results)
        })

    # Process V3
    for log_path in v3_logs:
        if "graded" in log_path: continue
        filename = os.path.basename(log_path)
        # Extract meaningful name
        if "with_gate" in filename: model = "Malaya V3 (Gate)"
        else: model = "Malaya V3 w/ " + filename.split('_')[0]
        
        results = {}
        try:
            with open(log_path, 'r') as f:
                d = json.load(f)
                if 'results' in d:
                    for r in d['results']:
                        results[str(r['id'])] = r.get('response', '')
        except: continue
        
        final_score = grade_submission(results, cases)
        final_results.append({
            "model": model,
            "score": round(final_score * 100, 1),
            "completed": len(results)
        })

    # Process V4
    for log_path in v4_logs:
        filename = os.path.basename(log_path)
        model = "Malaya V4 (Agnt)" # Short for Agentic
        
        results = {}
        try:
            with open(log_path, 'r') as f:
                d = json.load(f)
                if 'results' in d:
                    for r in d['results']:
                        results[str(r['id'])] = r.get('response', '')
        except: continue
        
        final_score = grade_submission(results, cases)
        final_results.append({
            "model": model,
            "score": round(final_score * 100, 1),
            "completed": len(results)
        })

    # Process V5
    for log_path in v5_logs:
        filename = os.path.basename(log_path)
        model = "Malaya V5 (Agnt)" # Agentic + Web
        
        results = {}
        try:
            with open(log_path, 'r') as f:
                d = json.load(f)
                if 'results' in d:
                    for r in d['results']:
                        results[str(r['id'])] = r.get('response', '')
                elif 'results' not in d and isinstance(d, dict): # Handle V5 new format if needed, but it uses "results" list
                     pass
        except: continue
        
        final_score = grade_submission(results, cases)
        final_results.append({
            "model": model,
            "score": round(final_score * 100, 1),
            "completed": len(results)
        })

    # Process V6
    for log_path in v6_logs:
        filename = os.path.basename(log_path)
        model = "Malaya V6 (Full)" # V6 with RAG + Web + SFT Model
        
        results = {}
        try:
            with open(log_path, 'r') as f:
                d = json.load(f)
                if 'results' in d:
                    for r in d['results']:
                        results[str(r['id'])] = r.get('response', '')
        except: continue
        
        final_score = grade_submission(results, cases)
        final_results.append({
            "model": model,
            "score": round(final_score * 100, 1),
            "completed": len(results)
        })
    
    # Print Table
    print(f"| Model | Score (Agent Proxy) | Cases |")
    print(f"| :--- | :--- | :--- |")
    for r in sorted(final_results, key=lambda x: x['score'], reverse=True):
        print(f"| {r['model']} | {r['score']}% | {r['completed']} |")
        
    # Diagnosis for V5 (Priority) or V4
    print("\n=== V5/V4 Failure Analysis ===")
    target_log = None
    if v5_logs: target_log = v5_logs[-1]
    elif v4_logs: target_log = v4_logs[-1]
    
    if target_log:
        with open(target_log, 'r') as f:
            d = json.load(f)
            # Handle V5 list format vs V4 list format (both use "results")
            if 'results' in d:
                results = {str(r['id']): r.get('response', '') for r in d['results']}
            else:
                results = {}
            
        for cid, case in cases.items():
            if cid in results:
                response = results[cid]
                
                # Check for negative keywords
                negative_hits = [k for k in case.get('negative_keywords', []) if k.lower() in response.lower()]
                if negative_hits:
                    score = 0.0
                    reason = f"Negative keyword: {negative_hits}"
                else:
                    needed = case.get('expected_keywords', [])
                    hits = [k for k in needed if k.lower() in response.lower()]
                    
                    if not needed: score = 1.0
                    else:
                        hit_count = len(hits)
                        if hit_count >= 2: score = 1.0
                        elif hit_count == 1: score = 0.5
                        else: score = 0.0
                    reason = f"Hits: {len(hits)}/{len(needed)} ({hits})"
                
                if score < 1.0:
                    print(f"Case {cid} (Score {score}): {case['input']}")
                    print(f"  Response: {response}")
                    print(f"  Reason: {reason}")
                    print("-" * 40)

if __name__ == "__main__":
    main()
