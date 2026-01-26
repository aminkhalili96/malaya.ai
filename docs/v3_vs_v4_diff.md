# Malaya LLM: V3 vs V4 Architecture Compare

**Summary**: V3 was a **Model** (SFT weights). V4 is a **System** (Agentic Pipeline).

| Feature | Malaya V3 (Legacy) | Malaya V4 (New) |
| :--- | :--- | :--- |
| **Architecture** | **Static Model** (Fine-Tuned Weights) | **Agentic Pipeline** (Inference Wrapper) |
| **Knowledge Source** | Implicit (Stored in weights) | **Explicit** (RAG / Context Injection) |
| **Reasoning** | Direct Answer (Zero-Shot) | **Chain-of-Thought** (Internal Monologue) |
| **Dialect Handling** | Hope the model knows it | **Dynamic Few-Shot** (Teach on-the-fly) |
| **Hallucination** | High (Chinese/English bleeding) | **Low** (Restricted by System Prompt) |
| **Reliability** | ~60% (Beta) | **Target >95% (Platinum)** |

---

## 🛠️ The V4 Mechanics (How it works)

V4 is not just a model checkpoint. It is a run-time engine (`benchmark_v4.py`) that wraps a base model (Qwen 2.5 7B) with 3 layers of intelligence:

### 1. Pre-Processing (The "Teacher")
*   **Detector**: Scans input for keywords (e.g., "demo", "Anwar", "makan").
*   **Retrieval**: failed to find "Anwar" in weights? Look up `data/v4_knowledge_base.json`.
*   **Injection**: Adds `Context: Anwar Ibrahim is the 10th PM.` to the prompt.

### 2. Processing (The "Thinker")
*   **Steering**: Forces the model to think before speaking.
    *   *System*: "You are Malaya-V4. Think step-by-step in <thought> tags."
    *   *Reasoning*: "User said 'tokene'. My dictionary says 'tak kena'. I will reply 'tidak kena'."

### 3. Post-Processing (The "Filter")
*   **Guardrails**: If the output contains Chinese characters (Hanzi), reject and regenerate with penalty.

## Why this wins?
V3 relies on **Memorization** (which fails).
V4 relies on **Context** (which is always correct).
