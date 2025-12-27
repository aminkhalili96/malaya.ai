"""
API key enforcement and dynamic rate limit helpers.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import yaml

from backend.runtime_config import load_runtime_config, merge_config
from fastapi import HTTPException, Request

DEFAULT_ROLE = "public"
DEFAULT_CHAT_LIMIT = "10/minute"
DEFAULT_VOICE_LIMIT = "5/minute"
DEFAULT_TTS_LIMIT = "10/minute"
DEFAULT_IMAGE_LIMIT = "5/minute"
DEFAULT_ANALYTICS_LIMIT = "60/minute"
DEFAULT_FEEDBACK_LIMIT = "30/minute"


def _load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    try:
        with open(config_path, "r") as handle:
            base = yaml.safe_load(handle) or {}
            runtime = load_runtime_config()
            return merge_config(base, runtime)
    except FileNotFoundError:
        return {}


def _load_api_keys(config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    config = config or _load_config()
    keys = config.get("api_keys", []) or []

    env_payload = os.environ.get("MALAYA_API_KEYS")
    if env_payload:
        try:
            parsed = json.loads(env_payload)
            if isinstance(parsed, list):
                keys = parsed
        except json.JSONDecodeError:
            pass

    return [key for key in keys if isinstance(key, dict) and key.get("key")]


def _normalize_limits(limits: Optional[Dict[str, str]]) -> Dict[str, str]:
    limits = limits or {}
    return {
        "chat": limits.get("chat", DEFAULT_CHAT_LIMIT),
        "voice": limits.get("voice", DEFAULT_VOICE_LIMIT),
        "tts": limits.get("tts", DEFAULT_TTS_LIMIT),
        "image": limits.get("image", DEFAULT_IMAGE_LIMIT),
        "analytics": limits.get("analytics", DEFAULT_ANALYTICS_LIMIT),
        "feedback": limits.get("feedback", DEFAULT_FEEDBACK_LIMIT),
    }


def _resolve_key_header(request: Request) -> Optional[str]:
    header = request.headers.get("X-API-Key")
    if header:
        return header.strip()
    auth = request.headers.get("Authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[-1].strip()
    return None


async def require_api_key(request: Request) -> None:
    required = os.environ.get("API_KEYS_REQUIRED", "false").lower() == "true"
    key_header = _resolve_key_header(request)

    config = _load_config()
    key_entries = _load_api_keys(config)
    key_map = {entry["key"]: entry for entry in key_entries}

    if not key_header and not required:
        request.state.api_role = DEFAULT_ROLE
        request.state.rate_limits = _normalize_limits(config.get("rate_limits"))
        return

    if not key_header or key_header not in key_map:
        raise HTTPException(status_code=401, detail="Missing or invalid API key.")

    entry = key_map[key_header]
    request.state.api_role = entry.get("role", DEFAULT_ROLE)
    request.state.rate_limits = _normalize_limits(entry.get("limits"))


def chat_rate_limit(request: Request) -> str:
    if hasattr(request.state, "rate_limits"):
        return request.state.rate_limits.get("chat", DEFAULT_CHAT_LIMIT)
    config = _load_config()
    key = _resolve_key_header(request)
    key_entries = _load_api_keys(config)
    key_map = {entry["key"]: entry for entry in key_entries}
    if key and key in key_map:
        return _normalize_limits(key_map[key].get("limits")).get("chat", DEFAULT_CHAT_LIMIT)
    return _normalize_limits(config.get("rate_limits")).get("chat", DEFAULT_CHAT_LIMIT)


def voice_rate_limit(request: Request) -> str:
    if hasattr(request.state, "rate_limits"):
        return request.state.rate_limits.get("voice", DEFAULT_VOICE_LIMIT)
    config = _load_config()
    key = _resolve_key_header(request)
    key_entries = _load_api_keys(config)
    key_map = {entry["key"]: entry for entry in key_entries}
    if key and key in key_map:
        return _normalize_limits(key_map[key].get("limits")).get("voice", DEFAULT_VOICE_LIMIT)
    return _normalize_limits(config.get("rate_limits")).get("voice", DEFAULT_VOICE_LIMIT)


def tts_rate_limit(request: Request) -> str:
    if hasattr(request.state, "rate_limits"):
        return request.state.rate_limits.get("tts", DEFAULT_TTS_LIMIT)
    config = _load_config()
    key = _resolve_key_header(request)
    key_entries = _load_api_keys(config)
    key_map = {entry["key"]: entry for entry in key_entries}
    if key and key in key_map:
        return _normalize_limits(key_map[key].get("limits")).get("tts", DEFAULT_TTS_LIMIT)
    return _normalize_limits(config.get("rate_limits")).get("tts", DEFAULT_TTS_LIMIT)


def image_rate_limit(request: Request) -> str:
    if hasattr(request.state, "rate_limits"):
        return request.state.rate_limits.get("image", DEFAULT_IMAGE_LIMIT)
    config = _load_config()
    key = _resolve_key_header(request)
    key_entries = _load_api_keys(config)
    key_map = {entry["key"]: entry for entry in key_entries}
    if key and key in key_map:
        return _normalize_limits(key_map[key].get("limits")).get("image", DEFAULT_IMAGE_LIMIT)
    return _normalize_limits(config.get("rate_limits")).get("image", DEFAULT_IMAGE_LIMIT)


def analytics_rate_limit(request: Request) -> str:
    if hasattr(request.state, "rate_limits"):
        return request.state.rate_limits.get("analytics", DEFAULT_ANALYTICS_LIMIT)
    config = _load_config()
    key = _resolve_key_header(request)
    key_entries = _load_api_keys(config)
    key_map = {entry["key"]: entry for entry in key_entries}
    if key and key in key_map:
        return _normalize_limits(key_map[key].get("limits")).get("analytics", DEFAULT_ANALYTICS_LIMIT)
    return _normalize_limits(config.get("rate_limits")).get("analytics", DEFAULT_ANALYTICS_LIMIT)


def feedback_rate_limit(request: Request) -> str:
    if hasattr(request.state, "rate_limits"):
        return request.state.rate_limits.get("feedback", DEFAULT_FEEDBACK_LIMIT)
    config = _load_config()
    key = _resolve_key_header(request)
    key_entries = _load_api_keys(config)
    key_map = {entry["key"]: entry for entry in key_entries}
    if key and key in key_map:
        return _normalize_limits(key_map[key].get("limits")).get("feedback", DEFAULT_FEEDBACK_LIMIT)
    return _normalize_limits(config.get("rate_limits")).get("feedback", DEFAULT_FEEDBACK_LIMIT)


def require_role(role: str):
    def _check_role(request: Request) -> None:
        current = getattr(request.state, "api_role", DEFAULT_ROLE)
        if current != role:
            raise HTTPException(status_code=403, detail="Insufficient role.")
    return _check_role
