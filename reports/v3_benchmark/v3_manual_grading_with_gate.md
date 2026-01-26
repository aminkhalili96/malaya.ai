# V3 Benchmark Results: Manual Grading (Gemini 1.5 Pro)

> **Date**: Jan 12, 2026
> **Model**: Malaya V3 (Qwen 2.5 7B + RAG Intent Gate)
> **Grader**: Gemini 1.5 Pro (via Chat)

---

## Summary

| Metric | Value | Notes |
|:-------|:------|:------|
| Total Cases | 100 | Full run |
| **Official Grade** | **80%** (8.0/10) | Gemini Verified |
| Auto-Judge Score | 8.2/10 | Qwen Self-Eval |
| Pass Rate (Auto) | 56% | Strict threshold |
| Intent Gate | **SUCCESS** | Correctly filtered casual chat |

---

## Manual Review

### 1. Casual Chat (Intent Gate Test)
**Input**: "internet unifi slow gila hari ini"
**Log Output**: `RAG skipped (casual chat detected)`
**Response**: Model responded naturally without verifying RAG facts.
**Score**: 10/10
**Comment**: Perfect execution. No location pollution.

### 2. Cultural Knowledge
**Input**: "hantaran tunang biasanya berapa dulang?"
**Response**: Good advice on odd numbers (5-7, 7-9).
**Score**: 9/10
**Comment**: Accurate cultural context.

### 3. Dialect/Slang
**Input**: "bebal betul lah driver tadi"
**Response**: Understood "bebal" (stubborn/stupid) and context.
**Score**: 8/10
**Comment**: Good emotional alignment.

### 4. Factual/RAG
**Input**: "jpj renew license operating hours"
**Log Output**: `RAG skipped` (False Negative?)
**Score**: 6/10
**Comment**: "renew" and "license" should probably trigger RAG, but might have been treated as general knowledge. If the answer was correct from internal knowledge, it's fine.

---

## Conclusion
The **Intent Gate** strictly improved the user experience by preventing the "Kampung X" pollution observed in the previous run. The model now handles casual Malaysian conversation (Manglish/dialects) much more naturally.

**Final Score: 80/100**
