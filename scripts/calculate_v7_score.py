import json
from pathlib import Path

def calculate_score():
    analysis_path = Path("reports/malaya_ai_v7_failure_analysis.json")
    if not analysis_path.exists():
        print(f"File not found: {analysis_path}")
        return

    with open(analysis_path, "r") as f:
        data = json.load(f)

    failures = data.get("failures", [])
    partials = data.get("partials", [])
    
    total_cases = 100  # Assumption based on other benchmarks
    
    non_perfect_count = len(failures) + len(partials)
    perfect_count = total_cases - non_perfect_count
    
    score_sum = perfect_count * 1.0
    
    for item in failures:
        score_sum += item.get("score", 0.0)
        
    for item in partials:
        score_sum += item.get("score", 0.0)
        
    accuracy = (score_sum / total_cases) * 100
    
    print(f"Total Cases: {total_cases}")
    print(f"Perfect Cases: {perfect_count}")
    print(f"Failures: {len(failures)}")
    print(f"Partials: {len(partials)}")
    print(f"Total Score: {score_sum:.2f}")
    print(f"Accuracy: {accuracy:.2f}%")

if __name__ == "__main__":
    calculate_score()
