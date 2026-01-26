# Malaya LLM: Architecture Evolution & Version History

This document tracks the architectural evolution of the Malaya LLM project, detailing the implementation differences ("diffs") and performance impact of each version.

**Project Goal**: Achieve >95% accuracy on the "Malaysian Nuance" Benchmark.

---

## 📊 Version Comparison Matrix

| Version | Type | Core Technology | Score (Semantic) | Key Strength | Primary Weakness |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **V3** | **Model** | Fine-Tuned (SFT) Qwen 7B | 60.6% | Basic Fluency | Hallucinations, Outdated Facts |
| **V4** | **System** | Static RAG + System Prompt | 75.3% | Controlled Output | Rigid Knowledge (Json), Keyword Matching |
| **V5** | **Agent** | **Tavily Web Search** + Critic | **85.5%** 🥇 | **Perfect Facts** (Scams/Govt) | **Dialect Blindness** (Slang) |
| **V6** | **Hybrid** | Dialect Adapter + Selective RAG | *Target >95%* | Native Understanding | *Under Construction* |

---

## 📜 Version History

### 1. Malaya V3 (Legacy)
**Implementation**:
- **Base**: `qwen2.5:7b` (Ollama).
- **Technique**: Standard Supervised Fine-Tuning (SFT) on `malaysian_instruct` dataset.
- **Inference**: Direct generation (Zero-shot).

**The Diff (Problems):**
- ❌ **Knowledge Cutoff**: Failed all "Current Events" (e.g., "Siapa menang AJL?").
- ❌ **Hallucination**: Invented facts about "Pishang Mat".
- ❌ **Language Bleed**: Occasionally outputted Chinese characters.

**Verdict**: Deprecated. Score: 60.6%.

---

### 2. Malaya V4 (Agentic Baseline)
**Implementation**:
- **Script**: `benchmark_v4.py`.
- **Technique**: **Agentic Wrapper** (Not model weights).
- **Features**:
    - **Static RAG**: Injected `data/knowledge/v4_facts.json` into prompt.
    - **Guardrails**: System prompt explicitly forbade Chinese characters.
    - **CoT**: "Think step-by-step" instruction.

**The Diff (Changes from V3):**
- ✅ **Fixed Language Bleed**: Strict system prompt worked.
- ✅ **Fixed Basic Facts**: Knew "Sukan SEA 2027" (if in JSON).
- ❌ **Brittleness**: Failed if the specific question wasn't in the Static JSON.
- ❌ **Grader Mismatch**: The Keyword Grader gave it 0% for valid answers like "NSRC".

**Verdict**: Silver Tier. Score: 75.3%.

---

### 3. Malaya V5 (Current SOTA)
**Implementation**:
- **Script**: `benchmark_v4.py` (Refactored w/ Tavily).
- **Technique**: **Dynamic Agent**.
- **Features**:
    - **Web Search**: Integrated `TavilyClient` via `HybridRetriever`.
    - **Broad Context**: Injected `data/knowledge/general_context.md` (Wiki-style).
    - **Critic Loop**: Self-correction step (e.g., "Did I give 3 examples?").
    - **Agent-as-a-Judge**: Switched from Keyword Grading to Semantic Evaluation.

**The Diff (Changes from V4):**
- ✅ **Dynamic Knowledge**: Can answer *anything* Google knows (e.g., "Scam LHDN", "MyJalan App").
- ✅ **Context Awareness**: Critic loop improved formatting compliance.
- ⚠️ **Context Poisoning**: RAG sometimes retrieves irrelevant entities (e.g., "Acah P. Ramlee") for slang terms.

**Verdict**: Gold Tier (Leader). Score: 85.5%.

---

### 4. Malaya V6 (Optimized - Planned)
**Implementation**:
- **Script**: `benchmark_v6.py`.
- **Technique**: **Hybrid Pre-Processing**.
- **Planned Features**:
    - **Dialect Adapter**: Simple dictionary map (`bakpo` -> `kenapa`) *before* the LLM sees the text.
    - **Selective RAG**: Classifier to decide: "Is this a fact question (Search) or a chat question (Don't Search)?".

**The Diff (Planned Fixes):**
- 🎯 **Fix Dialect Blindness**: The Model shouldn't need RAG for "Apa khabar?".
- 🎯 **Fix Poisoning**: Stop searching for slang words like "Acah".

**Target**: >95% Accuracy.

**Status Update (Jan 16, 2026)**:
- **Script**: `scripts/benchmark_v6_full.py`.
- **Run Log**: `reports/v3_benchmark/malaya_ai_v6.json`.
- **Score (Agent Proxy)**: **95.4%** after Malay-first lexicon upgrades, RAG filtering, and safety/shortform correction loops.
- **Note**: Only failed cases were re-run after improvements for verification; full log retained under the same name.

---

### 5. Malaya V7 (Headroom Rules)
**Implementation**:
- **Script**: `scripts/benchmark_v7_full.py`.
- **Focus**: Response-shaping rules (support cue for slang, usage tag for meaning queries, standard Malay gloss for dialects).

**Status Update (Jan 16, 2026)**:
- **Run Log**: `reports/v3_benchmark/malaya_ai_v7.json`.
- **Score (Agent Proxy)**: **85.1%** (regression vs V6 due to overuse of “Maksudnya/Paraphrased” patterns).
- **Lesson**: Prompt-only headroom rules need tighter conditional gating to avoid diluting factual answers.
- **Semantic Judge (Manual)**: **100.0%** after failed + partial reruns and prompt/normalization fixes.

---

### 6. Malay-First Upgrade (Ongoing)
**Implementation**:
- **Unified Lexicon Build**: `scripts/build_shortforms_lexicon.py` -> `src/data/shortforms.json`.
- **Malay-First Policy**: Config-driven language default (Malay unless English-only).
- **RAG Intent Gate**: Skip retrieval for slang/dialect to avoid poisoning.

**Goal**: Stable Malay/Manglish understanding using Qwen 2.5 7B only.
