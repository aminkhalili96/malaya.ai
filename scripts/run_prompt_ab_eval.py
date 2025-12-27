import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.chatbot.engine import MalayaChatbot


def load_cases(path: Path):
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        cases.append(json.loads(line))
    return cases


def load_variants(config_path: Path, variants_path: Path):
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    base_prompt = config.get("system_prompts", {}).get("chatbot", "")
    variants_doc = yaml.safe_load(variants_path.read_text(encoding="utf-8")) or {}
    variants = variants_doc.get("variants", {}) or {}

    resolved = []
    for key, info in variants.items():
        suffix = info.get("suffix", "")
        prompt = base_prompt + ("\n\n" + suffix if suffix else "")
        resolved.append({
            "id": key,
            "description": info.get("description", ""),
            "prompt": prompt,
        })
    return resolved


def score_case(response: str, expected_keywords):
    if not response:
        return 0, []
    response_lower = response.lower()
    hits = [kw for kw in expected_keywords if kw.lower() in response_lower]
    return len(hits), hits


async def run_eval(variants, cases):
    results = []
    for variant in variants:
        bot = MalayaChatbot()
        if not bot.llm:
            return {
                "error": f"LLM unavailable: {bot.llm_error or 'not configured'}"
            }
        bot.config["system_prompts"]["chatbot"] = variant["prompt"]
        variant_scores = []
        for case in cases:
            response = await bot.process_query(case["query"])
            answer = response.get("answer", "")
            score, hits = score_case(answer, case.get("expected_keywords", []))
            variant_scores.append({
                "id": case.get("id"),
                "query": case.get("query"),
                "expected": case.get("expected_keywords", []),
                "hits": hits,
                "score": score,
                "answer": answer,
            })
        avg_score = sum(item["score"] for item in variant_scores) / max(len(variant_scores), 1)
        results.append({
            "variant": variant["id"],
            "description": variant.get("description", ""),
            "avg_score": round(avg_score, 2),
            "cases": variant_scores,
        })
    return {"results": results}


def write_reports(output_dir: Path, payload: dict):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "prompt_ab_eval.json"
    md_path = output_dir / "prompt_ab_eval.md"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    if "error" in payload:
        md_path.write_text(f"# Prompt A/B Eval\n\nError: {payload['error']}\n", encoding="utf-8")
        return

    lines = ["# Prompt A/B Eval", ""]
    for result in payload.get("results", []):
        lines.append(f"## Variant: {result['variant']}")
        if result.get("description"):
            lines.append(result["description"])
        lines.append(f"Average score: {result['avg_score']}")
        lines.append("")
        for case in result.get("cases", []):
            lines.append(f"- {case['id']}: {case['score']} hits ({', '.join(case['hits'])})")
        lines.append("")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--variants", default="docs/prompt_variants.yaml")
    parser.add_argument("--cases", default="tests/fixtures/prompt_ab_cases.jsonl")
    parser.add_argument("--output", default="reports")
    args = parser.parse_args()

    config_path = Path(args.config)
    variants_path = Path(args.variants)
    cases_path = Path(args.cases)

    variants = load_variants(config_path, variants_path)
    cases = load_cases(cases_path)

    payload = asyncio.run(run_eval(variants, cases))
    write_reports(Path(args.output), payload)


if __name__ == "__main__":
    main()
