# Malaya LLM - Sovereign AI Copilot

A **Malaysian-language AI chatbot** that understands Malay, Manglish, and Malaysian slang. This project enhances standard LLMs (like Qwen) with preprocessing, normalization, and cultural understanding layers.

## 🎯 Project Goals

1. **Handle Manglish/Slang**: Understand Malaysian shortforms like "xleh", "mcm mane", "xde duit"
2. **Language Mirroring**: Reply in the same language the user speaks
3. **Real-time Search**: Answer current events using Tavily web search
4. **Source Citation**: Provide 3-5 inline references for factual claims
5. **Sovereign Architecture**: Run entirely on local infrastructure

## ✨ New Features

| Feature | Description |
|:--------|:------------|
| 🎧 **Podcast Mode** | Paste any article URL → AI summarizes → Listen in Malaysian voice |
| 📍 **Smart Maps** | Rich interactive cards with ⭐ ratings, photos & AI signature dish descriptions |
| 🗺️ **Tourist Mode** | Get curated travel itineraries for Malaysian destinations |
| 📸 **Snap & Translate** | Upload photo of signboard/menu → Translate Chinese/Jawi/Tamil |
| ⚡ **Agent Mode** | Execute multi-step tasks automatically using LangGraph |
| 🧠 **Long-Term Memory** | AI remembers your preferences across sessions |
| ⚙️ **Custom Instructions** | ChatGPT-style personalization ("Call me Boss", "Answer in code") |
| 🎙️ **Real-Time Voice** | WebSocket-based voice chat with TTS responses |

---

## 🧠 How It Works

```
┌─────────────────────────────────────────────────────────┐
│                      User Query                         │
│              "xleh la bro, xde duit skrg"               │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  1. TEXT NORMALIZATION (232 shortforms dictionary)      │
│     "xleh" → "tak boleh"                                │
│     "xde" → "tiada"                                     │
│     "skrg" → "sekarang"                                 │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  2. LANGUAGE DETECTION                                  │
│     Detects: Malay / English / Manglish                 │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  3. HYBRID RAG SEARCH                                   │
│     - BM25 (keyword) + Vector (semantic)                │
│     - Tavily Web Search (real-time)                     │
│     - Domain filtering (block Reddit/Quora)             │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  4. LLM GENERATION (Qwen/GPT-4)                         │
│     - Language mirroring                                │
│     - Citation injection [1], [2], [3]                  │
│     - Malaysian personality ("vibe")                    │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    AI Response                          │
│  "Faham bro, takpe. Nanti bila dah ada duit kita       │
│   jumpa la. Ada apa-apa aku boleh tolong?"              │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Raw Qwen 3 vs Malaya LLM: Input/Output Comparison

### Why This Matters

Raw Qwen models struggle with Malaysian slang, particles, and cultural context. Our preprocessing + prompt engineering pipeline dramatically improves understanding.

---

### Side-by-Side Comparison

| # | Input | Raw Qwen 3 Output | Malaya LLM Output | Score |
|:-:|:------|:------------------|:------------------|:-----:|
| 1 | `xleh la bro, aku xde duit skrg. nnt la kita jmpa` | "Bro, aku faham, **enggak** ada duit..." ❌ Uses Indonesian | "Okay, aku faham yang kau takde duit sekarang, so tak boleh jumpa lagi." ✅ | 4→**5** |
| 2 | `mcm mane nk buat ni? aku dh try byk kali tp xjd` | "Hehe, entahlah nak. Cikgu ada tips?" ❌ Off-topic | "Ok, aku faham yang kau dah cuba banyak kali tapi masih tak jadi." ✅ | 3→**5** |
| 3 | `best gila siot benda ni!` | "Takut-takutlah nih! Tiap orang ada pilihan makanan..." ❌ Confused | "Nampaknya awak betul-betul teruja! Apa yang best sangat?" ✅ | 1→**5** |
| 4 | `lepak mamak jom, aku belanja teh tarik` | "Saya tahu tehatar enak di sana." ❌ Misspells | "Oh, nak lepak mamak? Best! Teh tarik on you, bila nak pergi?" ✅ | 3→**5** |
| 5 | `eh bro, that meeting how ah? client happy tak?` | "That meeting kena lah! Klient senang tak?" ❌ Awkward | "Client nampak happy je, puas hati dengan presentation." ✅ | 3→**5** |
| 6 | `geram betul la dengan service ni, lambat macam siput` | "Geram betul je la, service memang lambat." ⚠️ | "Nampaknya awak tak puas hati dengan servis lambat tu." ✅ Empathetic | 4→**5** |
| 7 | `jangan kacau aku, mengantuk gila lepas sahur` | "Faham tu. Kita nak beri istirahat." ⚠️ Unnatural | "Faham, lepas sahur memang mengantuk. Cuba rehat sekejap." ✅ | 4→**5** |

---

### Summary Scores

| Category | Raw Qwen 3 (14B) | Malaya LLM |
|:---------|:----------------:|:----------:|
| Shortforms | 3.5/5 | **5.0/5** |
| Particles | 1.7/5 | **4.7/5** |
| Cultural | 3.7/5 | **5.0/5** |
| Manglish | 3.0/5 | **4.7/5** |
| Sentiment | 4.0/5 | **5.0/5** |
| **Overall** | **3.2/5** | **4.8/5** |

> **+1.6 point improvement** with our preprocessing pipeline

---

## 🚀 Quick Start

### Prerequisites
- **Ollama**: Install from [ollama.ai](https://ollama.ai)
- **Node.js**: v18+ for frontend
- **Python**: 3.11+

### 1. (Optional) Pull the Qwen 3 Model for Ollama
```bash
ollama pull qwen3:14b
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start Backend
```bash
python3 -m uvicorn backend.main:app --reload --port 8000
```

