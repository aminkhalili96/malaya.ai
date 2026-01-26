#!/usr/bin/env python3
"""
Build full Malay/Manglish lexicon and wordlist from local (Malaya) sources.

Outputs:
- data/lexicon_full.json
- data/dictionaries/malaya_wordlist.json
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).parent.parent
LEXICON_OUT = ROOT / "data" / "lexicon_full.json"
WORDLIST_OUT = ROOT / "data" / "dictionaries" / "malaya_wordlist.json"

SHORTFORMS_PATHS = [
    ROOT / "data" / "dictionaries" / "shortforms.json",
    ROOT / "data" / "dictionaries" / "malaya_shortforms.json",
]
SLANG_PATH = ROOT / "data" / "dictionaries" / "slang.json"
NOISE_PATH = ROOT / "data" / "dictionaries" / "malaya_noise.json"
DIALECT_DIR = ROOT / "data" / "dictionaries" / "dialects"
V4_DIALECT_PATH = ROOT / "data" / "dictionaries" / "v4_dialects.json"
PARTICLES_PATH = ROOT / "data" / "dictionaries" / "particles.json"
MANGLISH_PATTERNS_PATH = ROOT / "data" / "dictionaries" / "manglish_patterns.json"
LEGACY_LEXICON_PATH = ROOT / "data" / "lexicon.json"
MALAYA_GRAMMAR_PATH = ROOT / "data" / "dictionaries" / "malaya_grammar.json"
MALAYA_STOPWORDS_PATH = ROOT / "data" / "dictionaries" / "malaya_stopwords.json"

WORDLIST_SOURCES = [
    ROOT / "data" / "dictionaries" / "malaya_vocab.json",
    ROOT / "data" / "dictionaries" / "malaya_standard.json",
    ROOT / "data" / "dictionaries" / "malaya_formal.json",
]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _add_entry(entries: Dict[str, dict], term: str, definition: str, category: str, source: str):
    key = term.strip().lower()
    if not key:
        return
    if key in entries:
        return
    entries[key] = {
        "term": key,
        "definition": definition.strip(),
        "category": category,
        "source": source,
    }


def _build_shortforms(entries: Dict[str, dict]):
    for path in SHORTFORMS_PATHS:
        if not path.exists():
            continue
        data = _load_json(path)
        items = data.get("shortforms", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            short = item.get("short")
            full = item.get("full")
            if short and full:
                if len(str(short)) <= 1 and not str(short).isalpha():
                    continue
                definition = f"Shortform for '{full}'."
                _add_entry(entries, short, definition, "shortform", path.name)


def _build_slang(entries: Dict[str, dict]):
    if not SLANG_PATH.exists():
        return
    data = _load_json(SLANG_PATH)
    for item in data.get("slang_terms", []):
        if not isinstance(item, dict):
            continue
        term = item.get("term")
        meanings = item.get("meanings", [])
        examples = item.get("examples", [])
        synonyms = item.get("similar_terms", [])
        if not term or not meanings:
            continue
        meaning_text = "; ".join(str(m) for m in meanings if m)
        example_text = "; ".join(str(e) for e in examples[:2] if e)
        synonym_text = ", ".join(str(s) for s in synonyms if s)
        pieces = [f"Slang meaning: {meaning_text}."]
        if synonym_text:
            pieces.append(f"Synonyms: {synonym_text}.")
        if example_text:
            pieces.append(f"Examples: {example_text}.")
        _add_entry(entries, term, " ".join(pieces), "slang", SLANG_PATH.name)


def _build_noise(entries: Dict[str, dict]):
    if not NOISE_PATH.exists():
        return
    data = _load_json(NOISE_PATH)
    for token in data.get("laughing", []):
        if token:
            _add_entry(entries, token, "Laughter or casual expression.", "noise", NOISE_PATH.name)


def _build_particles(entries: Dict[str, dict]):
    if not PARTICLES_PATH.exists():
        return
    data = _load_json(PARTICLES_PATH)
    for item in data.get("particles", []):
        if not isinstance(item, dict):
            continue
        particle = item.get("particle")
        functions = ", ".join(item.get("functions", []))
        if particle and functions:
            definition = f"Particle functions: {functions}."
            _add_entry(entries, particle, definition, "particle", PARTICLES_PATH.name)


def _build_manglish_patterns(entries: Dict[str, dict]):
    if not MANGLISH_PATTERNS_PATH.exists():
        return
    data = _load_json(MANGLISH_PATTERNS_PATH)
    for item in data.get("patterns", []):
        if not isinstance(item, dict):
            continue
        pattern = item.get("pattern")
        meaning = item.get("meaning")
        example = ""
        examples = item.get("examples", [])
        if examples:
            example = str(examples[0])
        if pattern and meaning:
            definition = f"Manglish pattern meaning: {meaning}."
            if example:
                definition += f" Example: {example}."
            _add_entry(entries, pattern, definition, "manglish_pattern", MANGLISH_PATTERNS_PATH.name)


def _build_grammar(entries: Dict[str, dict]):
    if MALAYA_GRAMMAR_PATH.exists():
        data = _load_json(MALAYA_GRAMMAR_PATH)
        for category, terms in data.items():
            if not isinstance(terms, list):
                continue
            for term in terms:
                if not term:
                    continue
                definition = f"Malay grammar term ({category.replace('_', ' ')})."
                _add_entry(entries, term, definition, f"grammar:{category}", MALAYA_GRAMMAR_PATH.name)

    if MALAYA_STOPWORDS_PATH.exists():
        data = _load_json(MALAYA_STOPWORDS_PATH)
        for term in data.get("stopwords", []):
            if term:
                _add_entry(entries, term, "Malay stopword.", "stopword", MALAYA_STOPWORDS_PATH.name)


def _build_dialects(entries: Dict[str, dict]):
    if DIALECT_DIR.exists():
        for path in sorted(DIALECT_DIR.glob("*.json")):
            data = _load_json(path)
            dialect = data.get("dialect") or path.stem
            for item in data.get("words", []):
                if not isinstance(item, dict):
                    continue
                term = item.get("dialect_word")
                standard = item.get("standard_malay")
                english = item.get("english", "")
                if term and standard:
                    definition = f"Dialect ({dialect}) for '{standard}'."
                    if english:
                        definition += f" English: {english}."
                    _add_entry(entries, term, definition, f"dialect:{dialect}", path.name)
            for item in data.get("phrases", []):
                if not isinstance(item, dict):
                    continue
                term = item.get("dialect_phrase")
                standard = item.get("standard_malay")
                english = item.get("english", "")
                if term and standard:
                    definition = f"Dialect phrase ({dialect}) meaning '{standard}'."
                    if english:
                        definition += f" English: {english}."
                    _add_entry(entries, term, definition, f"dialect:{dialect}", path.name)

    if V4_DIALECT_PATH.exists():
        data = _load_json(V4_DIALECT_PATH)
        for dialect, terms in data.items():
            if not isinstance(terms, dict):
                continue
            category = "slang" if dialect == "slang" else f"dialect:{dialect}"
            for term, meaning in terms.items():
                definition = f"{category} term meaning '{str(meaning).split('(')[0].strip()}'."
                _add_entry(entries, term, definition, category, V4_DIALECT_PATH.name)


def _merge_legacy(entries: Dict[str, dict]):
    if not LEGACY_LEXICON_PATH.exists():
        return
    data = _load_json(LEGACY_LEXICON_PATH)
    if not isinstance(data, list):
        return
    for item in data:
        if not isinstance(item, dict):
            continue
        term = item.get("term")
        definition = item.get("definition")
        category = item.get("category", "legacy")
        if term and definition:
            _add_entry(entries, term, definition, category, LEGACY_LEXICON_PATH.name)


def _build_wordlist() -> dict:
    words = set()
    for path in WORDLIST_SOURCES:
        if not path.exists():
            continue
        data = _load_json(path)
        for word in data.get("words", []):
            if isinstance(word, str):
                words.add(word.lower())
    return {
        "meta": {
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d"),
            "sources": [p.name for p in WORDLIST_SOURCES if p.exists()],
        },
        "words": sorted(words),
    }


def main() -> int:
    entries: Dict[str, dict] = {}
    _build_shortforms(entries)
    _build_slang(entries)
    _build_noise(entries)
    _build_particles(entries)
    _build_manglish_patterns(entries)
    _build_grammar(entries)
    _build_dialects(entries)
    _merge_legacy(entries)

    lexicon = sorted(entries.values(), key=lambda x: x["term"])
    LEXICON_OUT.write_text(json.dumps(lexicon, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote lexicon: {LEXICON_OUT} ({len(lexicon)} entries)")

    wordlist = _build_wordlist()
    WORDLIST_OUT.write_text(json.dumps(wordlist, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote wordlist: {WORDLIST_OUT} ({len(wordlist.get('words', []))} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
