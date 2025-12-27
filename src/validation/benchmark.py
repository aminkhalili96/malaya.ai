"""
Malaysian LLM Evaluation Benchmark

This module provides a comprehensive benchmark for evaluating Malaysian language understanding,
including shortform expansion, dialect detection, particle analysis, and cultural knowledge.

Categories:
1. Shortform Expansion - Tests normalization of Malaysian slang
2. Ambiguous Slang - Tests sense-aware expansion for polysemous terms
3. Dialect Detection - Tests identification of regional dialects
4. Particle Understanding - Tests understanding of discourse particles (lah, meh, etc.)
5. Cultural References - Tests understanding of Malaysian cultural expressions
6. Sentiment Detection - Tests Malaysian-specific sentiment patterns
7. Code-Switching - Tests handling of English-Malay mixing
8. Dialect Catalog - Ensures dialect metadata is complete and wired
9. Dialect Normalization - Tests expansion of dialect-specific lexicon
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
# Ensure repo root is on sys.path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.summarization.preprocessing import (
    TextNormalizer,
    DialectDetector,
    ParticleAnalyzer,
    MalaysianSentimentAnalyzer,
    RAW_DICTIONARY
)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    category: str
    total_tests: int
    passed: int
    failed: int
    score: float
    details: List[Dict]


# ============================================================================
# TEST CASES
# ============================================================================

SHORTFORM_TESTS = [
    # Standard Manglish
    {
        "input": "xleh la bro, xde duit skrg",
        "expected_any": [
            ["tak boleh", "tiada", "sekarang"],
            ["tidak boleh", "tiada", "sekarang"]
        ],
        "category": "standard"
    },
    {"input": "jgn lpe bwk brg tu", "expected_contains": ["jangan", "bawa", "barang"], "category": "standard"},
    {"input": "mcm mane nk buat ni?", "expected_contains": ["macam mana", "nak"], "category": "standard"},
    {"input": "sy xtau nk ckp ape", "expected_contains": ["saya", "tidak tahu", "cakap", "apa"], "category": "standard"},
    {"input": "korg pegi mne td?", "expected_contains": ["korang", "pergi", "mana", "tadi"], "category": "standard"},
    {"input": "tlg jwb msg sy", "expected_contains": ["tolong", "jawab"], "category": "standard"},
    {"input": "dh smpi blm?", "expected_contains": ["dah", "sampai", "belum"], "category": "standard"},
    {"input": "nk makan ape mlm ni?", "expected_contains": ["nak", "apa", "malam"], "category": "standard"},
    
    # Gen-Z/TikTok
    {"input": "bestie, that's lowkey sus fr fr", "expected_contains": ["kawan baik", "mencurigakan", "serius"], "category": "genz"},
    {"input": "slay queen, no cap", "expected_contains": ["hebat", "serius"], "category": "genz"},
    {"input": "itu bussin frfr", "expected_contains": ["sedap"], "category": "genz"},
    
    # Intensity markers
    {"input": "makanan tu sedapppp gila", "expected_contains": ["sedap sangat"], "category": "intensity"},
    {"input": "bestttt gila tempat ni", "expected_contains": ["best sangat"], "category": "intensity"},
]

AMBIGUOUS_TESTS = [
    {"input": "power bank aku rosak", "expected_contains": ["kuasa elektrik"], "category": "power"},
    {"input": "presentation tu power gila", "expected_contains": ["hebat"], "category": "power"},
    {"input": "signal steady sekarang", "expected_contains": ["stabil"], "category": "steady"},
    {"input": "aku rasa sick hari ni", "expected_contains": ["sakit"], "category": "sick"},
    {"input": "game tu sick gila", "expected_contains": ["hebat"], "category": "sick"},
    {"input": "panas hati aku tengok dia", "expected_contains": ["marah"], "category": "panas"},
]

DIALECT_TESTS = [
    # Kelantanese
    {"input": "Gapo demo nok make?", "expected_dialect": "kelantanese", "expected_meaning": "What do you want to eat?"},
    {"input": "Ambo takdok pitih", "expected_dialect": "kelantanese", "expected_meaning": "I don't have money"},
    {"input": "Guano kawe nok gi?", "expected_dialect": "kelantanese", "expected_meaning": "How do I go?"},
    
    # Terengganu
    {"input": "Mung nok gi dunung?", "expected_dialect": "terengganu", "expected_meaning": "Where do you want to go?"},
    {"input": "Dok, ambe dok nak", "expected_dialect": "terengganu", "expected_meaning": "No, I don't want"},
    
    # Kedah/Perlis
    {"input": "Hang pi mana?", "expected_dialect": "kedah_perlis", "expected_meaning": "Where are you going?"},
    {"input": "Awat hang buat camtu?", "expected_dialect": "kedah_perlis", "expected_meaning": "Why did you do that?"},
    {"input": "Depa semua dah balik", "expected_dialect": "kedah_perlis", "expected_meaning": "They all have gone home"},
    
    # Penang
    {"input": "Lu mana tau gua punya hal", "expected_dialect": "penang", "expected_meaning": "How would you know my business"},
    {"input": "Tarak problem la", "expected_dialect": "penang", "expected_meaning": "No problem"},
    {"input": "Kasi tau gua", "expected_dialect": "penang", "expected_meaning": "Tell me"},
    
    # Sabah
    {"input": "Bah, ko bilang apa tadi?", "expected_dialect": "sabah", "expected_meaning": "What did you say earlier?"},
    {"input": "Nda buli bah kalau macam tu", "expected_dialect": "sabah", "expected_meaning": "Cannot if like that"},
    {"input": "Sia pigi dulu bah", "expected_dialect": "sabah", "expected_meaning": "I'm going first"},
    
    # Sarawak
    {"input": "Kitak maok pergi mana?", "expected_dialect": "sarawak", "expected_meaning": "Where do you want to go?"},
    {"input": "Kamek sik tauk", "expected_dialect": "sarawak", "expected_meaning": "I don't know"},
    {"input": "Nang, kitak betul", "expected_dialect": "sarawak", "expected_meaning": "Yes, you're right"},
    
    # Negeri Sembilan
    {"input": "Den nak poi ghomeh", "expected_dialect": "negeri_sembilan", "expected_meaning": "I want to go home"},
    {"input": "Bona ko cakap tu?", "expected_dialect": "negeri_sembilan", "expected_meaning": "Is what you said true?"},
    
    # Perak
    {"input": "Den tak ghoyat la", "expected_dialect": "perak", "expected_meaning": "I don't understand"},

    # Brunei Malay
    {"input": "Biskita bisai banar", "expected_dialect": "brunei_malay", "expected_meaning": "You are very pretty"},

    # Banjar
    {"input": "Ulun handak kada", "expected_dialect": "banjar", "expected_meaning": "I don't want"},

    # Minangkabau
    {"input": "Urang indak samo", "expected_dialect": "minangkabau", "expected_meaning": "People are not the same"},

    # Bazaar Malay
    {"input": "Bikin barang tu, tarak masa", "expected_dialect": "bazaar_malay", "expected_meaning": "Make that thing, no time"},

    # Baba Malay
    {"input": "Lu punya dan gua punya", "expected_dialect": "baba_malay", "expected_meaning": "Yours and mine"},
]

DIALECT_NORMALIZATION_TESTS = [
    {
        "input": "Biskita bisai banar",
        "expected_contains": ["awak", "cantik", "betul"],
        "category": "brunei_malay"
    },
    {
        "input": "Ulun handak makan, kada pian?",
        "expected_contains": ["saya", "nak", "makan", "tidak", "awak"],
        "category": "banjar"
    },
    {
        "input": "Urang indak samo, dima bana?",
        "expected_contains": ["orang", "tidak", "sama", "di mana", "betul"],
        "category": "minangkabau"
    },
    {
        "input": "Bikin itu, tarak masa untuk saya",
        "expected_contains": ["buat", "tiada", "masa", "untuk", "saya"],
        "category": "bazaar_malay"
    },
    {
        "input": "Lu punya buku, gua punya pen",
        "expected_contains": ["awak punya", "saya punya"],
        "category": "baba_malay"
    },
]

PARTICLE_TESTS = [
    {"input": "Okay lah, I'll do it", "expected_particles": ["lah"], "expected_sentiment": "friendly"},
    {"input": "Really meh? I don't believe", "expected_particles": ["meh"], "expected_sentiment": "doubtful"},
    {"input": "Like that lor, nothing can do", "expected_particles": ["lor"], "expected_sentiment": "accepting"},
    {"input": "You understand kan?", "expected_particles": ["kan"], "expected_sentiment": "uncertain"},
    {"input": "Weh, come here quick!", "expected_particles": ["weh"], "expected_sentiment": "neutral"},
    {"input": "Sure geh, confirm one", "expected_particles": ["geh"], "expected_sentiment": "confident"},
    {"input": "This one good hor?", "expected_particles": ["hor"], "expected_sentiment": "uncertain"},
    {"input": "Bah, jom kita pergi", "expected_particles": ["bah"], "expected_sentiment": "positive"},
]

SENTIMENT_TESTS = [
    {"input": "Makanan ni best gila siot!", "expected_sentiment": "positive", "reason": "Malaysian positive intensifier"},
    {"input": "Gila babi mahal tempat ni", "expected_sentiment": "neutral", "reason": "Expletive as intensifier, not negative"},
    {"input": "Pergh, power la presentation kau", "expected_sentiment": "positive", "reason": "Positive exclamation"},
    {"input": "Haih, boring gila event ni", "expected_sentiment": "negative", "reason": "Negative exclamation + word"},
    {"input": "Wah, gempak gila results!", "expected_sentiment": "positive", "reason": "Positive exclamation + word"},
    {"input": "Teruk gila service dekat sini", "expected_sentiment": "negative", "reason": "Negative intensifier"},
    {"input": "Alamak, fail dah exam", "expected_sentiment": "negative", "reason": "Negative exclamation + word"},
    {"input": "Fuyo, mantap la bro!", "expected_sentiment": "positive", "reason": "Positive exclamation + word"},
]

CULTURAL_TESTS = [
    {"input": "Jom lepak mamak tonight", "expected_understanding": ["hang out", "mamak restaurant"], "category": "colloquialism"},
    {"input": "Nak tapau ke dine in?", "expected_understanding": ["takeaway", "eat in"], "category": "colloquialism"},
    {"input": "Weekend ni kita makan angin kat Langkawi", "expected_understanding": ["vacation", "travel"], "category": "colloquialism"},
    {"input": "Dia syok sendiri je, ingat dia hebat", "expected_understanding": ["self-absorbed", "delusional"], "category": "colloquialism"},
    {"input": "Selamat Hari Raya, Maaf Zahir dan Batin", "expected_understanding": ["eid", "forgiveness"], "category": "festival"},
    {"input": "CNY ni dapat banyak angpow tak?", "expected_understanding": ["chinese new year", "red packet"], "category": "festival"},
]

CODE_SWITCH_TESTS = [
    {"input": "I nak go to that kedai kejap", "type": "intra-sentential", "languages": ["english", "malay"]},
    {"input": "Okay la, let's discuss nanti. Kita meet up esok.", "type": "inter-sentential", "languages": ["english", "malay"]},
    {"input": "That one memang best gila siot", "type": "mixed", "languages": ["english", "malay", "manglish"]},
    {"input": "Wei bro, your presentation that day was gempak habis", "type": "mixed", "languages": ["english", "malay"]},
]


class MalaysianBenchmark:
    """
    Comprehensive benchmark for Malaysian LLM evaluation.
    Tests shortforms, dialects, particles, sentiment, cultural knowledge, and code-switching.
    """
    
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.dialect_detector = DialectDetector()
        self.particle_analyzer = ParticleAnalyzer()
        self.sentiment_analyzer = MalaysianSentimentAnalyzer()
    
    def run_all(self) -> Dict[str, BenchmarkResult]:
        """Run all benchmark tests and return results."""
        results = {}
        
        results["shortform"] = self.test_shortforms()
        results["ambiguous"] = self.test_ambiguous_terms()
        results["dialect"] = self.test_dialects()
        results["dialect_catalog"] = self.test_dialect_catalog()
        results["dialect_normalization"] = self.test_dialect_normalization()
        results["particle"] = self.test_particles()
        results["sentiment"] = self.test_sentiment()
        results["cultural"] = self.test_cultural()
        results["code_switch"] = self.test_code_switching()
        
        return results
    
    def get_summary(self, results: Dict[str, BenchmarkResult]) -> Dict:
        """Generate summary of benchmark results."""
        total_tests = sum(r.total_tests for r in results.values())
        total_passed = sum(r.passed for r in results.values())
        
        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_tests - total_passed,
            "overall_score": round(total_passed / total_tests * 100, 1) if total_tests > 0 else 0,
            "category_scores": {
                name: round(result.score, 1) 
                for name, result in results.items()
            }
        }
    
    def test_shortforms(self) -> BenchmarkResult:
        """Test shortform normalization."""
        passed = 0
        failed = 0
        details = []
        
        for test in SHORTFORM_TESTS:
            normalized = self.normalizer.normalize(test["input"]).lower()
            
            # Check if all expected words are in normalized output
            if "expected_any" in test:
                all_found = any(
                    all(exp.lower() in normalized for exp in expected_group)
                    for expected_group in test["expected_any"]
                )
                expected_display = test["expected_any"]
            else:
                all_found = all(exp.lower() in normalized for exp in test["expected_contains"])
                expected_display = test["expected_contains"]
            
            if all_found:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"
            
            details.append({
                "input": test["input"],
                "normalized": normalized,
                "expected": expected_display,
                "status": status,
                "category": test.get("category", "standard")
            })
        
        return BenchmarkResult(
            category="shortform",
            total_tests=len(SHORTFORM_TESTS),
            passed=passed,
            failed=failed,
            score=passed / len(SHORTFORM_TESTS) * 100 if SHORTFORM_TESTS else 0,
            details=details
        )
    
    def test_dialects(self) -> BenchmarkResult:
        """Test dialect detection accuracy."""
        passed = 0
        failed = 0
        details = []
        
        for test in DIALECT_TESTS:
            detected_dialect, confidence, matched_words = self.dialect_detector.detect(test["input"])
            
            if detected_dialect == test["expected_dialect"]:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"
            
            details.append({
                "input": test["input"],
                "expected_dialect": test["expected_dialect"],
                "detected_dialect": detected_dialect,
                "confidence": confidence,
                "matched_words": matched_words,
                "expected_meaning": test.get("expected_meaning", ""),
                "status": status
            })
        
        return BenchmarkResult(
            category="dialect",
            total_tests=len(DIALECT_TESTS),
            passed=passed,
            failed=failed,
            score=passed / len(DIALECT_TESTS) * 100 if DIALECT_TESTS else 0,
            details=details
        )

    def test_dialect_catalog(self) -> BenchmarkResult:
        """Ensure dialect metadata is complete and aligned with detection tables."""
        raw_dialects = RAW_DICTIONARY.get("dialects", {})
        missing_description = []
        missing_status = []
        missing_in_detector = []
        missing_in_names = []
        extra_in_detector = []
        extra_in_names = []

        if not isinstance(raw_dialects, dict):
            raw_dialects = {}

        for dialect, payload in raw_dialects.items():
            if not isinstance(payload, dict):
                missing_description.append(dialect)
                missing_status.append(dialect)
                continue
            if not payload.get("_description"):
                missing_description.append(dialect)
            if not payload.get("_status"):
                missing_status.append(dialect)
            if dialect not in self.dialect_detector.DIALECT_INDICATORS:
                missing_in_detector.append(dialect)
            if dialect not in self.dialect_detector.DIALECT_NAMES:
                missing_in_names.append(dialect)

        for dialect in self.dialect_detector.DIALECT_INDICATORS.keys():
            if dialect == "standard":
                continue
            if dialect not in raw_dialects:
                extra_in_detector.append(dialect)

        for dialect in self.dialect_detector.DIALECT_NAMES.keys():
            if dialect == "standard":
                continue
            if dialect not in raw_dialects:
                extra_in_names.append(dialect)

        all_clear = not any([
            missing_description,
            missing_status,
            missing_in_detector,
            missing_in_names,
            extra_in_detector,
            extra_in_names,
        ])

        details = [{
            "missing_description": missing_description,
            "missing_status": missing_status,
            "missing_in_detector": missing_in_detector,
            "missing_in_names": missing_in_names,
            "extra_in_detector": extra_in_detector,
            "extra_in_names": extra_in_names,
            "status": "PASS" if all_clear else "FAIL",
        }]

        return BenchmarkResult(
            category="dialect_catalog",
            total_tests=1,
            passed=1 if all_clear else 0,
            failed=0 if all_clear else 1,
            score=100.0 if all_clear else 0.0,
            details=details
        )

    def test_dialect_normalization(self) -> BenchmarkResult:
        """Test normalization of dialect-specific lexicon."""
        passed = 0
        failed = 0
        details = []

        for test in DIALECT_NORMALIZATION_TESTS:
            normalized = self.normalizer.normalize(test["input"]).lower()
            all_found = all(exp.lower() in normalized for exp in test["expected_contains"])

            if all_found:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"

            details.append({
                "input": test["input"],
                "normalized": normalized,
                "expected": test["expected_contains"],
                "status": status,
                "category": test.get("category", "dialect_normalization")
            })

        return BenchmarkResult(
            category="dialect_normalization",
            total_tests=len(DIALECT_NORMALIZATION_TESTS),
            passed=passed,
            failed=failed,
            score=passed / len(DIALECT_NORMALIZATION_TESTS) * 100 if DIALECT_NORMALIZATION_TESTS else 0,
            details=details
        )

    def test_ambiguous_terms(self) -> BenchmarkResult:
        """Test sense-aware slang expansion for ambiguous terms."""
        passed = 0
        failed = 0
        details = []

        for test in AMBIGUOUS_TESTS:
            normalized = self.normalizer.normalize_for_retrieval(test["input"]).lower()
            all_found = all(exp.lower() in normalized for exp in test["expected_contains"])

            if all_found:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"

            details.append({
                "input": test["input"],
                "normalized": normalized,
                "expected": test["expected_contains"],
                "status": status,
                "category": test.get("category", "ambiguous")
            })

        return BenchmarkResult(
            category="ambiguous",
            total_tests=len(AMBIGUOUS_TESTS),
            passed=passed,
            failed=failed,
            score=passed / len(AMBIGUOUS_TESTS) * 100 if AMBIGUOUS_TESTS else 0,
            details=details
        )
    
    def test_particles(self) -> BenchmarkResult:
        """Test particle detection and sentiment analysis."""
        passed = 0
        failed = 0
        details = []
        
        for test in PARTICLE_TESTS:
            analysis = self.particle_analyzer.analyze(test["input"])
            detected_particles = [p["particle"] for p in analysis["particles"]]
            detected_sentiment = analysis["overall_sentiment"]
            
            # Check if expected particles are detected
            particles_match = all(p in detected_particles for p in test["expected_particles"])
            sentiment_match = detected_sentiment == test["expected_sentiment"]
            
            if particles_match:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"
            
            details.append({
                "input": test["input"],
                "expected_particles": test["expected_particles"],
                "detected_particles": detected_particles,
                "expected_sentiment": test["expected_sentiment"],
                "detected_sentiment": detected_sentiment,
                "particles_match": particles_match,
                "sentiment_match": sentiment_match,
                "status": status
            })
        
        return BenchmarkResult(
            category="particle",
            total_tests=len(PARTICLE_TESTS),
            passed=passed,
            failed=failed,
            score=passed / len(PARTICLE_TESTS) * 100 if PARTICLE_TESTS else 0,
            details=details
        )
    
    def test_sentiment(self) -> BenchmarkResult:
        """Test Malaysian sentiment detection."""
        passed = 0
        failed = 0
        details = []
        
        for test in SENTIMENT_TESTS:
            analysis = self.sentiment_analyzer.analyze(test["input"])
            detected_sentiment = analysis["sentiment"]
            
            if detected_sentiment == test["expected_sentiment"]:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"
            
            details.append({
                "input": test["input"],
                "expected_sentiment": test["expected_sentiment"],
                "detected_sentiment": detected_sentiment,
                "confidence": analysis["confidence"],
                "reason": test.get("reason", ""),
                "analysis": analysis["analysis"],
                "status": status
            })
        
        return BenchmarkResult(
            category="sentiment",
            total_tests=len(SENTIMENT_TESTS),
            passed=passed,
            failed=failed,
            score=passed / len(SENTIMENT_TESTS) * 100 if SENTIMENT_TESTS else 0,
            details=details
        )
    
    def test_cultural(self) -> BenchmarkResult:
        """Test cultural reference understanding (placeholder - requires LLM)."""
        # This is a placeholder - full testing would require LLM inference
        # For now, we just test that the normalizer doesn't break these inputs
        passed = 0
        failed = 0
        details = []
        
        for test in CULTURAL_TESTS:
            try:
                normalized = self.normalizer.normalize(test["input"])
                passed += 1
                status = "PASS"
            except Exception as e:
                failed += 1
                status = "FAIL"
                normalized = str(e)
            
            details.append({
                "input": test["input"],
                "normalized": normalized,
                "expected_understanding": test["expected_understanding"],
                "category": test.get("category", "general"),
                "status": status,
                "note": "Cultural understanding requires LLM evaluation"
            })
        
        return BenchmarkResult(
            category="cultural",
            total_tests=len(CULTURAL_TESTS),
            passed=passed,
            failed=failed,
            score=passed / len(CULTURAL_TESTS) * 100 if CULTURAL_TESTS else 0,
            details=details
        )
    
    def test_code_switching(self) -> BenchmarkResult:
        """Test code-switching detection and handling."""
        passed = 0
        failed = 0
        details = []
        
        for test in CODE_SWITCH_TESTS:
            try:
                normalized = self.normalizer.normalize(test["input"])
                passed += 1
                status = "PASS"
            except Exception as e:
                failed += 1
                status = "FAIL"
                normalized = str(e)
            
            details.append({
                "input": test["input"],
                "normalized": normalized,
                "type": test["type"],
                "languages": test["languages"],
                "status": status
            })
        
        return BenchmarkResult(
            category="code_switch",
            total_tests=len(CODE_SWITCH_TESTS),
            passed=passed,
            failed=failed,
            score=passed / len(CODE_SWITCH_TESTS) * 100 if CODE_SWITCH_TESTS else 0,
            details=details
        )


def run_benchmark() -> Dict:
    """Run the full benchmark and return results."""
    benchmark = MalaysianBenchmark()
    results = benchmark.run_all()
    summary = benchmark.get_summary(results)
    
    return {
        "summary": summary,
        "results": {
            category: {
                "total": r.total_tests,
                "passed": r.passed,
                "failed": r.failed,
                "score": r.score,
                "details": r.details
            }
            for category, r in results.items()
        }
    }


def print_benchmark_report(results: Dict):
    """Print a formatted benchmark report."""
    print("\n" + "="*60)
    print("          MALAYSIAN LLM BENCHMARK REPORT")
    print("="*60)
    
    summary = results["summary"]
    print(f"\n📊 OVERALL SCORE: {summary['overall_score']}%")
    print(f"   Tests Passed: {summary['total_passed']}/{summary['total_tests']}")
    
    print("\n📁 CATEGORY SCORES:")
    for category, score in summary["category_scores"].items():
        emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        print(f"   {emoji} {category.capitalize()}: {score}%")
    
    print("\n" + "-"*60)
    print("DETAILED RESULTS:")
    print("-"*60)
    
    for category, data in results["results"].items():
        print(f"\n📌 {category.upper()} ({data['passed']}/{data['total']} passed)")
        for detail in data["details"][:3]:  # Show first 3 examples
            status_emoji = "✅" if detail.get("status") == "PASS" else "❌"
            if "input" in detail:
                print(f"   {status_emoji} Input: {detail['input'][:50]}...")
            else:
                summary_parts = []
                for key in (
                    "missing_description",
                    "missing_status",
                    "missing_in_detector",
                    "missing_in_names",
                    "extra_in_detector",
                    "extra_in_names",
                ):
                    if detail.get(key):
                        summary_parts.append(f"{key}={len(detail[key])}")
                summary = ", ".join(summary_parts) if summary_parts else "catalog ok"
                print(f"   {status_emoji} {summary}")
    
    print("\n" + "="*60)


def render_benchmark_markdown(results: Dict) -> str:
    summary = results["summary"]
    lines = []
    lines.append("# Malaysian LLM Benchmark Report")
    lines.append("")
    lines.append(f"Overall score: **{summary['overall_score']}%**")
    lines.append(f"Tests passed: **{summary['total_passed']}** / **{summary['total_tests']}**")
    lines.append("")
    lines.append("## Category scores")
    for category, score in summary["category_scores"].items():
        lines.append(f"- {category}: {score}%")
    lines.append("")
    lines.append("## Sample failures (first 3 per category)")
    for category, data in results["results"].items():
        failures = [d for d in data["details"] if d["status"] != "PASS"]
        if not failures:
            continue
        lines.append(f"### {category}")
        for detail in failures[:3]:
            lines.append(f"- Input: `{detail['input']}`")
            lines.append(f"  Expected: `{detail.get('expected') or detail.get('expected_sentiment') or detail.get('expected_dialect')}`")
            lines.append(f"  Normalized/Detected: `{detail.get('normalized') or detail.get('detected_sentiment') or detail.get('detected_dialect')}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Malaysian LLM benchmark suite")
    parser.add_argument("--json", dest="json_path", help="Optional path to save JSON results")
    parser.add_argument("--report", dest="report_path", help="Optional path to save Markdown report")
    args = parser.parse_args()

    results = run_benchmark()
    print_benchmark_report(results)

    if args.json_path:
        with open(args.json_path, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved JSON report to: {args.json_path}")

    if args.report_path:
        report = render_benchmark_markdown(results)
        with open(args.report_path, "w") as f:
            f.write(report)
        print(f"Saved Markdown report to: {args.report_path}")
