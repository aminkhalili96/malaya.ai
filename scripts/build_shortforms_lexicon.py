#!/usr/bin/env python3
"""
Build unified Malay/Manglish lexicon for TextNormalizer.

Sources:
- data/dictionaries/shortforms.json
- data/dictionaries/malaya_shortforms.json
- data/dictionaries/slang.json
- data/dictionaries/dialects/*.json
- data/prompts/dialects.yaml
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

try:
    import yaml
except Exception:
    yaml = None


ROOT = Path(__file__).parent.parent
OUT_PATH = ROOT / "src" / "data" / "shortforms.json"

SHORTFORM_SOURCES = [
    ROOT / "data" / "dictionaries" / "shortforms.json",
    ROOT / "data" / "dictionaries" / "malaya_shortforms.json",
]

DIALECT_DIR = ROOT / "data" / "dictionaries" / "dialects"
DIALECT_PROMPT_PATH = ROOT / "data" / "prompts" / "dialects.yaml"
SLANG_PATH = ROOT / "data" / "dictionaries" / "slang.json"
V4_DIALECT_PATH = ROOT / "data" / "dictionaries" / "v4_dialects.json"
LEXICON_PATH = ROOT / "data" / "lexicon.json"
NOISE_PATH = ROOT / "data" / "dictionaries" / "malaya_noise.json"
WORDLIST_PATH = ROOT / "data" / "dictionaries" / "malaya_wordlist.json"


DIALECT_ALIASES = {
    "kelantan": "kelantanese",
    "kelantanese": "kelantanese",
    "terengganu": "terengganu",
    "penang": "penang",
    "negeri_sembilan": "negeri_sembilan",
    "sabah": "sabah",
    "sabahan": "sabah",
    "sarawak": "sarawak",
    "sarawakian": "sarawak",
    "northern": "kedah_perlis",
    "kedah_perlis": "kedah_perlis",
}


AMBIGUOUS_TERMS = {
    "_description": "Ambiguous slang/loanwords resolved by context keywords.",
    "power": {
        "default": "kuasa",
        "strategy": "append",
        "senses": [
            {"replacement": "hebat", "keywords": ["presentation", "persembahan", "performance", "best", "gempak", "padu"]},
            {"replacement": "kuasa", "keywords": ["bank", "powerbank", "charger", "cas", "charge"]},
        ],
    },
    "steady": {
        "default": "stabil",
        "strategy": "append",
        "senses": [
            {"replacement": "bagus", "keywords": ["job", "kerja", "ok", "baik"]},
            {"replacement": "stabil", "keywords": ["signal", "line", "internet", "coverage"]},
        ],
    },
    "sick": {
        "default": "sakit",
        "strategy": "append",
        "senses": [
            {"replacement": "hebat", "keywords": ["game", "presentation", "performance", "best", "gempak"]},
        ],
    },
    "on": {
        "default": "on",
        "strategy": "append",
        "senses": [
            {"replacement": "setuju", "keywords": ["korang", "kita", "jom", "join", "ikut", "set"], "strategy": "replace"},
        ],
    },
    "signal": {
        "default": "signal",
        "strategy": "append",
        "senses": [
            {"replacement": "signal telefon", "keywords": ["line", "internet", "celcom", "digi", "maxis", "tm", "unifi", "wifi", "5g", "4g"]},
            {"replacement": "signal kereta", "keywords": ["driver", "kereta", "jalan", "lane", "memandu", "lorry", "moto"]},
        ],
    },
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _load_wordlist() -> set:
    if not WORDLIST_PATH.exists():
        return set()
    try:
        data = _load_json(WORDLIST_PATH)
        return {str(word).lower() for word in data.get("words", []) if isinstance(word, str)}
    except Exception:
        return set()


def _merge_terms(target: Dict[str, str], source: Dict[str, str], override: bool = False) -> None:
    for key, value in source.items():
        if key.startswith("_"):
            continue
        if not override and key in target:
            continue
        target[key] = value


def _extract_shortforms(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    data = _load_json(path)
    items = data.get("shortforms", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return {}
    malay_wordlist = _load_wordlist()
    english_markers = {
        "too", "much", "bored", "crazy", "please", "thanks", "sorry",
        "dont", "don't", "cannot", "cant", "no", "yes", "what", "why",
        "when", "where", "who", "how", "with", "without", "hello",
    }
    mapping = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        short = item.get("short") or item.get("term")
        full = item.get("full") or item.get("definition") or item.get("meaning")
        if short and full:
            short_key = str(short).lower()
            full_text = str(full).strip()
            full_lower = full_text.lower()
            if malay_wordlist and short_key in malay_wordlist:
                if any(marker in full_lower.split() for marker in english_markers):
                    continue
            mapping[short_key] = full_text
    return mapping


def _extract_slang(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    data = _load_json(path)
    items = data.get("slang_terms", [])
    mapping = {}
    malay_wordlist = _load_wordlist()
    english_markers = {
        "too", "much", "bored", "crazy", "please", "thanks", "sorry",
        "dont", "don't", "cannot", "cant", "no", "yes", "what", "why",
        "when", "where", "who", "how", "with", "without", "hello",
    }
    slang_overrides = {
        "padu": "mantap",
        "gempak": "mantap",
        "terror": "mantap",
        "best": "bagus",
        "power": "mantap",
        "steady": "bagus",
        "pishang": "bosan",
        "koyak": "sentap",
    }
    for item in items:
        if not isinstance(item, dict):
            continue
        term = item.get("term")
        if not term:
            continue
        term = str(term).lower()
        if term in slang_overrides:
            mapping[term] = slang_overrides[term]
            continue
        meanings = item.get("meanings", [])
        if meanings:
            meaning_text = str(meanings[0]).strip()
            meaning_lower = meaning_text.lower()
            if malay_wordlist and term in malay_wordlist:
                if any(marker in meaning_lower.split() for marker in english_markers):
                    continue
            mapping[term] = meaning_text
            for similar in item.get("similar_terms", []) or []:
                if not similar:
                    continue
                similar_key = str(similar).lower()
                if malay_wordlist and similar_key in malay_wordlist:
                    continue
                if similar_key not in mapping:
                    mapping[similar_key] = mapping[term]
    return mapping


def _extract_noise(path: Path) -> Dict[str, str]:
    """Map noise tokens (laughter/emotes) to a normalized placeholder."""
    if not path.exists():
        return {}
    data = _load_json(path)
    mapping = {}
    for token in data.get("laughing", []):
        if token:
            mapping[str(token).lower()] = "haha"
    return mapping


def _extract_v4_dialects(path: Path):
    """Extract dialect and slang terms from v4_dialects.json (legacy map)."""
    if not path.exists():
        return {}, {}
    data = _load_json(path)
    dialect_terms: Dict[str, Dict[str, str]] = {}
    slang_terms: Dict[str, str] = {}
    for raw_name, terms in data.items():
        if not isinstance(terms, dict):
            continue
        if raw_name == "slang":
            for term, mapping in terms.items():
                clean = str(mapping).split('(')[0].strip()
                slang_terms[str(term).lower()] = clean
            continue
        dialect = DIALECT_ALIASES.get(raw_name, raw_name)
        dialect_terms.setdefault(dialect, {})
        for term, mapping in terms.items():
            clean = str(mapping).split('(')[0].strip()
            dialect_terms[dialect][str(term).lower()] = clean
    return dialect_terms, slang_terms


def _extract_lexicon(path: Path) -> Dict[str, str]:
    """Extract term->definition from lexicon.json."""
    if not path.exists():
        return {}
    data = _load_json(path)
    mapping = {}
    if isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                continue
            term = entry.get("term")
            definition = entry.get("definition")
            if term and definition:
                mapping[str(term).lower()] = str(definition).strip()
    return mapping


def _extract_dialects_from_files() -> Dict[str, Dict[str, str]]:
    dialects: Dict[str, Dict[str, str]] = {}
    if not DIALECT_DIR.exists():
        return dialects
    for path in sorted(DIALECT_DIR.glob("*.json")):
        data = _load_json(path)
        raw_name = data.get("dialect") or path.stem
        dialect = DIALECT_ALIASES.get(raw_name, raw_name)
        if dialect not in dialects:
            dialects[dialect] = {}
        for item in data.get("words", []):
            if not isinstance(item, dict):
                continue
            key = item.get("dialect_word")
            value = item.get("standard_malay")
            if key and value:
                dialects[dialect][str(key).lower()] = str(value).strip()
        for item in data.get("phrases", []):
            if not isinstance(item, dict):
                continue
            key = item.get("dialect_phrase")
            value = item.get("standard_malay")
            if key and value:
                dialects[dialect][str(key).lower()] = str(value).strip()
    return dialects


def _extract_dialects_from_prompt() -> Dict[str, Dict[str, str]]:
    if not DIALECT_PROMPT_PATH.exists() or not yaml:
        return {}
    payload = yaml.safe_load(DIALECT_PROMPT_PATH.read_text(encoding="utf-8"))
    dialects_data = payload.get("dialects", {}) if isinstance(payload, dict) else {}
    dialects: Dict[str, Dict[str, str]] = {}
    for raw_name, info in dialects_data.items():
        dialect = DIALECT_ALIASES.get(raw_name, raw_name)
        vocab = info.get("vocabulary", {}) if isinstance(info, dict) else {}
        if not isinstance(vocab, dict):
            continue
        dialects.setdefault(dialect, {})
        for key, value in vocab.items():
            if key and value:
                dialects[dialect][str(key).lower()] = str(value).strip()
    return dialects


def _build_dialect_entries(dialect_terms: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    entries = {}
    for dialect, terms in sorted(dialect_terms.items()):
        payload = {
            "_description": f"{dialect} dialect lexicon",
            "_status": "active",
            "_min_matches": 1,
        }
        payload.update(terms)
        entries[dialect] = payload
    return entries


def build_lexicon() -> dict:
    shortforms: Dict[str, str] = {}
    for source in SHORTFORM_SOURCES:
        _merge_terms(shortforms, _extract_shortforms(source))

    colloquialisms: Dict[str, str] = {}
    _merge_terms(colloquialisms, _extract_slang(SLANG_PATH))
    _merge_terms(colloquialisms, _extract_lexicon(LEXICON_PATH))
    _merge_terms(colloquialisms, _extract_noise(NOISE_PATH))

    dialect_terms = _extract_dialects_from_files()
    prompt_terms = _extract_dialects_from_prompt()
    for dialect, terms in prompt_terms.items():
        dialect_terms.setdefault(dialect, {})
        _merge_terms(dialect_terms[dialect], terms)
    v4_dialects, v4_slang = _extract_v4_dialects(V4_DIALECT_PATH)
    for dialect, terms in v4_dialects.items():
        dialect_terms.setdefault(dialect, {})
        _merge_terms(dialect_terms[dialect], terms)
    _merge_terms(shortforms, v4_slang)
    _merge_terms(colloquialisms, v4_slang)

    dialect_entries = _build_dialect_entries(dialect_terms)

    categories = [
        "shortforms",
        "dialects",
        "genz_tiktok",
        "intensity_markers",
        "colloquialisms",
        "ambiguous_terms",
    ] + sorted(dialect_entries.keys())

    lexicon = {
        "_meta": {
            "description": "Unified Malay/Manglish lexicon for normalization and dialect handling.",
            "source": "Merged from data/dictionaries + prompts/dialects.yaml",
            "version": "1.0.0",
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
            "categories": categories,
        },
        "shortforms": shortforms,
        "dialects": dialect_entries,
        "genz_tiktok": {
            "_description": "Gen-Z/TikTok style slang expansions.",
            "frfr": "serius",
            "sus": "mencurigakan",
            "slay": "hebat",
        },
        "intensity_markers": {
            "_description": "Intensity markers normalized for retrieval.",
            "gila": "sangat",
            "siot": "sangat",
            "bapak": "sangat",
        },
        "colloquialisms": colloquialisms,
        "ambiguous_terms": AMBIGUOUS_TERMS,
    }
    return lexicon


def main() -> int:
    lexicon = build_lexicon()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(lexicon, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote lexicon to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
