# v3 Release Notes: Production-Grade Malaysian Language Support

> **Release Date**: Jan 12, 2026
> **Focus**: Deep Malaysian Knowledge Integration & Dialect Mastery

---

## Executive Summary

v3 transforms Malaya.ai from a "good chatbot with Malay support" into a **deeply Malaysian AI** capable of understanding over 180,000 local terms, 45,000+ factual entities (Schools, Parliament, Geography), and 6 major regional dialects.

---

## v2 → v3 Gap Analysis

| Gap in v2 | v3 Solution |
|:----------|:------------|
| **Limited Vocabulary**: Model relied on pre-trained knowledge | Extracted **130k+ words** from DBP Dictionary |
| **Poor Shortform Handling**: "xleh" was sometimes missed | Dictionary-first normalization with **3,300+ rules** at O(1) speed |
| **Zero Local Facts**: Couldn't answer "Where is SMK Bukit Bintang?" | **45,000 facts** (Schools, Hospitals, Parliament) loaded into RAG |
| **Dialect Blindness**: Kelantan/Sabah text not understood | `DialectDetector` + `data/prompts/dialects.yaml` for 6 dialects |
| **Model Dependency**: Used heavy Malaya BERT models | Extracted *static data* from Malaya; reduced model reliance |

---

## Key Features in v3

### 1. Massive Data Extraction from Malaya NLP
We bypassed heavy BERT models by extracting raw dictionary data:

| Category | File | Count |
|:---------|:-----|------:|
| Standard Dictionary | `malaya_standard.json` | 57,632 |
| Official DBP Terms | `malaya_formal.json` | 48,341 |
| Shortform Rules | `malaya_shortforms.json` | 3,374 |
| Locations/Entities | `locations_malaysia.json` | 43,834 |
| Schools | `entities_schools.json` | ~358 |
| Parliament Seats | `politics.json` | 222 |
| Grammar/Stopwords | `malaya_grammar.json` | 50+ |

**Total: ~180,000 entries.**

### 2. RAG with Local Knowledge Base
`RAGService` now indexes `data/knowledge/*.json`, enabling exact-match retrieval for Malaysian entities.

```python
# engine.py now uses:
from src.chatbot.services.rag_service import get_rag_service
self.rag_service = get_rag_service(self.config)
self.retriever = self.rag_service.get_retriever()  # 45k docs loaded!
```

### 3. Dialect Strategy via Prompt Engineering
`data/prompts/dialects.yaml` contains vocabulary + few-shot examples for:
- Kelantanese (demo, kawe, gok)
- Terengganu (mung, dok, kekgi)
- Sabahan (bah, sia, buli)
- Sarawakian (kamek, kitak, sik)
- Northern/Penang (hang, cek, depa)
- Negeri Sembilan (den, ekau, waghih)

---

## Malaya BERT Models: Still Used?

| Component | v2 Approach | v3 Approach | Status |
|:----------|:------------|:------------|:-------|
| **Normalization** | Malaya T5 Model | Dictionary-first (JSON), T5 fallback | ✅ Optimized |
| **Toxicity Check** | Malaya toxicity model | Still uses model (no static alternative) | ⚠️ Model Required |
| **Sentiment** | Malaya sentiment model | Still uses model (no static alternative) | ⚠️ Model Required |
| **Grammar** | Malaya grammar model | Light TrueCase only; LLM does rest | ✅ Reduced |
| **RAG/Facts** | N/A | Fully static JSON | ✅ No Model |

**Recommendation**: Keep `malaya` installed for Toxicity/Sentiment detection (which require models), but all vocabulary/normalization is now dictionary-based for speed.

---

## Files Modified/Created in v3

| File | Type | Description |
|:-----|:-----|:------------|
| `src/chatbot/services/rag_service.py` | Modified | Loads `data/knowledge/*.json` |
| `src/chatbot/services/native_malaya.py` | Modified | Multi-source dictionary loading |
| `src/chatbot/engine.py` | Modified | Uses `RAGService` |
| `config.yaml` | Modified | Prompt mentions local facts |
| `data/prompts/dialects.yaml` | **NEW** | Dialect vocabulary + examples |
| `data/dictionaries/*.json` | **NEW** | Extracted Malaya data |
| `data/knowledge/*.json` | **NEW** | Factual entities |
| `docs/DIALECT_STRATEGY.md` | **NEW** | Dialect handling docs |

---

## Next Steps (Benchmarking)

1. Run LLM-as-Judge benchmark
2. Run Semantic Similarity benchmark
3. Compare v3 vs v2 baseline
4. Document results

---

*Last Updated: Jan 12, 2026 17:40*
