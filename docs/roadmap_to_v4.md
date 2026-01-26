# Roadmap to 95% Accuracy (Malaya LLM V4 - Inference Only)

**Goal**: Achieve "Platinum Tier" (>95%) without re-training (No SFT). Focus on Context, Prompting, and RAG.

---

## 🏗️ Strategy 1: Targeted RAG (The "Knowledge Injection")
*Solving: Facts, Acronyms, Dates*

**Expanded Approach**:
1.  **Fact Dictionary (JSONL)**:
    *   `{"entity": "PDPR", "desc": "Pengajaran dan Pembelajaran di Rumah"}`
    *   `{"entity": "PM Malaysia", "desc": "Anwar Ibrahim"}`
2.  **Retrieval Step**:
    *   Pre-scan input for precise entity matches.
    *   Inject concise context blocks into the System Prompt.
    *   *Result*: Model answers correctly because the answer is *in the prompt*.

## 🧠 Strategy 2: Dynamic Few-Shot Prompting (The "Context Teacher")
*Solving: Dialects (Tokene), Shortforms (xleh)*
*Replaces: SFT Fine-Tuning*

**Approach**: "Show, Don't Train"
1.  **Dialect Database**: maintain a database of 500+ dialect/slang terms and their Standard Malay meanings.
2.  **Dynamic Context Injection**:
    *   If input contains "demo" or "tokene", the system retrieves relevant examples.
    *   **Injected Prompt**:
        > User uses Kelantan dialect.
        > Examples: "Demo" -> "Awak", "Tokene" -> "Tak Kena", "Kawe" -> "Saya".
        > Use these mappings to understand the user.
3.  **Result**: The model uses In-Context Learning (ICL) to decipher the slang on the fly.

## 💭 Strategy 3: Chain-of-Thought (CoT) Steering
*Solving: Logic Failures, Misinterpretations*

**Approach**: "Internal Monologue"
1.  **Hidden Reasoning Step**:
    *   Force the model to output a `<thought>` block before the final answer.
    *   *Prompt Instruction*: "Analyze the user's intent and language style first. If dialect is detecting, translate mentaly to Standard Malay."
2.  **Example Flow**:
    *   **Input**: "Mung dop mari?"
    *   **CoT**: `<thought> User is speaking Terengganu dialect. "dop" means "tak", "mari" means "datang". Intent: Asking why I didn't come.</thought>`
    *   **Output**: "Maaf, saya tak dapat hadir..."

## 🛡️ Strategy 4: Logit/Grammar Constraints (The "Guardrails")
*Solving: Chinese/English Hallucinations*

**Approach**: "Hard Blocking"
1.  **Logit Bias / Suppression**:
    *   During inference, set the probability of **Chinese Unicode Ranges** (CJK Unified Ideographs) to `-Infinity`.
    *   *Result*: The model physically *cannot* output Chinese characters, forcing it to find the next best token (Malay/Latin).
2.  **Grammar Constrained Decoding**:
    *   Use a grammar file (GBNF) to restrict output structure if necessary (advanced).

---

## 🚀 Execution Plan (v4-inference)

| Phase | Strategy | Difficulty | Impact |
| :--- | :--- | :--- | :--- |
| **1** | **Logit Suppression** (No Chinese) | Low | +10% (Fixes Bleeding) |
| **2** | **Targeted RAG** (Facts) | Medium | +15% (Fixes Hallucination) |
| **3** | **Dynamic Prompting** (Dialects) | Medium | +10% (Fixes Tokenization) |

**Total Est. Gain**: +35% (Current 60% -> 95%) without touching weights.
