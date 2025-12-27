# Production Readiness

This document summarizes the guardrails and operational practices added to make Malaya LLM production grade.

## Lexicon Governance
- Schema: `src/data/shortforms.schema.json`
- Validator: `scripts/validate_shortforms.py`
- Coverage report: `scripts/lexicon_report.py` (writes to `reports/lexicon_report.*`)

Guardrails enforced
- All dialects must have `_description` and `_status`.
- Active dialects require a minimum term count (`--min-active-terms`, default 2).
- Ambiguous terms must include `default` and `senses`.
- Category list must include all dialect codes.

## Tiered Evaluation
Fast (PR-friendly):
```
./scripts/run_fast_tests.sh
```

Regression:
```
./scripts/run_regression_tests.sh
```

Deep (benchmarks + full tests):
```
./scripts/run_deep_tests.sh
```

Notes
- Integration tests are marked with `@pytest.mark.integration` and skipped in fast/regression.
- Deep tests include integration when credentials and network are available.
- CI runs fast checks on PRs and deep tests on a nightly schedule.

## Observability
Structured logs (JSON per line)
- `backend/observability.py` logs request + error events.
- Each response carries `X-Request-ID`.
- Set `LOG_LEVEL` to control verbosity (default `INFO`).
- Override logger name via `LOG_NAME` if needed.

Metrics
- `GET /metrics` exposes Prometheus metrics.
- Core series: `malaya_http_requests_total`, `malaya_http_request_duration_seconds`,
  `malaya_chat_requests_total`, `malaya_chat_errors_total`.

Latency instrumentation
- Backend response timings include `preprocess_ms`, `retrieval_ms`, `llm_ms`, `tool_ms`, and `total_ms`.
- Frontend captures TTFB + total latency and surfaces it in message metadata.

## Streaming + Tool UX
- `POST /api/chat/stream` emits SSE events (`meta`, `tool`, `sources`, `delta`, `done`).
- Frontend consumes streaming deltas and updates tool widgets as soon as tool payloads arrive.
- Set `VITE_STREAMING_CHAT=false` to disable streaming fallback.
- Claude/ChatGPT-style “Thinking” panel shows per-step progress, sources, and tools.

## Tool Safety
- Tool allowlist: `config.yaml` `tool_allowlist` (defaults to Maps tools).
- Tool input limits: `tool_arg_limits` caps string and array sizes.
- Tool arg validation uses MCP-provided JSON schema via `jsonschema`.
- Tool outputs are sanitized to strip prompt-injection patterns before LLM use.
- Parallel tool execution is controlled via `tool_policy.parallel`.
- Per-tool timeouts, budgets, and circuit breakers are enforced via `tool_policy`.

## Provenance Badges
- Sources are enriched with `type`, `trusted`, and `title`.
- UI renders badges under assistant messages for quick trust signals.

## Performance Guardrails
- MCP tool calls are cached in-memory (`tool_cache_ttl`, default 600s).
- Long chat history rendering is windowed with “Show earlier” to avoid DOM bloat.
- Response caching uses SQLite for identical prompts (`cache.response_*`).
- Tool caches persist across restarts (`MALAYA_DB_PATH`).
- Source snippets are truncated with `rag.source_snippet_chars` for UI stability.
- Web search circuit breaker avoids repeated Tavily failures (`rag.web_*`).

## Memory Summaries
- Per-project memory summaries are maintained server-side and injected into prompts.
- Config: `memory.summary_every`, `memory.max_recent_messages`, `memory.summary_max_chars`.
- Memory is persisted to SQLite for multi-session continuity.

## Evaluation Loop (Prompt A/B)
- Prompt variants live in `docs/prompt_variants.yaml`.
- Test cases in `tests/fixtures/prompt_ab_cases.jsonl`.
- Run: `python scripts/run_prompt_ab_eval.py` (writes to `reports/prompt_ab_eval.*`).

## API Keys & Rate Limits
- Optional API key gate: `API_KEYS_REQUIRED=true` and `MALAYA_API_KEYS` JSON.
- Keys map to roles with per-endpoint limits (`config.yaml` `rate_limits`).
- Rate limits are enforced by SlowAPI with dynamic role limits.
- Runtime overrides live in `config.runtime.yaml` (managed by Admin Console).

## Admin Console
- UI panel for metrics, errors, runtime keys, and rate limits.
- Backend endpoints: `/api/chat/admin/summary`, `/api/chat/admin/config`,
  `/api/chat/admin/keys`, `/api/chat/admin/rate-limits`.

## Sharing & Exports
- Share tokens are stored in SQLite with TTL (`/api/chat/share`).
- Sidebar exports conversations/projects to JSON or Markdown.

## Feedback Loop
- Per-message thumbs up/down capture quality signals in SQLite.
- Endpoint: `POST /api/chat/feedback` (rate-limited via `rate_limits.feedback`).
- UI supports feedback tags + comments to capture failure modes.

## Workspace UX
- Command palette (`⌘K`) for quick navigation.
- Conversation hygiene: pin, rename, tags, folders, and bulk actions.
- Project space includes file attachments and memory summaries.
- Source drawer opens all citations in one click.
- Auto/Fast/Quality response modes for latency-sensitive workflows.
- Semantic search toggle for recents.
- Rich code block rendering with copy buttons.
- Alternate response diff view for regeneration comparison.

## Attachments
- Per-message and project file attachments are supported for text files.
- Limits: `MAX_ATTACHMENT_CHARS`, `MAX_ATTACHMENTS` (enforced server-side).

## Privacy & Retention
- Optional PII redaction before persisting local data (Settings toggle).
- Optional auto-retention window for local chat history.
- Per-project memory scope, PII policy, and retention overrides.
- Project access control via runtime config `project_access` map (role-based).

## Offline Mode
- Set `OFFLINE_MODE=true` to disable web search and fallback to local models.

## Reliability UX
- Offline queues retry analytics and feedback when the client is back online.

## Error Monitoring
- Optional Sentry integration via `SENTRY_DSN`.
- Sampling via `SENTRY_TRACES_SAMPLE_RATE`.

## Release Checklist
1. Run `./scripts/run_regression_tests.sh`.
2. Review `reports/benchmark_report.md` + `reports/lexicon_report.md`.
3. Verify `/health` and `/metrics` endpoints in staging.