### 4. Start Frontend
```bash
cd frontend && npm install && npm run dev
```

### 5. Or use the startup script (single command)
```bash
./start.sh
```

Optional dependency install:
```bash
INSTALL_DEPS=1 ./start.sh
```

**Backend**: http://localhost:8000 | **Frontend**: http://localhost:5173

> **Note**: The default model is GPT-4o, so set `OPENAI_API_KEY`. To run without API keys, switch `model.provider` to `ollama` in `config.yaml` and use a local model.

---

## 🧪 Testing

Run the evaluation suite:
```bash
python -m pytest tests/north_star_eval.py -v
```

Notes:
- Web-search integration tests require `TAVILY_API_KEY` and are skipped if it is not set.
- End-to-end chat tests require `OPENAI_API_KEY` and are skipped if it is not set.
- `grpcio` and `grpcio-status` are pinned in `requirements.txt` for DSPy/LiteLLM compatibility; update both together if you change them.

## 🧰 Models & Tools

The chat UI lets you:
- Switch models (installed Ollama models, custom Ollama model, GPT-4o, or GPT-4o mini).
- Toggle tools like web search and citations per request.
- Reopen prior conversations from the left sidebar (stored locally in the browser).

Notes:
- GPT models require `OPENAI_API_KEY`.
- Web search uses Tavily and requires `TAVILY_API_KEY`.
- Custom Ollama models must be pulled locally (e.g., `ollama pull llama3:8b`).
- The default provider is set in `config.yaml` (`model.provider`).
- To point to a remote Ollama server, set `OLLAMA_BASE_URL` (default is `http://localhost:11434`).
- Model inventory is fetched from `GET /api/chat/models` (Ollama `/api/tags` + OpenAI key check). If Ollama is offline, the UI will show it as unavailable.
- `/api/chat/voice` and `/api/chat/image` enforce payload size limits (override with `MAX_AUDIO_BYTES`, `MAX_IMAGE_BYTES`).
- Streaming chat defaults to on; set `VITE_STREAMING_CHAT=false` to disable.
- Limit frontend history payload with `VITE_HISTORY_LIMIT` (default 8).
- Backend also caps history with `CHAT_HISTORY_LIMIT` (default 10).
- Set `OFFLINE_MODE=true` to disable web search and force local model fallback.
- SQLite data lives at `MALAYA_DB_PATH` (default `data/malaya.db`).
- Attachments are supported via `attachments` in chat payloads (text files only; limits via `MAX_ATTACHMENT_CHARS`, `MAX_ATTACHMENTS`).
- Project memory can be fetched via `GET /api/chat/projects/{project_id}/memory`.
- Project memory can be reset via `DELETE /api/chat/projects/{project_id}/memory`.

API example:
```json
{
  "message": "Apa khabar?",
  "history": [],
  "model": { "provider": "ollama", "name": "qwen3:14b" },
  "tools": { "web_search": true, "citations": true },
  "project_id": "project-123"
}
```

Streaming endpoint:
- `POST /api/chat/stream` (SSE events: `meta`, `tool`, `sources`, `delta`, `done`)
Voice streaming:
- `POST /api/chat/voice/stream` (SSE events: `transcript`, `answer`, `audio`, `done`)
- `POST /api/chat/voice/stop/{session_id}` to interrupt

Operational endpoints:
- `GET /health` for readiness
- `GET /metrics` for Prometheus

## ✅ Deep Testing

Run the benchmark + core tests:

```bash
./scripts/run_deep_tests.sh
```

