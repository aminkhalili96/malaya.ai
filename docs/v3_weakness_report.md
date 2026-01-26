# Malaya V3 Gap Analysis & Weakness Report
**Date**: 2026-01-12
**Current Score**: ~60% (Agent Proxy)
**Target Score**: 95%

---

## 🚨 Critical Weaknesses (Why we are losing 40%)

### 1. Cross-Lingual Hallucination (Language Bleeding)
**Severity**: High
**Observation**: The model sometimes "Bleeds" into full Mandarin/Chinese characters or English when confused, losing the context of Malay/Manglish.
*   **The Nuance**: Valid Manglish *should* include Chinese loanwords (e.g., "Tapau", "Cincai", "Walao") but in **Rumi** (Romanized) script.
*   **The Failure**: The model outputs **Hanzi (Chinese Characters)** or full Mandarin sentences.
    *   *Case 40*: Input `maksud 'atuh' dalam bahasa sarawak apa?` -> Response: `"A吞乎"` (Chinese Characters - FAIL).
    *   *Case 54*: Input `universiti malaya world ranking berapa?` -> Response: Full Chinese paragraph (FAIL).
**Root Cause**: The base model (Qwen/Llama) associates Malaysia with a multilingual context but lacks the "Anchor" to stick to Rumi/Malay syntax unless explicitly asked.

### 2. Fact / Acronym Errors (Knowledge Gap)
**Severity**: High
**Observation**: The model confidently invents meanings for Malaysian acronyms.
*   **Case 55**: `PDPR` identified as **"Personal Data Protection Act"** (instead of *Pengajaran dan Pembelajaran di Rumah*).
*   **Case 32**: Refusal to identify the PM ("Saya tidak mempunyai maklumat..."), likely due to over-safety training or outdated knowledge cutoff.
**Root Cause**: Lack of Malaysian-specific "Knowledge Injection" in the post-training phase.

### 3. Dialect Misinterpretation (Tokenization Issue)
**Severity**: Medium
**Observation**: Valid dialect words are misread as English words due to spelling similarity.
*   **Case 8**: `demo tokene` (Kelantan: *awak tak kena*) -> Interpreted as **"Token Pricing/Economy"** (English).
**Root Cause**: Tokenizer splits dialect words into English subwords.

---

## 🗺️ Roadmap to 95% Accuracy (V4 Strategy)

To bridge the gap from 60% to 95%, we must move beyond simple SFT (Supervised Fine-Tuning).

### Phase 1: Data Hygiene (Quick Wins 10%)
*   [ ] **Filter Training Data**: Aggressively remove any Chinese/English instruction pairs that slipped into the Malay dataset.
*   [ ] **Synthetic Dialect Generation**: Use Gemini/GPT-4 to generate 5,000 pairs of high-quality Dialect <-> Standard Malay translations to fix the "Tokene" issue.

### Phase 2: RAG Integration (Fact Fix 15%)
*   [ ] **Hybrid RAG System**: Do not rely on the model's weights for facts.
    *   *Query*: "Siapa PM Malaysia?"
    *   *RAG*: Retreives `context: { PM: Anwar Ibrahim, Year: 2026 }`
    *   *Answer*: Accurate.
*   [ ] **Acronym Dictionary**: Hard-code or vector-index a dictionary of Malaysian acronyms (PDPR, PdP, PdP, SST).

### Phase 3: Alignment (Style Fix 10%)
*   [ ] **DPO (Direct Preference Optimization)**:
    *   Show the model two answers: one "Standard Malay Robot" and one "Natural Malaysian".
    *   Train it to prefer the Natural one.
    *   *Benefit*: Fixes the "Saya tidak faham" refusals.

### Phase 4: Tokenizer Patching (Advanced)
*   [ ] **Vocabulary Expansion**: Add specific Malaysian tokens (`xleh`, `aq`, `pishang`) to the tokenizer so they aren't split into English subwords.

---

## Estimated Impact

| Action | Est. Score Gain | New Total |
| :--- | :--- | :--- |
| **Current Baseline** | - | **60%** |
| + Clean Data | +10% | 70% |
| + RAG (Facts) | +15% | 85% |
| + DPO (Style) | +10% | **95%** |
