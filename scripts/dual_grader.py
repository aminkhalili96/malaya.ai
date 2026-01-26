#!/usr/bin/env python3
"""
Dual Grader System for Malaya LLM Benchmark
============================================
Implements two grading styles:
1. Semantic Similarity (SentenceTransformers)
2. Keyword Match (Original)

Output: JSON with scores for each method
"""

import json
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

# Load model once
print("Loading SentenceTransformer model...")
EMBED_MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def score_keyword(response: str, expected_keywords: list, negative_keywords: list = None) -> float:
    """Original keyword matching (ANY match = 1.0)"""
    response_lower = response.lower()
    
    # Check negatives first
    if negative_keywords:
        if any(neg.lower() in response_lower for neg in negative_keywords):
            return 0.0
    
    # Check positives (ANY match = 1.0)
    if any(kw.lower() in response_lower for kw in expected_keywords):
        return 1.0
    return 0.0

def score_semantic(response: str, expected_keywords: list) -> float:
    """Semantic similarity between response and expected meaning"""
    if not response or not expected_keywords:
        return 0.0
    
    # Create expected meaning text
    expected_text = " ".join(expected_keywords)
    
    # Get embeddings
    resp_emb = EMBED_MODEL.encode(response, convert_to_tensor=True)
    exp_emb = EMBED_MODEL.encode(expected_text, convert_to_tensor=True)
    
    # Cosine similarity
    similarity = util.cos_sim(resp_emb, exp_emb).item()
    return max(0.0, min(1.0, similarity))  # Clamp to 0-1

def load_jsonl(filepath: str) -> list:
    """Load JSONL file"""
    results = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    results.append(json.loads(line))
                except:
                    pass
    return results

def load_test_cases(cases_path: str) -> dict:
    """Load test cases and create lookup"""
    with open(cases_path, 'r') as f:
        cases = json.load(f)
    return {c['id']: c for c in cases}

def grade_results(results: list, cases: dict) -> list:
    """Grade all results with both methods"""
    graded = []
    
    for result in results:
        case_id = result.get('id')
        if case_id not in cases:
            continue
            
        case = cases[case_id]
        response = result.get('output', '')
        expected = case.get('expected_keywords', [])
        negative = case.get('negative_keywords', [])
        
        # Score with both methods
        kw_score = score_keyword(response, expected, negative)
        sem_score = score_semantic(response, expected)
        
        graded.append({
            'id': case_id,
            'category': case.get('category', 'Unknown'),
            'input': case.get('input', '')[:50] + '...',
            'keyword_score': round(kw_score, 2),
            'semantic_score': round(sem_score, 2),
            'response_preview': response[:100] + '...' if len(response) > 100 else response
        })
    
    return graded

def main():
    ROOT = Path(__file__).parent.parent
    CASES_PATH = ROOT / 'tests/fixtures/expanded_cases.json'
    
    # Load test cases
    cases = load_test_cases(str(CASES_PATH))
    print(f"Loaded {len(cases)} test cases")
    
    # Grade specific log file (or accept as argument)
    if len(sys.argv) > 1:
        log_path = sys.argv[1]
    else:
        # Default to latest Malaya V2 log
        log_path = ROOT / 'reports/benchmark_competitor_gemma3_27b.jsonl'
    
    print(f"Loading results from: {log_path}")
    results = load_jsonl(str(log_path))
    print(f"Loaded {len(results)} results")
    
    # Grade
    graded = grade_results(results, cases)
    
    # Summary
    kw_avg = sum(g['keyword_score'] for g in graded) / len(graded) if graded else 0
    sem_avg = sum(g['semantic_score'] for g in graded) / len(graded) if graded else 0
    
    print("\n" + "="*60)
    print("DUAL GRADING RESULTS")
    print("="*60)
    print(f"Total Cases: {len(graded)}")
    print(f"Keyword Match Avg: {kw_avg:.2%}")
    print(f"Semantic Similarity Avg: {sem_avg:.2%}")
    print("="*60)
    
    # Print sample
    print("\nSample Results (First 10):")
    print("-"*80)
    for g in graded[:10]:
        print(f"Case {g['id']:3d} | KW: {g['keyword_score']:.2f} | SEM: {g['semantic_score']:.2f} | {g['category']}")
    
    # Save full results
    output_path = ROOT / 'reports/dual_grading_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'summary': {
                'total_cases': len(graded),
                'keyword_avg': round(kw_avg, 4),
                'semantic_avg': round(sem_avg, 4)
            },
            'results': graded
        }, f, indent=2)
    print(f"\nFull results saved to: {output_path}")

if __name__ == '__main__':
    main()