Reports are saved to `reports/benchmark_report.json` and `reports/benchmark_report.md`.

## 🧪 Testing Tiers

- Fast (schema + non-integration tests): `./scripts/run_fast_tests.sh`
- Regression (benchmarks + non-integration tests): `./scripts/run_regression_tests.sh`
- Deep (benchmarks + full tests): `./scripts/run_deep_tests.sh`

## 🧪 Prompt A/B Evaluation

- Variants: `docs/prompt_variants.yaml`
- Cases: `tests/fixtures/prompt_ab_cases.jsonl`
- Run: `python scripts/run_prompt_ab_eval.py`
- Outputs: `reports/prompt_ab_eval.json` + `reports/prompt_ab_eval.md`

## 🔐 API Keys & Rate Limits

- Set `API_KEYS_REQUIRED=true` and supply `MALAYA_API_KEYS` (JSON list of keys/roles/limits).
- Rate limits default to values in `config.yaml` under `rate_limits`.
- If you protect analytics, set `VITE_API_KEY` in the frontend to forward the header.
- Admin console endpoints allow runtime key/limit updates via `config.runtime.yaml`.
  Configure path via `MALAYA_RUNTIME_CONFIG`.

Admin console:
- Click the top-right sidebar icon to open the admin panel.
- Requires an admin API key (`VITE_API_KEY`) when key enforcement is enabled.

## 📦 Sharing & Exports

- Share links for chats/projects are created via `POST /api/chat/share`.
- Export JSON/Markdown from the sidebar menu (conversation) or project view.

## 🧠 Personalization

- Tone (`neutral|formal|casual`) and profile are sent with each request.
- Project instructions are stored per project and injected into prompts.
- Prompt variants can be selected globally (Settings) or per-project.

## 💬 Chat UX (Claude/ChatGPT-style)

- Streaming responses with a “Thinking” timeline and tool/source milestones.
- Message actions: copy, regenerate, edit & resend, retry, and feedback.
- Auto/Fast/Quality response modes (auto routes by message intent/size).
- Rich code block rendering with copy buttons.
- Conversation management: pin, rename, folders, tags, bulk actions, and semantic search toggle.
- Command palette (`⌘K`) for quick navigation.
- Project space: files + memory summary view in the sidebar.
- Attachment support for text files (per-message + project files).
- Latency badges (TTFB/Total/Backend) and request IDs for debugging.
- Alternate response diff view for quick comparison.

## 📈 Analytics

- Client-side events post to `POST /api/chat/analytics`.
- Disable analytics in the UI with `VITE_ANALYTICS_DISABLED=true`.

## 👍 Feedback

- Per-message thumbs up/down in the UI.
- Feedback tags + comments are stored via `POST /api/chat/feedback` (SQLite-backed).

## 🔒 Privacy & Retention

- Optional local PII redaction before saving to browser storage (Settings).
- Optional auto-retention window for local chats (Settings).
- Per-project memory scope, PII policy, and retention overrides.
- Project access can be restricted via runtime config `project_access` map (requires API keys).

## 🛡 Production Readiness

See `docs/production_grade.md` for lexicon governance, observability, and release checklist.

## 🏗 Architecture

| Component | Technology |
|:----------|:-----------|
| Frontend | React 19, Vite 7, Tailwind CSS v4 |
| Backend | FastAPI, LangChain, ChromaDB |
| LLM | Qwen 3 (14B) via Ollama / GPT-4 |
| Search | Tavily API (real-time web) |
| NLP | [Malaya](https://github.com/huseinzol05/Malaya) library |

---

## 📁 Key Files

```
├── src/
│   ├── chatbot/engine.py      # Main chatbot logic
│   ├── rag/retrieval.py       # Hybrid search (BM25 + Vector)
│   ├── summarization/         # Text normalization
│   ├── validation/benchmark.py # Malaysian benchmark suite
│   └── data/shortforms.json   # Malaysian slang + dialect + Gen-Z + ambiguous terms
│   └── data/shortforms.schema.json # Lexicon schema guardrails
├── docs/dialects.md           # Dialect catalog and activation checklist
├── docs/production_grade.md   # Production readiness guide
├── backend/
│   ├── main.py               # FastAPI app
│   └── routers/chat.py       # Chat endpoint with rate limiting
├── frontend/                 # React UI (Claude-style)
├── config.yaml               # System prompts & settings
├── scripts/run_deep_tests.sh # Deep testing harness
├── scripts/run_fast_tests.sh # Fast checks (schema + non-integration tests)
├── scripts/run_regression_tests.sh # Regression suite (benchmarks + tests)
└── tests/
    └── north_star_eval.py    # Comprehensive tests
```

---

## 📜 License

MIT
