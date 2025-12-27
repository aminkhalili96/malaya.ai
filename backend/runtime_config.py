import os
from pathlib import Path
from typing import Any, Dict

import yaml


def _runtime_path() -> Path:
    path = os.environ.get("MALAYA_RUNTIME_CONFIG", "config.runtime.yaml")
    return Path(path)


def load_runtime_config() -> Dict[str, Any]:
    path = _runtime_path()
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def save_runtime_config(payload: Dict[str, Any]) -> None:
    path = _runtime_path()
    data = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)
    path.write_text(data, encoding="utf-8")


def merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in (override or {}).items():
        merged[key] = value
    return merged
