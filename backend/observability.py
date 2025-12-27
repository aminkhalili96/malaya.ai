"""
Observability helpers: structured logging + Prometheus metrics.
"""

import json
import logging
import os
import time
import uuid
from typing import Optional
import re

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    PROM_AVAILABLE = True
except Exception:
    Counter = None
    Histogram = None
    generate_latest = None
    CONTENT_TYPE_LATEST = "text/plain; charset=utf-8"
    PROM_AVAILABLE = False
from starlette.responses import Response

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOGGER_NAME = os.environ.get("LOG_NAME", "malaya")

logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)


EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s\-()]{7,}\d)")


def redact_pii(value):
    if isinstance(value, str):
        value = EMAIL_PATTERN.sub("[redacted-email]", value)
        value = PHONE_PATTERN.sub("[redacted-phone]", value)
        return value
    if isinstance(value, list):
        return [redact_pii(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_pii(val) for key, val in value.items()}
    return value


RECENT_ERRORS = []
MAX_RECENT_ERRORS = 50


def record_error(event: str, payload: dict) -> None:
    RECENT_ERRORS.append({"event": event, **payload, "ts": time.time()})
    if len(RECENT_ERRORS) > MAX_RECENT_ERRORS:
        RECENT_ERRORS.pop(0)


class _NoopMetric:
    _metrics = {}

    def labels(self, *args, **kwargs):
        return self

    def inc(self, *args, **kwargs):
        return None

    def observe(self, *args, **kwargs):
        return None


REQUEST_COUNT = (
    Counter(
        "malaya_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )
    if PROM_AVAILABLE
    else _NoopMetric()
)
REQUEST_LATENCY = (
    Histogram(
        "malaya_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["path"],
    )
    if PROM_AVAILABLE
    else _NoopMetric()
)
CHAT_REQUESTS = (
    Counter(
        "malaya_chat_requests_total",
        "Total chat requests",
        ["endpoint"],
    )
    if PROM_AVAILABLE
    else _NoopMetric()
)
CHAT_ERRORS = (
    Counter(
        "malaya_chat_errors_total",
        "Total chat errors",
        ["endpoint", "error_type"],
    )
    if PROM_AVAILABLE
    else _NoopMetric()
)


def log_event(event: str, **fields) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=True))


def _counter_total(counter) -> float:
    try:
        return sum(metric._value.get() for metric in counter._metrics.values())
    except Exception:
        return 0.0


def metrics_snapshot() -> dict:
    return {
        "recent_errors": RECENT_ERRORS[-MAX_RECENT_ERRORS:],
        "requests_total": _counter_total(REQUEST_COUNT),
        "chat_requests_total": _counter_total(CHAT_REQUESTS),
        "chat_errors_total": _counter_total(CHAT_ERRORS),
    }


def metrics_response() -> Response:
    if not PROM_AVAILABLE or generate_latest is None:
        return Response(b"Prometheus metrics disabled.", media_type=CONTENT_TYPE_LATEST)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def attach_middleware(app) -> None:
    @app.middleware("http")
    async def observability_middleware(request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        status_code: Optional[int] = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            status_code = 500
            log_event(
                "http_error",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status=status_code,
                error_type=type(exc).__name__,
            )
            record_error(
                "http_error",
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "error_type": type(exc).__name__,
                },
            )
            raise
        finally:
            duration = time.perf_counter() - start
            REQUEST_COUNT.labels(request.method, request.url.path, status_code or 500).inc()
            REQUEST_LATENCY.labels(request.url.path).observe(duration)
            log_event(
                "http_request",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status=status_code or 500,
                duration_ms=round(duration * 1000, 2),
                client_ip=getattr(request.client, "host", None),
            )
