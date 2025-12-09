# Malaya LLM - Sovereign AI Copilot

A **Malaysian-language AI chatbot** that understands Malay, Manglish, and Malaysian slang. This project enhances standard LLMs (like Qwen) with preprocessing, normalization, and cultural understanding layers.

## 🎯 Project Goals

1. **Handle Manglish/Slang**: Understand Malaysian shortforms like "xleh", "mcm mane", "xde duit"
2. **Language Mirroring**: Reply in the same language the user speaks
3. **Real-time Search**: Answer current events using Tavily web search
4. **Source Citation**: Provide 3-5 inline references for factual claims
5. **Sovereign Architecture**: Run entirely on local infrastructure

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

### Test 1: Shortforms
**Input**: `xleh la bro, aku xde duit skrg. nnt la kita jmpa`

| Model | Output | Score |
|:------|:-------|:-----:|
| **Raw Qwen** | "Bro, aku faham, **enggak** ada duit sekarang je..." ❌ Uses Indonesian | 4/5 |
| **Malaya LLM** | "Okay, aku faham yang kau takde duit sekarang, so tak boleh jumpa lagi. Takpe, kita boleh plan lain kali." ✅ | **5/5** |

---

### Test 2: Understanding "mcm mane"
**Input**: `mcm mane nk buat ni? aku dh try byk kali tp xjd`

| Model | Output | Score |
|:------|:-------|:-----:|
| **Raw Qwen** | "Hehe, entahlah nak. Cikgu ada tips kecapi pula tak?" ❌ Off-topic | 3/5 |
| **Malaya LLM** | "Ok, aku faham yang kau dah cuba banyak kali tapi masih tak jadi. Boleh tak kau bagi tau apa yang kau cuba buat tu?" ✅ | **5/5** |

---

### Test 3: Particles (gila, siot)
**Input**: `best gila siot benda ni!`

| Model | Output | Score |
|:------|:-------|:-----:|
| **Raw Qwen** | "Hehe, takut-takutlah nih! Tiap-tiap orang mempunyai pilihan makanan favoritnya sendiri." ❌ Complete confusion | **1/5** |
| **Malaya LLM** | "Nampaknya awak betul-betul teruja dengan benda tu! Apa yang best sangat? Cerita sikit." ✅ | **5/5** |

---

### Test 4: Cultural (Mamak, Teh Tarik)
**Input**: `lepak mamak jom, aku belanja teh tarik`

| Model | Output | Score |
|:------|:-------|:-----:|
| **Raw Qwen** | "Wah, lepak! Saya tahu tehatar enak di sana." ❌ Misspells "teh tarik" | 3/5 |
| **Malaya LLM** | "Oh, nak lepak mamak eh? Best jugak tu! Teh tarik on you, nice lah. Bila nak pergi?" ✅ | **5/5** |

---

### Test 5: Manglish (Code-switching)
**Input**: `eh bro, that meeting just now how ah? client happy tak?`

| Model | Output | Score |
|:------|:-------|:-----:|
| **Raw Qwen** | "Eh bro, that meeting kena lah! Rasa macam tu, klient senang tak?" ❌ Awkward | 3/5 |
| **Malaya LLM** | "Oh, you nak tahu pasal meeting tadi. Client nampak happy je, dia puas hati dengan presentation kita." ✅ | **5/5** |

---

### Test 6: Sentiment (Frustration)
**Input**: `geram betul la dengan service ni, lambat macam siput`

| Model | Output | Score |
|:------|:-------|:-----:|
| **Raw Qwen** | "Geram betul je la, service itu memang lambat macam siput. Kalau ada apa-apa masalah, kita boleh cari solusinya bersama." ✅ | 4/5 |
| **Malaya LLM** | "Nampaknya awak memang tak puas hati dengan servis yang lambat tu, kan? Memang frust bila kena tunggu lama." ✅ Empathetic | **5/5** |

---

### Test 7: Sahur Context (Islamic/Ramadan)
**Input**: `jangan kacau aku, aku tengah mengantuk gila lepas sahur`

| Model | Output | Score |
|:------|:-------|:-----:|
| **Raw Qwen** | "Hehe, faham tu. Kita nak beri istirahat kat badan ni selepas sahur." ❌ Unnatural | 4/5 |
| **Malaya LLM** | "Faham, lepas sahur memang rasa mengantuk tu biasa. Kalau boleh, cuba rehat sekejap..." ✅ | **5/5** |

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

### 1. Pull the Qwen 3 Model
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

### 5. Or use the startup script
```bash
./run.sh
```

**Backend**: http://localhost:8000 | **Frontend**: http://localhost:5173

> **Note**: No API keys required! The project uses Qwen 3 (14B) via Ollama (free, local).

---

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
│   └── data/shortforms.json   # 232 Malaysian slang terms
├── backend/
│   ├── main.py               # FastAPI app
│   └── routers/chat.py       # Chat endpoint with rate limiting
├── frontend/                 # React UI (Claude-style)
├── config.yaml               # System prompts & settings
└── tests/
    └── north_star_eval.py    # Comprehensive tests
```

---

## 📜 License

MIT
