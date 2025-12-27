#!/usr/bin/env python3
"""
Validate the shortforms lexicon against schema + guardrails.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from jsonschema import Draft7Validator


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
ALLOWED_STATUS = {"active", "draft"}


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _collect_terms(block: dict) -> dict:
    return {k: v for k, v in block.items() if isinstance(k, str) and not k.startswith("_")}


def _validate_meta(meta: dict, errors: list, warnings: list) -> None:
    if not DATE_RE.match(meta.get("last_updated", "")):
        warnings.append("`_meta.last_updated` should be YYYY-MM-DD.")
    if not VERSION_RE.match(meta.get("version", "")):
        warnings.append("`_meta.version` should be semantic versioning (x.y.z).")


def _validate_dialects(dialects: dict, errors: list, warnings: list, min_terms: int) -> None:
    for name, payload in dialects.items():
        if not isinstance(payload, dict):
            errors.append(f"Dialect `{name}` should be an object.")
            continue
        status = payload.get("_status", "").lower()
        if status not in ALLOWED_STATUS:
            errors.append(f"Dialect `{name}` has invalid _status: {status!r}.")
        if not payload.get("_description"):
            errors.append(f"Dialect `{name}` missing _description.")
        terms = _collect_terms(payload)
        if status == "active" and len(terms) < min_terms:
            errors.append(
                f"Dialect `{name}` is active but has only {len(terms)} terms (min {min_terms})."
            )


def _validate_ambiguous(ambiguous: dict, errors: list) -> None:
    for term, payload in ambiguous.items():
        if term.startswith("_"):
            continue
        if not isinstance(payload, dict):
            errors.append(f"Ambiguous term `{term}` must be an object.")
            continue
        if not payload.get("default"):
            errors.append(f"Ambiguous term `{term}` missing default.")
        senses = payload.get("senses", [])
        if not isinstance(senses, list) or not senses:
            errors.append(f"Ambiguous term `{term}` missing senses list.")
            continue
        for idx, sense in enumerate(senses):
            if not isinstance(sense, dict):
                errors.append(f"Ambiguous term `{term}` sense {idx} must be an object.")
                continue
            if not sense.get("replacement"):
                errors.append(f"Ambiguous term `{term}` sense {idx} missing replacement.")
            keywords = sense.get("keywords", [])
            if not isinstance(keywords, list) or not keywords:
                errors.append(f"Ambiguous term `{term}` sense {idx} missing keywords.")


def _validate_categories(meta: dict, dialects: dict, errors: list) -> None:
    categories = set(meta.get("categories", []))
    missing = sorted([dialect for dialect in dialects.keys() if dialect not in categories])
    if missing:
        errors.append(
            "Missing dialects in `_meta.categories`: " + ", ".join(missing)
        )


def _find_overlaps(groups: dict) -> dict:
    term_map = defaultdict(list)
    for group, terms in groups.items():
        for term in terms:
            term_map[term].append(group)
    overlaps = {
        term: groups for term, groups in term_map.items() if len(groups) > 1
    }
    return overlaps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        default="src/data/shortforms.json",
        help="Path to shortforms JSON.",
    )
    parser.add_argument(
        "--schema",
        default="src/data/shortforms.schema.json",
        help="Path to JSON schema.",
    )
    parser.add_argument(
        "--min-active-terms",
        type=int,
        default=2,
        help="Minimum terms required for active dialects.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings as well as errors.",
    )
    args = parser.parse_args()

    data_path = Path(args.path)
    schema_path = Path(args.schema)

    data = _load_json(data_path)
    schema = _load_json(schema_path)

    errors = []
    warnings = []

    validator = Draft7Validator(schema)
    schema_errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    for err in schema_errors:
        path = ".".join(str(p) for p in err.path) or "root"
        errors.append(f"Schema error at {path}: {err.message}")

    meta = data.get("_meta", {})
    _validate_meta(meta, errors, warnings)

    dialects = data.get("dialects", {})
    _validate_dialects(dialects, errors, warnings, args.min_active_terms)
    _validate_categories(meta, dialects, errors)

    _validate_ambiguous(data.get("ambiguous_terms", {}), errors)

    # Overlap analysis (warning only)
    group_terms = {
        "shortforms": _collect_terms(data.get("shortforms", {})),
        "genz_tiktok": _collect_terms(data.get("genz_tiktok", {})),
        "intensity_markers": _collect_terms(data.get("intensity_markers", {})),
        "colloquialisms": _collect_terms(data.get("colloquialisms", {})),
    }
    for dialect_name, payload in dialects.items():
        group_terms[f"dialect:{dialect_name}"] = _collect_terms(payload)
    overlaps = _find_overlaps(group_terms)
    if overlaps:
        warnings.append(
            f"{len(overlaps)} overlapping terms across categories/dialects (see lexicon report)."
        )

    if errors:
        print("Lexicon validation failed:")
        for err in errors:
            print(f"- {err}")
    if warnings:
        print("Lexicon validation warnings:")
        for warn in warnings:
            print(f"- {warn}")

    if errors or (warnings and args.strict):
        return 1

    print("Lexicon validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
