# Malaya LLM: Dialect Handling Strategy

To achieve "Claude/ChatGPT-grade" Malaysian Language capability, we must handle the rich diversity of Malaysian dialects (loghat). Since raw dialect dictionaries are scarce or scattered, we employ a **Prompt Engineering + Few-Shot Learning** strategy, reinforced by our extracted knowledge base.

## 1. Supported Dialects
We actively support the following major dialects:
- **Kelantanese (Kelate)**: *gok, make, demo, kawe*
- **Terengganu (Ganu/Tranung)**: *dok, mung, kekgi*
- **Sabahan**: *bah, sia, buli, limpas*
- **Sarawakian**: *kamek, kitak, sik, nang*
- **Penang/Northern (Utaqa)**: *haghi, depa, kupang, ketaq*
- **Negeri Sembilan (Nogori)**: *den, ekau, waghih*

## 2. Implementation Strategy

### A. Detection 
The `DialectDetector` (in `src/summarization/preprocessing.py`) scans user input for unique dialect markers (e.g., "demo" -> Kelantan).
It now merges static indicators with the unified lexicon at `src/data/shortforms.json` for broader coverage.

### B. Prompt Injection (System Layer)
When a dialect is detected, we inject a specific "Persona Block" into the System Prompt. This instructs Qwen/LLM to:
1.  **Understand**: Mentally map the dialect words to Standard Malay.
2.  **Acknolwedge**: "Ah, oghe Kelate!" (build rapport).
3.  **Respond**:
    - **Default**: Standard Malay (for clarity/safety).
    - **Persona Mode**: Reply *in* the dialect (if requested).

### C. Knowledge Source
We rely on `data/prompts/dialects.yaml` which acts as a "Cheat Sheet" for the LLM, providing definitions and valid usage examples for each dialect.
Dialect terms are also normalized for retrieval via the unified lexicon build script.

## 3. Workflow
1.  **Input**: "Demo nak gi mano tuh?"
2.  **Detection**: `DialectDetector` identifies "Kelantanese" (words: *demo, mano*).
3.  **Prompting**: Engine appends `prompts/dialects.yaml/kelantanese` context.
4.  **Generation**: LLM generates: "Eh, kawe nak gi kedai jap. Demo nak kirim gapo?" (if dialect mode on) OR "Saya nak ke kedai sekejap." (standard).
