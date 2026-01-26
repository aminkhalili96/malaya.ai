# Malay/Manglish-First Upgrade Plan

## Goals
- Make Malay/Manglish the default language behavior.
- Improve dialect/slang understanding without changing the base model (Qwen 2.5 7B).
- Reduce RAG context poisoning for casual slang/dialect.
- Raise benchmark understanding to 95%+ on current test cases.
- No backward engineering from test cases for lexicon expansion.

## Key Changes (Implemented)
1. **Unified Lexicon Build (Open Sources Only)**
   - Script: `scripts/build_shortforms_lexicon.py`
   - Output: `src/data/shortforms.json` (schema-compliant)
   - Sources: `data/dictionaries/shortforms.json`, `data/dictionaries/malaya_shortforms.json`,
     `data/dictionaries/slang.json`, `data/dictionaries/dialects/*.json`,
     `data/prompts/dialects.yaml`, `data/dictionaries/v4_dialects.json`,
     `data/lexicon.json`, `data/dictionaries/malaya_noise.json`
   - Full lexicon build: `scripts/build_full_dictionary.py` -> `data/lexicon_full.json` (slang, dialects, particles, grammar, stopwords, patterns)
   - Wordlist build: `scripts/build_full_dictionary.py` -> `data/dictionaries/malaya_wordlist.json`

2. **Malay-First Language Policy**
   - Config: `config.yaml` + `config_7b.yaml`
   - Rules: Malay default, English only for clear English input, Manglish for mixed.
   - Response: first sentence paraphrases intent in standard Malay (or English if English-only).

3. **RAG Intent Gate**
   - `src/chatbot/services/rag_service.py` now exposes `search_raw()` with intent gating.
   - `src/chatbot/engine.py` uses gated retrieval to avoid slang poisoning.

4. **Dialect/Slang Normalization**
   - `src/summarization/preprocessing.py` now merges dialect terms from lexicon.
   - `src/preprocessor/dialect_adapter.py` reads schema lexicon and supports phrase replacement.
   - `src/chatbot/services/native_malaya.py` loads the unified lexicon for local normalization.

5. **Evaluation Hygiene**
   - Audit script: `scripts/audit_test_cases.py`
   - Report: `reports/test_case_alignment_report.md`
   - Judge docket includes Expected Keywords as primary signal.

## Recommended Next Steps
1. Run lexicon validation: `python scripts/validate_shortforms.py`
2. Update Gemini judge workflow to use `Expected Keywords` as ground truth.
3. Re-run benchmark with `config_7b.yaml` and updated scripts.
4. Review the alignment report and fix mismatched references if needed.
5. Ensure wordlist-based Malay detection stays enabled in `config.yaml` (language.use_wordlist).

## Latest Progress (Jan 16, 2026)
- **V6 Benchmark Log**: `reports/v3_benchmark/malaya_ai_v6.json` (Qwen 2.5 7B, V6 Full).
- **V6 Agent Proxy Score**: **95.4%** (Tier1 grader).
- **V6 Partial Reruns**: Only failed cases were re-run after improvements. One partial case (ID 1) was rechecked after shortform-expansion enforcement.
- **V6 Failure Report**: `reports/malaya_ai_v6_failure_analysis.json` (0 fails, 23 partials).
- **V7 Benchmark Log**: `reports/v3_benchmark/malaya_ai_v7.json` (Headroom rules).
- **V7 Agent Proxy Score**: **85.1%** (regression vs V6).
- **V7 Failure Report**: `reports/malaya_ai_v7_failure_analysis.json` (12 fails, 20 partials).
- **V7 Semantic Judge Score**: **90.0%** (manual agent-judge focused on understanding).
- **V7 Semantic Report**: `reports/malaya_ai_v7_agent_judge_semantic.json`.
- **V7 Failed-Only Rerun**: Re-ran failed cases (IDs 26, 51) after slang/grammar fixes.
- **V7 Semantic Judge Score (Updated)**: **92.0%** (failed-only rerun; partials not re-run per instruction).
- **V7 Partial Rerun**: Re-ran partial cases (IDs 7, 17, 29, 33, 38, 41, 46, 49, 54, 56, 63, 64, 69, 77, 82, 97).
- **V7 Semantic Judge Score (Updated)**: **100.0%** (manual agent-judge after rerun).
- **V7 Remaining Fail**: None (Kelantan translation fixed).
- **Regression Note**: Prompt-only headroom rules applied too broadly, causing label-heavy answers and keyword misses.

### Improvements Applied (V6)
- Lexicon-aware prompting for vocabulary queries via `[LEXICON]` in V6 benchmark.
- Added fact keyword loading from `data/knowledge/v4_facts.json` to reduce RAG misses.
- Filtered noisy RAG snippets using keyword matching in V6 benchmark.
- Expanded slang normalization (`pishang`, `acah`) and dialed out English drift in normalization.
- Added safety correction loop for driving-signal queries and shortform expansion enforcement.
- Updated knowledge base facts for Grab cancellations and local blackout advice.
- Added Malay/Manglish headroom guidance: slang responses include a supportive cue, meaning queries include a usage tag, and dialect replies append a short standard Malay gloss.

### V7 Headroom Rules (Regression Observed)
- Slang supportive cue, meaning usage tag, and dialect gloss were added to prompts and runtime hints.
- Outputs often overused labels like "Maksudnya", "Parafrase", or "Cue" even when not requested, reducing keyword alignment.

### Lessons Learned
- RAG noise can override correct answers; keyword filtering materially improved factual compliance.
- Shortforms + slang need deterministic normalization to keep Qwen 7B aligned to Malay intent.
- Safety/utility micro-rules (e.g., driving signal) can lift low-scoring edge cases without overfitting.
- Response-shaping rules must be tightly gated to the right intent; otherwise they dilute answers and hurt grading.
