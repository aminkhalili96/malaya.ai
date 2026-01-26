# v2 Implementation Checklist

> **Purpose**: Granular task tracking for v2 implementation. Update this file as tasks complete.
> **Session**: If context is lost, read this file first to resume work.

---

## Session Handoff (For Next Agent Session)

| Field | Value |
|:------|:------|
| **Last Updated** | Jan 12, 2026 05:50 |
| **Current Phase** | ALL PHASES COMPLETE - Ready for Testing |
| **Current Task** | Implementation done, running benchmark |
| **Next Steps** | Run benchmark with Qwen 2.5 7B, save logs |
| **Blockers** | None |

---

## Phase 1: Smart Engine (Target: 95%+ Benchmark) ✅ COMPLETE

### P0: Dependencies & Setup ✅
- [x] Add `malaya` to `requirements.txt`
- [x] Add `faiss-cpu` to `requirements.txt`
- [x] Add `asyncio` (if not present) to `requirements.txt`
- [x] Run `pip install -r requirements.txt`
- [x] Test: `import malaya` works without error
- [x] Test: `import faiss` works without error

### P0: Input Pipeline (Shortforms + Safety) ✅
- [x] Import `malaya` in `src/chatbot/engine.py`
- [x] Create `src/chatbot/services/malaya_service.py` with MalayaService class
- [x] Add `normalize_text()` method using `malaya.normalizer`
- [x] Hook normalization into `process_query` before LLM call
- [x] Add `check_toxicity()` method using `malaya.toxicity`
- [x] Hook toxicity check into input pipeline (block if score > 0.7)

### P0: Async Pipeline Refactor ✅
- [x] `process_query` is already `async def`
- [x] v2 pipeline integrated into existing async flow

### P1: Vector RAG (FAISS) ✅
- [x] Create `src/rag/vector_service.py`
- [x] Initialize embedding model for Malay text
- [x] Create FAISS index for lexicon definitions
- [x] Load lexicon from `data/lexicon.json` (or create default with 20 terms)
- [x] Implement `search(query)` method returning top-k similar terms
- [x] Hook into RAG pipeline in engine (context injection)

### P1: Chain-of-Thought Prompting ✅
- [x] Update `config.yaml` system prompt with CoT instructions (Section 8)
- [x] Added step-by-step reasoning instructions for complex queries

### P1: Self-Consistency (Paraphraser) ✅
- [x] Add paraphrase method in `MalayaService.generate_paraphrases()`
- [x] Create `_v2_generate_query_variations()` helper in engine

### P2: Output Pipeline (Grammar + TrueCase) ✅
- [x] Add `correct_grammar()` method in MalayaService
- [x] Add `fix_capitalization()` method in MalayaService
- [x] Create `polish_output(text)` method combining both
- [x] Hook into output pipeline after LLM response

---

## Phase 2: Multimodal & Agents ✅ COMPLETE

### P0: Voice Input ✅
- [x] Add `malaya-speech` to `requirements.txt`
- [x] Create `src/chatbot/services/voice_service.py`
- [x] Implement `VoiceService` with ASR using malaya-speech
- [x] Implement `TextToSpeechService` with Edge TTS
- [x] Add `transcribe_audio()` method in engine
- [x] Add lazy-loading properties for voice services

### P1: Vision ✅
- [x] Create `src/chatbot/services/vision_service.py`
- [x] Implement `VisionService` with Ollama LLaVA/Qwen-VL support
- [x] Add `analyze_image()` method with description/question answering
- [x] Add `extract_text()` for OCR
- [x] Add `analyze_image()` method in engine
- [x] Add lazy-loading property for vision service

### P2: Tool Use / Function Calling ✅
- [x] Create `src/chatbot/services/tool_service.py`
- [x] Implement `ToolRegistry` for managing available tools
- [x] Add built-in tools: calculator, datetime, currency_convert, unit_convert
- [x] Implement `execute_tool_call()` method
- [x] Add lazy-loading property for tool service

### P3: User Memory ✅
- [x] Create `src/chatbot/services/user_memory_service.py`
- [x] Implement `UserMemory` class with facts, preferences, conversation summaries
- [x] Implement `UserMemoryService` with persistence to JSON
- [x] Add `get_user_context()` for LLM context injection
- [x] Add `extract_facts_from_message()` for auto-extraction
- [x] Add `user_id` parameter to `process_query()`
- [x] Integrate user memory injection into context building

---

## Verification Checklist

- [ ] Unit tests pass for all new modules
- [ ] Benchmark run completed (target: 95%+)
- [ ] Logs saved to `benchmark-tracker/logs/v2_benchmark_YYYYMMDD.log`
- [ ] No regression in existing functionality

---

## Files Modified/Created in v2

| File | Status | Description |
|:-----|:-------|:------------|
| `requirements.txt` | Modified | Added `faiss-cpu`, `malaya-speech` |
| `config.yaml` | Modified | Added `malaya_v2` + `v2_phase2` configs, CoT prompting |
| `config_7b.yaml` | Modified | Updated for v2 benchmark |
| `src/chatbot/engine.py` | Modified | Integrated all v2 services |
| `src/chatbot/services/malaya_service.py` | **NEW** | Malaya NLP wrapper (normalizer, toxicity, grammar) |
| `src/rag/vector_service.py` | **NEW** | FAISS vector search for lexicon |
| `src/chatbot/services/voice_service.py` | **NEW** | ASR/TTS services |
| `src/chatbot/services/vision_service.py` | **NEW** | Vision/VLM service |
| `src/chatbot/services/tool_service.py` | **NEW** | Function calling tools |
| `src/chatbot/services/user_memory_service.py` | **NEW** | User memory/personalization |
| `docs/v2_implementation_checklist.md` | **NEW** | This tracking file |

---

*Last Updated: Jan 12, 2026 05:50*
