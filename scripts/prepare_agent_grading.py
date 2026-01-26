#!/usr/bin/env python3
"""
Prepare Agent Grading Docket
============================
Reads all .jsonl benchmark logs and creates a Markdown file optimized for 
Gemini 3 Pro to review and grade.

Output: reports/grading_docket.md
"""

import json
import glob
import os
from pathlib import Path

def load_test_cases(filepath):
    with open(filepath, 'r') as f:
        cases = json.load(f)
    # Ensure it's a dict keyed by ID
    return {str(c['id']): c for c in cases}

def reference_alignment_flag(case):
    reference = case.get("reference_answer", "") or ""
    expected = [k.lower() for k in case.get("expected_keywords", [])]
    ref_lower = reference.lower()
    if not expected:
        return False
    return any(k in ref_lower for k in expected)

def load_log_file(filepath):
    results = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if 'id' in data:
                            results[str(data['id'])] = data.get('output', '') or data.get('response', '')
                        elif 'grading' in data: # V3 format
                             results[str(data['id'])] = data.get('response', '')
                    except:
                        pass
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return results

def main():
    root_dir = Path(__file__).parent.parent
    reports_dir = root_dir / "reports"
    cases_path = root_dir / "tests/fixtures/expanded_cases.json"
    output_path = reports_dir / "grading_docket.md"

    print(f"Loading test cases from {cases_path}...")
    cases = load_test_cases(cases_path)
    total_cases = len(cases)
    print(f"Total Reference Cases: {total_cases}")

    # Find all log files
    log_files = glob.glob(str(reports_dir / "benchmark_competitor_*.jsonl"))
    # Add V3 logs
    v3_logs = glob.glob(str(reports_dir / "v3_benchmark/v3_benchmark_*.json"))
    
    # Also Check for logs in reports/ if any
    
    model_data = {}

    # Process Competitor Logs
    for log_file in log_files:
        model_name = os.path.basename(log_file).replace("benchmark_competitor_", "").replace(".jsonl", "")
        results = load_log_file(log_file)
        model_data[model_name] = results

    # Process V3 Logs (Usually JSON, not JSONL, but let's check extension)
    for log_file in v3_logs:
        if "graded" in log_file: continue
        model_name = "Malaya_V3_" + os.path.basename(log_file).split('_')[2] # timestamp
        try:
             with open(log_file, 'r') as f:
                data = json.load(f)
                results = {}
                if 'results' in data:
                    for r in data['results']:
                        results[str(r['id'])] = r.get('response', '')
                model_data[model_name] = results
        except:
            pass

    # Generate Markdown Docket
    with open(output_path, 'w') as f:
        f.write("# Agent Grading Docket\n\n")
        f.write("> Instructions: Use Expected Keywords + intent as primary signal. Reference Answer may be misaligned.\n")
        f.write("> Rate 0-10 for understanding and helpfulness.\n\n")
        
        # Summary Table
        f.write("## 1. Completion Summary\n\n")
        f.write("| Model | Completed Cases | % |\n")
        f.write("| :--- | :--- | :--- |\n")
        for model in sorted(model_data.keys()):
            count = len(model_data[model])
            pct = round((count / total_cases) * 100, 1)
            f.write(f"| {model} | {count}/{total_cases} | {pct}% |\n")
        
        f.write("\n---\n\n")
        f.write("## 2. Test Case Deep Dive (Sample 5 Difficult Cases)\n\n")
        
        # Select 5 specific difficult cases (Shortforms, Dialects)
        target_ids = ['1', '8', '14', '32', '38'] 
        
        for case_id in target_ids:
            if case_id not in cases: continue
            case = cases[case_id]
            f.write(f"### Case {case_id}: {case['category']}\n")
            f.write(f"**Input:** `{case['input']}`\n")
            f.write(f"**Expected Keywords:** `{', '.join(case.get('expected_keywords', []))}`\n")
            reference = case.get('reference_answer', '')
            aligned = reference_alignment_flag(case)
            if aligned:
                f.write(f"**Reference:** `{reference}`\n\n")
            else:
                f.write(f"**Reference (Unaligned):** `{reference}`\n\n")
            
            f.write("| Model | Response | Score (Agent) |\n")
            f.write("| :--- | :--- | :--- |\n")
            
            for model in sorted(model_data.keys()):
                response = model_data[model].get(case_id, "MISSING").replace("\n", " ")
                f.write(f"| **{model}** | {response[:150]}... | |\n")
            
            f.write("\n")

    print(f"Docket generated at {output_path}")

if __name__ == "__main__":
    main()
