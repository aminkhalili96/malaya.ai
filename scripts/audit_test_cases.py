#!/usr/bin/env python3
"""
Audit expanded_cases.json for reference/keyword alignment issues.
Outputs a Markdown report for tracking.
"""

import json
from pathlib import Path


ROOT = Path(__file__).parent.parent
CASES_PATH = ROOT / "tests" / "fixtures" / "expanded_cases.json"
OUT_PATH = ROOT / "reports" / "test_case_alignment_report.md"


def reference_has_keywords(case):
    reference = (case.get("reference_answer") or "").lower()
    expected = [k.lower() for k in case.get("expected_keywords", [])]
    if not expected:
        return True
    return any(k in reference for k in expected)


def main() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    mismatches = [c for c in cases if not reference_has_keywords(c)]

    lines = []
    lines.append("# Test Case Reference Alignment Report")
    lines.append("")
    lines.append(f"Total cases: **{len(cases)}**")
    lines.append(f"Reference mismatches: **{len(mismatches)}**")
    lines.append("")
    lines.append("## Mismatched Cases")
    lines.append("")
    lines.append("| ID | Category | Input | Reference (Current) |")
    lines.append("| --- | --- | --- | --- |")
    for case in mismatches:
        cid = case.get("id")
        category = case.get("category", "Unknown")
        input_text = case.get("input", "").replace("\n", " ")
        reference = (case.get("reference_answer") or "").replace("\n", " ")
        lines.append(f"| {cid} | {category} | {input_text} | {reference} |")
    lines.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
