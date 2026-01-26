import sys
import os
sys.path.append(os.getcwd())
from scripts.tier1_grader import load_case_keywords, grade_submission

# Load Cases
cases = load_case_keywords('tests/fixtures/expanded_cases.json')

# Simulate a "Perfect" response for Case 2
case_id = '2'
case = cases[case_id]
perfect_response = case['reference_answer'] # "Macam mana nak buat ni? Aku dah cuba banyak kali tapi tak jadi."

print(f"--- Case {case_id} Analysis ---")
print(f"Expected Keywords ({len(case['expected_keywords'])}): {case['expected_keywords']}")
print(f"Response: {perfect_response}")

# Manual Grading Logic Trace
response_lower = perfect_response.lower()
expected = [k.lower() for k in case.get('expected_keywords', [])]
hits = [k for k in expected if k in response_lower]

print(f"Hits ({len(hits)}): {hits}")

ratio = len(hits) / len(expected)
score = 0.5 + (ratio * 0.5)

print(f"Calculated Score: {score:.2f}")
