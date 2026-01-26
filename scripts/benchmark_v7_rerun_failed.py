#!/usr/bin/env python3
"""
Re-run only failed cases for Malaya V7 benchmark and update the existing log.

Usage:
  MALAYA_BENCHMARK_OUTPUT=reports/v3_benchmark/malaya_ai_v7.json \
  python scripts/benchmark_v7_rerun_failed.py
"""

import json
import os
import re
import sys
import importlib.util
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).parent.parent
DEFAULT_LOG = ROOT / "reports" / "v3_benchmark" / "malaya_ai_v7.json"
DEFAULT_FAILURES = ROOT / "reports" / "malaya_ai_v7_agent_judge_semantic.json"
CASES_FILE = ROOT / "tests" / "fixtures" / "expanded_cases.json"


def _load_benchmark_module():
    module_path = ROOT / "scripts" / "benchmark_v7_full.py"
    spec = importlib.util.spec_from_file_location("benchmark_v7_full", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["benchmark_v7_full"] = module
    if spec and spec.loader:
        spec.loader.exec_module(module)
    return module


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _extract_failed_ids(failure_data: dict) -> list:
    if "failures" in failure_data:
        return [str(item["id"]) for item in failure_data.get("failures", []) if "id" in item]
    if "results" in failure_data:
        return [
            str(item["id"])
            for item in failure_data.get("results", [])
            if isinstance(item, dict) and str(item.get("score", "")) == "0.0"
        ]
    return []


def main() -> int:
    benchmark = _load_benchmark_module()
    log_path = Path(os.getenv("MALAYA_BENCHMARK_OUTPUT", str(DEFAULT_LOG)))
    failures_path = Path(os.getenv("MALAYA_FAILURES_PATH", str(DEFAULT_FAILURES)))
    override_cases = os.getenv("MALAYA_CASE_IDS", "").strip()

    if not log_path.exists():
        raise SystemExit(f"Missing log file: {log_path}")
    if not failures_path.exists():
        raise SystemExit(f"Missing failures file: {failures_path}")

    cases = {str(c["id"]): c for c in load_json(CASES_FILE)}
    log_data = load_json(log_path)
    results = log_data.get("results", [])
    results_map = {str(r.get("id")): r for r in results if isinstance(r, dict)}

    if override_cases:
        failed_ids = [cid.strip() for cid in override_cases.split(",") if cid.strip()]
    else:
        failure_data = load_json(failures_path)
        failed_ids = _extract_failed_ids(failure_data)

    if not failed_ids:
        print("No failed cases to re-run.")
        return 0

    updated = []
    for cid in failed_ids:
        case = cases.get(cid)
        if not case:
            continue
        print(f"Re-running case {cid}...")
        response = benchmark.generate_v7_full_response(case["input"])
        clean_response = re.sub(r"<thought>.*?</thought>", "", response, flags=re.DOTALL).strip()
        results_map[cid] = {
            "id": case["id"],
            "input": case["input"],
            "response": clean_response,
            "raw_response": response,
            "category": case.get("category"),
        }
        updated.append(cid)

    log_data["results"] = [results_map[str(c["id"])] for c in cases.values() if str(c["id"]) in results_map]
    log_data["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    log_data["updated_cases"] = updated
    save_json(log_path, log_data)

    print(f"Updated {len(updated)} cases in {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
