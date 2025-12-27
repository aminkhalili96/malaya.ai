#!/usr/bin/env python3
"""
Generate a lexicon coverage and overlap report.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _collect_terms(block: dict) -> dict:
    return {k: v for k, v in block.items() if isinstance(k, str) and not k.startswith("_")}


def _build_report(data: dict) -> dict:
    dialects = data.get("dialects", {})
    report = {
        "meta": data.get("_meta", {}),
        "counts": {},
        "dialects": {},
        "overlaps": {},
    }

    report["counts"]["shortforms"] = len(_collect_terms(data.get("shortforms", {})))
    report["counts"]["genz_tiktok"] = len(_collect_terms(data.get("genz_tiktok", {})))
    report["counts"]["intensity_markers"] = len(_collect_terms(data.get("intensity_markers", {})))
    report["counts"]["colloquialisms"] = len(_collect_terms(data.get("colloquialisms", {})))
    report["counts"]["ambiguous_terms"] = len(
        [k for k in data.get("ambiguous_terms", {}).keys() if not k.startswith("_")]
    )

    all_terms = defaultdict(list)
    for dialect, payload in dialects.items():
        terms = _collect_terms(payload if isinstance(payload, dict) else {})
        report["dialects"][dialect] = {
            "status": payload.get("_status") if isinstance(payload, dict) else None,
            "terms": len(terms),
        }
        for term in terms.keys():
            all_terms[term].append(dialect)

    overlaps = {term: groups for term, groups in all_terms.items() if len(groups) > 1}
    report["overlaps"]["dialects"] = overlaps
    report["overlaps"]["dialect_overlap_count"] = len(overlaps)

    overlap_sizes = Counter(len(groups) for groups in overlaps.values())
    report["overlaps"]["distribution"] = dict(overlap_sizes)

    return report


def _render_markdown(report: dict) -> str:
    lines = []
    lines.append("# Lexicon Coverage Report")
    lines.append("")
    meta = report.get("meta", {})
    if meta:
        lines.append(f"Version: **{meta.get('version', 'unknown')}**")
        lines.append(f"Last updated: **{meta.get('last_updated', 'unknown')}**")
        lines.append("")

    counts = report.get("counts", {})
    lines.append("## Counts")
    lines.append("")
    lines.append("| Category | Terms |")
    lines.append("| --- | --- |")
    for key, value in counts.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")

    lines.append("## Dialect Coverage")
    lines.append("")
    lines.append("| Dialect | Status | Terms |")
    lines.append("| --- | --- | --- |")
    for dialect, info in sorted(report.get("dialects", {}).items()):
        lines.append(f"| {dialect} | {info.get('status')} | {info.get('terms')} |")
    lines.append("")

    overlaps = report.get("overlaps", {})
    lines.append("## Dialect Overlaps")
    lines.append("")
    lines.append(f"Overlapping dialect terms: **{overlaps.get('dialect_overlap_count', 0)}**")
    distribution = overlaps.get("distribution", {})
    if distribution:
        lines.append("")
        lines.append("Overlap distribution (term appears in N dialects):")
        for count, total in sorted(distribution.items()):
            lines.append(f"- {count} dialects: {total} terms")
    lines.append("")

    # Show a small sample of overlaps
    overlap_items = list(overlaps.get("dialects", {}).items())
    if overlap_items:
        lines.append("Sample overlaps:")
        for term, dialects in overlap_items[:10]:
            lines.append(f"- `{term}`: {', '.join(sorted(dialects))}")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        default="src/data/shortforms.json",
        help="Path to shortforms JSON.",
    )
    parser.add_argument("--json", dest="json_out", help="Path to JSON report output.")
    parser.add_argument("--report", dest="md_out", help="Path to Markdown report output.")
    args = parser.parse_args()

    data = _load_json(Path(args.path))
    report = _build_report(data)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(_render_markdown(report), encoding="utf-8")

    if not args.json_out and not args.md_out:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
