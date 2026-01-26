# V3 Benchmark Results: Manual LLM-as-Judge Grading

> **Date**: Jan 12, 2026
> **Model**: Qwen 2.5 7B
> **Grader**: Claude Opus 4.5 (via Chat)

---

## Summary

| Metric | Value | Notes |
|:-------|:------|:------|
| Total Cases | 5 | Quick smoke test |
| Auto-Passed | 0 (0%) | Threshold: 0.6 |
| Avg LLM Judge (Auto) | 7.4/10 | Self-judged by Qwen |
| Avg Semantic | 0.5 | Missing reference answers |

---

## Manual Grading (LLM-as-Judge: Claude Opus 4.5)

### Case 1: Shortforms
| Field | Value |
|:------|:------|
| **Input** | "xleh la bro, aku xde duit skrg. nnt la kita jmpa" |
| **Expected Behavior** | Normalize to "tak boleh, aku tiada duit sekarang. nanti la kita jumpa", respond casually |
| **Response** | "Abang, jangan khawatir! Kalau tak ada duit sekarang, kita boleh jumpa lain kali. Ada banyak tempat yang dekat, macam Kampung Wan Lah..." |
| **Issue** | RAG injected irrelevant place names ("Kampung Wan Lah", "Sungai Lah") matching the particle "lah" |
| **Manual Score** | **5/10** |
| **Feedback** | Normalization worked ("tak boleh"). Tone is good. But RAG noise derailed the response into irrelevant location mentions. |

---

### Case 2: Shortforms
| Field | Value |
|:------|:------|
| **Input** | "mcm mane nk buat ni? aku dh try byk kali tp xjd" |
| **Expected Behavior** | Normalize to "macam mana nak buat ni? aku dah try banyak kali tapi tak jadi", ask for clarification |
| **Response** | "Could you please provide more details? Are you trying to create something related to Batang Kali, Kampung Tok Dah...?" |
| **Issue** | RAG matched "dah" -> "Kampung Tok Dah" which is nonsensical |
| **Manual Score** | **4/10** |
| **Feedback** | Model correctly asked for clarification (good intent), but RAG context poisoned the response with random locations. |

---

### Case 3: Sentiment
| Field | Value |
|:------|:------|
| **Input** | "best gila siot benda ni!" (Translation: "This thing is absolutely amazing!") |
| **Expected Behavior** | Recognize positive sentiment, respond enthusiastically |
| **Response** | "It seems like you're looking for the best 'Gila Siot Benda' in Kampung Parit Gila..." |
| **Issue** | RAG matched "gila" -> "Kampung Parit Gila". Model failed to recognize Manglish slang as an exclamation. |
| **Manual Score** | **3/10** |
| **Feedback** | Complete misunderstanding. "Gila" is slang for "crazy/amazing", not a location keyword. Sentiment system should have flagged this. |

---

### Case 4: Cultural
| Field | Value |
|:------|:------|
| **Input** | "lepak mamak jom, aku belanja teh tarik" (Translation: "Let's chill at the mamak, I'll treat you to teh tarik") |
| **Expected Behavior** | Recognize cultural invitation, respond warmly ("Ok jom!") |
| **Response** | "You're probably referring to going to the market or store to buy ingredients for making teh tarik..." |
| **Issue** | RAG matched "belanja" -> "Tanjung Belanja". Model misunderstood context (mamak is an Indian-Muslim restaurant, not a shopping trip). |
| **Manual Score** | **4/10** |
| **Feedback** | Should recognize "lepak mamak" as a cultural hang-out invitation. RAG noise led to wrong interpretation. |

---

### Case 5: Manglish
| Field | Value |
|:------|:------|
| **Input** | "eh bro, that meeting how ah? client happy tak?" |
| **Expected Behavior** | Respond in Manglish, "Ok la, client seems happy" |
| **Response** | "Eh, boleh jadi tu. Client Gembira mungkin nak bertemu di tempat yang berhubungan dengan nama 'Gembira'..." |
| **Issue** | RAG matched "gembira" (happy) -> "Kampung Gembira". Response confused an emotion with a location. |
| **Manual Score** | **4/10** |
| **Feedback** | Language mirroring OK (Manglish-ish). But semantic understanding derailed by RAG location injection. |

---

## Overall Manual Score

| Case | Auto Score | Manual Score |
|:-----|:-----------|:-------------|
| 1 | 7.4/10 | **5/10** |
| 2 | 7.4/10 | **4/10** |
| 3 | 7.4/10 | **3/10** |
| 4 | 7.4/10 | **4/10** |
| 5 | 7.4/10 | **4/10** |
| **Average** | 7.4/10 | **4.0/10** |

---

## Root Cause Analysis

### Primary Issue: **RAG Context Pollution**
The newly loaded **45,000 location facts** (Schools, Kampungs, etc.) are **too aggressively matched**:
- "lah" (particle) -> "Kampung Wan Lah"
- "dah" (already) -> "Kampung Tok Dah"
- "gila" (slang for amazing) -> "Kampung Parit Gila"
- "gembira" (happy) -> "Kampung Gembira"

The RAG retriever uses **BM25 keyword matching**, which naively matches any word, including particles, slang, and common words.

### Solution: **RAG Filter + Intent Classification**

1. **Blacklist common words from RAG**:
   - Particles: lah, meh, lor, kan, gok, mung, etc.
   - Slang: gila, siot, best, power, etc.
   - Stopwords: sudah, dah, tak, etc.

2. **Intent Classification First**:
   - Detect if query is a **location query** (e.g., "mana ada kedai") vs. **casual chat** (e.g., "best gila siot").
   - Only inject RAG context if intent is factual/location-seeking.

3. **Higher Retrieval Threshold**:
   - Require higher BM25 scores before injecting context.

---

## v3 Status

| Component | Status | Notes |
|:----------|:-------|:------|
| Data Extraction | ✅ Done | 180k+ entries |
| RAG Loading | ✅ Done | 45k docs indexed |
| Shortform Normalization | ✅ Working | 3,437 rules |
| Dialect Detection | ✅ Done | data/prompts/dialects.yaml |
| **RAG Filtering** | ❌ TODO | Needs stopword/slang blacklist |
| **Intent Classification** | ❌ TODO | Needed before RAG injection |

---

## Recommendation

Before full benchmark, implement **RAG Intent Gate**:
```python
# Pseudocode
if _is_factual_query(query):  # "where is SMK Damansara?"
    context = rag.search(query)
else:  # "best gila siot benda ni!"
    context = ""  # Don't pollute with locations
```

---

*Graded by: Claude Opus 4.5 via Chat | Jan 12, 2026*
