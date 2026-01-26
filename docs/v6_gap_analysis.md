# V6 Gap Analysis & Optimization Plan
**Current State:** Malaya V5 (85.5%)
**Target:** >95%
**Gap:** ~10% (10 Cases)

## 1. Failure Analysis (The "Last Mile")
The grader is now accurate (Agentic). The remaining failures are **Model Failures**, falling into two categories:

### A. Dialect Blindness (Severity: High)
The Qwen 7B model (even with RAG) fails to understand heavy regional slang/dialect.
- **Case 09:** `bakpo mung dop mari` (Why didn't you come)
    - *Model Response:* "Report to JKR..." (Hallucination)
    - *Cause:* Model sees "lubang" (implied/hallucinated) or matches "mari" to some RAG chunk.
- **Case 22:** `pishang mat` (Bored/Tired)
    - *Model Response:* "Pishang Mat is a traditional dance..."
    - *Cause:* RAG treats "Pishang" as a proper noun and fetches irrelevant cultural facts.

### B. Context Poisoning (Severity: Medium)
RAG is "too eager". It treats conversational fillers as search keywords.
- **Case 24:** `dia tu acah je` (He's just pretending)
    - *Model Response:* "Acah P. Ramlee is a pioneer..."
    - *Cause:* The keyword "Acah" exists in `general_context.md` (likely under P. Ramlee context), confusing the model.

---

## 2. Proposed V6 Architecture

To bridge the 95% gap, we must fix **Understanding** before **Retrieval**.

### Strategy 1: The "Dialect Adapter" (Pre-processing)
Before the query hits the RAG/LLM, we run it through a lightweight **Dialect Translator**.
- *Input:* "bakpo mung dop mari"
- *Translation:* "kenapa kamu tidak datang"
- *Mechanism:* Simple Dict Mapping + Few-Shot Prompting.

### Strategy 2: Selective RAG (Intent Classification)
Do not RAG everything.
- IF query is `greeting` OR `chit-chat` OR `opinion`: -> **Skip RAG** (Pure LLM).
- IF query is `fact` OR `current_event`: -> **Execute RAG**.

## 3. Implementation Plan

1.  **Create `data/dictionaries/dialect_map.json`**: A hardened mapping of common slang (pishang, acah, bakpo, mung) to standard Malay.
2.  **Update `hybrid_retriever.py`**: Add a `pre_process_query(text)` method.
3.  **Refine `general_context.md`**: Remove ambiguous keywords like "Acah" from P. Ramlee section if they cause collisions.
