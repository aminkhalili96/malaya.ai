import argparse
import json
import re
import os
from pathlib import Path

# Project Paths
root_dir = Path(__file__).parent.parent
DEFAULT_CASES_FILE = root_dir / "tests/fixtures/expanded_cases.json"
DEFAULT_LOG_FILE = root_dir / "reports/v3_benchmark/malaya_ai_v7.json"
DEFAULT_MANUAL_FILE = root_dir / "reports/malaya_ai_v7_agent_judge_semantic.json"
DEFAULT_REPORT_FILE = root_dir / "reports/malaya_ai_v7_agent_judge_manual.json"

def load_json(path):
    with open(path, 'r') as f: return json.load(f)

def _is_idk_response(text):
    if not text:
        return True
    lowered = text.lower()
    return bool(re.search(
        r"\\b(idk|i\\s*(?:do\\s+not|don't|dont)\\s+know|no\\s+idea|not\\s+sure|"
        r"(?:tak|tidak|x)\\s*tahu|xtau|tak\\s*pasti|tidak\\s*pasti|entah)\\b",
        lowered
    ))

def load_manual_scores(path):
    data = load_json(path)
    if isinstance(data, dict) and "results" in data:
        entries = data["results"]
    elif isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = [{"id": k, "score": v} for k, v in data.items()]
    else:
        entries = []
    scores = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        cid = entry.get("id")
        score = entry.get("score")
        if cid is None or score is None:
            continue
        scores[str(cid)] = float(score)
    return scores

def main():
    parser = argparse.ArgumentParser(description="Manual Agent Judge aggregator (no API judge).")
    parser.add_argument("--log", default=os.getenv("MALAYA_JUDGE_LOG", str(DEFAULT_LOG_FILE)))
    parser.add_argument("--cases", default=os.getenv("MALAYA_JUDGE_CASES", str(DEFAULT_CASES_FILE)))
    parser.add_argument("--manual", default=os.getenv("MALAYA_JUDGE_MANUAL", str(DEFAULT_MANUAL_FILE)))
    parser.add_argument("--output", default=os.getenv("MALAYA_JUDGE_OUTPUT", str(DEFAULT_REPORT_FILE)))
    args = parser.parse_args()

    print("Agent-as-a-Judge: Initializing...")
    
    # 1. Load Test Cases
    cases_list = load_json(Path(args.cases))
    cases_map = {str(c['id']): c for c in cases_list}
    
    # 2. Load Results
    log_data = load_json(Path(args.log))
    results = log_data.get('results', [])

    manual_scores = load_manual_scores(Path(args.manual))
    if not manual_scores:
        raise SystemExit(f"No manual scores found in {args.manual}")
    
    scores = []
    report_rows = []
    unscored = 0
    
    print(f"Judging {len(results)} cases from {Path(args.log).name}...")
    print("-" * 60)
    print(f"{'ID':<5} | {'Score':<5} | {'Verdict':<10}")
    print("-" * 60)
    
    for res in results:
        cid = str(res.get('id'))
        actual = res.get('response') or res.get('raw_response') or ""
        
        # Get reference
        if cid not in cases_map:
            continue
        ref_case = cases_map[cid]
        question = ref_case['input']
        reference = ref_case.get('reference_answer', '')
        # Grading
        if _is_idk_response(actual):
            score = 0.0
            reason = "IDK response"
        elif cid in manual_scores:
            score = float(manual_scores[cid])
            reason = "Manual score"
        else:
            score = 0.0
            reason = "Unscored"
            unscored += 1
        scores.append(score)
        
        verdict = "PASS" if score == 1.0 else ("PARTIAL" if score == 0.5 else "FAIL")
        print(f"{cid:<5} | {score:<5} | {verdict}")
        report_rows.append({
            "id": int(cid) if cid.isdigit() else cid,
            "category": ref_case.get("category"),
            "input": question,
            "response": actual,
            "score": score,
            "verdict": verdict,
            "reason": reason,
        })
        
    # 4. Final Calculation
    avg_score = (sum(scores) / len(scores)) * 100
    print("-" * 60)
    print(f"Final Agentic Score: {avg_score:.1f}%")
    print("-" * 60)
    
    # 5. Save Report
    report = {
        "summary": {
            "manual_scores": str(Path(args.manual).name),
            "log": str(Path(args.log).name),
            "score_percent": round(avg_score, 1),
            "cases": len(scores),
            "unscored": unscored,
        },
        "results": report_rows,
    }
    with open(Path(args.output), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
if __name__ == "__main__":
    main()
