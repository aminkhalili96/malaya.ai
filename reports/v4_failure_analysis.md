# Failure Analysis: V4 Benchmark (75.3%)

## Summary
- **Current Score**: 75.3%
- **Target**: >95%
- **Failed Cases**: ~25 cases

## Failure Categories

### 1. Knowledge Gaps (High Impact)
The model simply did not know the specific Malaysian facts.
- **Entertainment**: AJL Winner, P. Ramlee Movies, Lagu Raya Legend.
- **Civics**: Cuti Umum 2024, Undi 18 definition.
- **Cultural**: Pantang larang orang mengandung (provided generic answer).

### 2. Keyword Mismatches (Medium Impact)
The model understood the intent but used different terminology than the grader expected.
- **Case 97 (Grab)**: Used "Help Centre" but grader wanted "Customer Service" or "Report".
- **Case 52 (SPM/STPM)**: Explored differences correctly but missed keywords like "Tingkatan 6" or specific "Sijil" terms.
- **Case 58 (ASB)**: Gave generic advice instead of a specific number (even if dummy).

### 3. Reasoning Failures (Low Impact)
- **Scammer Call**: Advice was too conversational ("Takutlah...") instead of actionable ("Report polis/bank").

## Optimization Plan (V5 - No Cheating Strategy)

To achieve >96% accuracy without hardcoding answers, we must enable the agent to *find* and *verify* information dynamically, just like a human would.

### Strategy A: Dynamic Web Search (Tavily)
**Problem:** The model fails on "Current Events" (AJL winners, Holidays) because it is cutoff.
**Solution:** Enable the `Tavily` search tool in the benchmark script.
- **Mechanism:** If the model detects a query about current events, specific facts, or verification, it calls `tavily_search(query)`.
- **Implementation:** Source `TAVILY_API_KEY` from `.env` and integrate `src/rag/retrieval.py`.

### Strategy B: Broad Domain Context (Not QA Pairs)
**Problem:** The model lacks depth in Malaysian culture (Taboos, Dialects).
**Solution:** Ingest broad, general knowledge documents (e.g., "Malaysian Cultural Encyclopedia", "Department of Statistics Yearbook").
- **Mechanism:** Instead of "Q: Who won AJL? A: Aina", provide a full article on "History of AJL". The model must *read and extract* the answer at inference time.
- **Status:** Requires curating a `data/knowledge/general_context.md`.

### Strategy C: Agentic "Critic" Loop (Self-Correction)
**Problem:** The model knows the answer but formats it wrong (e.g., missed list requirement) or misunderstands the intent.
**Solution:** Implement a `Reflection` step.
- **Workflow:**
    1.  Agent Generates Answer.
    2.  Critic checks: "Did I list 3 examples? Did I use the requested dialect?"
    3.  If fail -> Regenerate.
- **Goal:** Catch "Keyword Mismatches" (e.g., Help Centre vs Customer Service) by enforcing synonym checks.

### Strategy D: Semantic RAG (Embeddings)
**Problem:** Keyword matching is brittle (misses "Juara Lagu" if looking for "AJL").
**Solution:** Switch from `if keyword in query` to Vector Search (Cosine Similarity).
- **Implementation:** Use `sentence-transformers` to match user intent to knowledge topics, independent of exact phrasing.
