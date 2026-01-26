#!/usr/bin/env python3
"""
Malaya LLM V3 Benchmark Runner
Implements Dual-Grading: LLM-as-Judge + Semantic Similarity
"""

import json
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

# Configuration
MODEL_NAME = os.environ.get("BENCHMARK_MODEL", "qwen2.5:7b")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "qwen2.5:7b")  # Can be different for judging
LOG_DIR = ROOT_DIR / "reports/v3_benchmark"
CASES_FILE = ROOT_DIR / "tests/fixtures/expanded_cases.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class GradingResult:
    llm_judge_score: float = 0.0  # 0-10
    semantic_score: float = 0.0   # 0-1
    keyword_score: float = 0.0    # 0-1
    combined_score: float = 0.0   # Weighted average
    llm_judge_feedback: str = ""
    passed: bool = False

@dataclass
class BenchmarkCase:
    id: str
    category: str
    input_text: str
    expected_keywords: List[str] = field(default_factory=list)
    reference_answer: str = ""
    grading_criteria: str = ""

class V3Benchmark:
    def __init__(self):
        # Import services
        try:
            from src.chatbot.services.rag_service import get_rag_service
            from src.chatbot.services.native_malaya import NativeMalaya
            import ollama
            self.ollama = ollama
            self.malaya = NativeMalaya()
            self.rag = get_rag_service({})
            self._sentence_model = None
            logger.info("V3 Services loaded successfully")
        except ImportError as e:
            logger.error(f"Import failed: {e}")
            sys.exit(1)
    
    @property
    def sentence_model(self):
        """Lazy load sentence transformer for semantic similarity."""
        if self._sentence_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._sentence_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            except ImportError:
                logger.warning("SentenceTransformer not available, semantic scoring disabled.")
        return self._sentence_model

    def normalize(self, text: str) -> str:
        """Use v3 NativeMalaya normalization."""
        return self.malaya.normalize(text)
    
    def generate_response(self, query: str) -> str:
        """Generate response using the Chatbot Pipeline (simplified)."""
        # Normalize
        normalized = self.normalize(query)
        
        # Get RAG Context
        context = self.rag.search(normalized, k=3)
        
        # Build Prompt
        system_prompt = """You are Malaya.ai, a Malaysian AI Copilot. 
Answer in the user's language (Malay/English/Manglish).
Use the provided context if relevant. Be concise and helpful."""
        
        prompt = f"{system_prompt}\n\n[Context]\n{context}\n\n[User Query]\n{normalized}"
        
        # Generate
        try:
            response = self.ollama.chat(model=MODEL_NAME, messages=[
                {'role': 'user', 'content': prompt}
            ])
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return ""
    
    # --- GRADING METHODS ---
    
    def grade_keyword_match(self, response: str, keywords: List[str]) -> float:
        """Simple keyword matching score."""
        if not keywords:
            return 1.0
        response_lower = response.lower()
        matches = sum(1 for k in keywords if k.lower() in response_lower)
        return matches / len(keywords)
    
    def grade_semantic_similarity(self, response: str, reference: str) -> float:
        """Cosine similarity between response and reference answer."""
        if not self.sentence_model or not reference:
            return 0.5  # Neutral if unavailable
        try:
            embeddings = self.sentence_model.encode([response, reference])
            from numpy import dot
            from numpy.linalg import norm
            sim = dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
            return float(max(0, min(1, sim)))  # Clamp to [0, 1]
        except Exception as e:
            logger.warning(f"Semantic similarity failed: {e}")
            return 0.5
    
    def grade_llm_judge(self, query: str, response: str, criteria: str = "") -> Tuple[float, str]:
        """Use a separate LLM call to judge the response quality."""
        judge_prompt = f"""You are an expert evaluator for Malaysian AI responses.

Evaluate the following response on a scale of 0-10:
- 10: Perfect answer, accurate, culturally appropriate, correct language.
- 7-9: Good answer with minor issues.
- 4-6: Acceptable but with noticeable problems.
- 1-3: Poor quality, wrong info, or wrong language.
- 0: Completely wrong or harmful.

{f"Specific Criteria: {criteria}" if criteria else ""}

---
User Query: {query}

AI Response: {response}
---

Respond ONLY with a JSON object:
{{"score": <0-10>, "feedback": "<one sentence explanation>"}}
"""
        try:
            judge_response = self.ollama.chat(model=JUDGE_MODEL, messages=[
                {'role': 'user', 'content': judge_prompt}
            ])
            content = judge_response['message']['content']
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                score = float(parsed.get("score", 5))
                feedback = parsed.get("feedback", "")
                return min(10, max(0, score)), feedback
            return 5.0, "Could not parse judge response."
        except Exception as e:
            logger.warning(f"LLM Judge failed: {e}")
            return 5.0, f"Error: {e}"
    
    def grade_response(self, case: BenchmarkCase, response: str) -> GradingResult:
        """
        SKIP AUTO-GRADING. 
        Responses will be manually graded by Gemini 3 Pro / Opus 4.5 as per user request.
        """
        result = GradingResult()
        # Placeholder values
        result.keyword_score = 0.0
        result.semantic_score = 0.0
        result.llm_judge_score = 0.0
        result.llm_judge_feedback = "Manual Grading Pending"
        result.passed = False # Will be determined manually
        return result
    
    def run(self, max_cases: int = None):
        """Run the full benchmark."""
        logger.info(f"Starting V3 Benchmark with model: {MODEL_NAME}")
        
        # Load cases
        if not CASES_FILE.exists():
            logger.error(f"Cases file not found: {CASES_FILE}")
            return
        
        with open(CASES_FILE, 'r') as f:
            data = json.load(f)
            raw_cases = data if isinstance(data, list) else data.get("test_cases", [])
        
        cases = []
        for i, c in enumerate(raw_cases):
            cases.append(BenchmarkCase(
                id=c.get("id", str(i)),
                category=c.get("category", "general"),
                input_text=c.get("input", ""),
                expected_keywords=c.get("expected_keywords", []),
                reference_answer=c.get("reference_answer", ""),
                grading_criteria=c.get("grading_criteria", "")
            ))
        
        if max_cases:
            cases = cases[:max_cases]
        
        results = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = LOG_DIR / f"v3_benchmark_{timestamp}.json"
        
        for i, case in enumerate(cases):
            print(f"[{i+1}/{len(cases)}] {case.category}: {case.input_text[:50]}...")
            
            # Generate
            response = self.generate_response(case.input_text)
            
            # Grade
            grading = self.grade_response(case, response)
            
            result = {
                "id": case.id,
                "category": case.category,
                "input": case.input_text,
                "response": response,
                "grading": {
                    "keyword_score": round(grading.keyword_score, 3),
                    "semantic_score": round(grading.semantic_score, 3),
                    "llm_judge_score": round(grading.llm_judge_score, 1),
                    "llm_judge_feedback": grading.llm_judge_feedback,
                    "combined_score": round(grading.combined_score, 3),
                    "passed": grading.passed
                }
            }
            results.append(result)
            print(f"   - Combined: {grading.combined_score:.2f} | LLM: {grading.llm_judge_score}/10 | {'PASS' if grading.passed else 'FAIL'}")
        
        # Summary
        total = len(results)
        passed = sum(1 for r in results if r["grading"]["passed"])
        avg_combined = sum(r["grading"]["combined_score"] for r in results) / total if total else 0
        avg_llm = sum(r["grading"]["llm_judge_score"] for r in results) / total if total else 0
        avg_semantic = sum(r["grading"]["semantic_score"] for r in results) / total if total else 0
        
        summary = {
            "timestamp": timestamp,
            "model": MODEL_NAME,
            "judge_model": JUDGE_MODEL,
            "total_cases": total,
            "passed": passed,
            "pass_rate": round(passed / total * 100, 1) if total else 0,
            "avg_combined_score": round(avg_combined, 3),
            "avg_llm_judge_score": round(avg_llm, 1),
            "avg_semantic_score": round(avg_semantic, 3),
        }
        
        # Save Results
        output = {"summary": summary, "results": results}
        with open(log_file, 'w') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*50)
        print("V3 BENCHMARK SUMMARY")
        print("="*50)
        print(f"Model: {MODEL_NAME}")
        print(f"Total: {total} | Passed: {passed} ({summary['pass_rate']}%)")
        print(f"Avg Combined Score: {summary['avg_combined_score']}")
        print(f"Avg LLM Judge: {summary['avg_llm_judge_score']}/10")
        print(f"Avg Semantic Similarity: {summary['avg_semantic_score']}")
        print(f"Results saved to: {log_file}")
        print("="*50)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run V3 Benchmark")
    parser.add_argument("--max", type=int, default=None, help="Max cases to run (for quick testing)")
    args = parser.parse_args()
    
    bench = V3Benchmark()
    bench.run(max_cases=args.max)
