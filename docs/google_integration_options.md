# Google Services Integration Options

## 1. Current Status
**✅ Google Maps Platform**
- **Integration Method**: Model Context Protocol (MCP) via `@modelcontextprotocol/server-google-maps`.
- **Status**: Integrated and configured in `config.yaml`.
- **Capabilities**: 
  - `maps_search_places` (Find places/food/businesses)
  - `maps_geocode` (Convert addresses to coordinates)
  - `maps_directions` (Route planning)
- **Keys**: `GOOGLE_MAPS_API_KEY` is present in `.env`.

**❓ Google Generic API**
- **Key**: `GOOGLE_API_KEY` is present in `.env`.
- **Status**: **Unused**. No code currently references this key. It is likely intended for Gemini API or Custom Search but dependencies are missing.

---

## 2. Potential Integrations

### A. Artificial Intelligence (Vertex AI / Google AI)
Powerful LLMs to replace or augment local Ollama models.
- **Gemini 1.5 Pro / Flash**: Best-in-class context window (1M+ tokens) and reasoning.
  - *Use Case*: Complex reasoning, large document analysis, multimodal inputs (images/video).
- **Imagen 3**: Image generation.
  - *Use Case*: Generating visual assets or diagrams.
- **Google Cloud Speech**:
  - *Use Case*: High-accuracy Speech-to-Text (STT) and premium Text-to-Speech (TTS) voices (e.g., Journey voices).

### B. Search & Knowledge
- **Google Custom Search API (Programmable Search Engine)**:
  - *Use Case*: Web search capability (alternative to Tavily) for retrieving real-time information.
- **YouTube Data API**:
  - *Use Case*: Searching and retrieving video transcripts/metadata for RAG.

### C. Workspace (Productivity)
Integration via MCP or LangChain toolkits.
- **Google Calendar**:
  - *Use Case*: Agent can check availability, schedule meetings, or remind you of events.
- **Gmail**:
  - *Use Case*: Draft emails, summarized unread messages.
- **Google Drive / Docs / Sheets**:
  - *Use Case*: RAG knowledge base. Agent can read internal documentation, logs, or project trackers directly from Drive.
  - *Use Case*: Log benchmark results directly to a Google Sheet.

### D. Cloud Infrastructure Services
- **Google Cloud Storage (GCS)**:
  - *Use Case*: Storing generated artifacts, logs, or user upload backups.
- **Google Cloud Run**:
  - *Use Case*: Deploying the `benchmark-tracker` or the main Chatbot API as a serverless container.
- **BigQuery**:
  - *Use Case*: Logging conversation analytics or benchmark metrics for SQL analysis.

---

## 3. Requirements to Proceed

To enable any of the above, I generally need the following from you:

### For Gemini (AI) / Custom Search
1.  **Enable APIs**: Go to Google Cloud Console > "APIs & Services" > Enable **"Vertex AI API"** or **"Google AI Studio"**.
2.  **Verify Key**: Ensure the `GOOGLE_API_KEY` in `.env` has permissions for "Generative Language API" (if using AI Studio) or "Vertex AI".

### For Workspace (Drive, Gmail, Calendar) / Cloud Storage / BigQuery
1.  **Service Account**: We need a dedicated Service Account, not just an API Key.
2.  **Credentials**: 
    - Create a Service Account in GCP Console.
    - Download the **JSON Key file**.
    - Place it in a secure location (e.g., `secrets/google-credentials.json`) and **add it to `.gitignore`**.
3.  **Scopes**: Enable specific APIs (e.g., "Google Drive API", "Gmail API") for that project.

### Recommended First Step
If you want to integrate **Gemini** (logic) or **Drive/Docs** (knowledge), please:
1.  Confirm if `GOOGLE_API_KEY` is from **Google AI Studio** or **GCP Vertex AI**.
2.  Let me know which specific service interests you most (e.g., "I want it to read my Google Docs").
