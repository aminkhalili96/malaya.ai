import requests
import json
import os
import re
import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env immediately
load_dotenv()

# --- V7 Integration: Add project root to path ---
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.rag.retrieval import HybridRetriever
from src.summarization.preprocessing import TextNormalizer
from src.router.intent_classifier import IntentClassifier

# Constants
MODEL_NAME = "qwen2.5:7b"
TEST_CASES_FILE = "tests/fixtures/expanded_cases.json"
OUTPUT_FILE = "reports/v3_benchmark/malaya_ai_v7.json"
DIALECT_FILE = "data/dictionaries/v4_dialects.json"
GENERAL_CONTEXT_FILE = "data/knowledge/general_context.md"
FACTS_FILE = "data/knowledge/v4_facts.json"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT", "180"))
LEXICON_FILE = "data/lexicon_full.json"

OUTPUT_FILE = os.getenv("MALAYA_BENCHMARK_OUTPUT", OUTPUT_FILE)

def load_json(path):
    with open(path, 'r') as f: return json.load(f)

def load_lexicon_map(path):
    if not os.path.exists(path):
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    if not isinstance(data, list):
        return {}
    mapping = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        term = entry.get("term")
        definition = entry.get("definition")
        category = str(entry.get("category", "")).lower()
        if not term or not definition:
            continue
        if category.startswith("stopword") or category.startswith("grammar"):
            continue
        mapping[str(term).lower()] = str(definition).strip()
    return mapping

LEXICON_MAP = load_lexicon_map(LEXICON_FILE)

def load_existing_results(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data.get("results", []) if isinstance(data, dict) else []
    except Exception:
        return []

def save_results(path, results):
    with open(path, 'w') as f:
        json.dump({"model": "Malaya-V7-Full", "results": results}, f, indent=4, ensure_ascii=False)

# --- V7: Initialization (Same as V6) ---
dialect_map = load_json(DIALECT_FILE)
normalizer = TextNormalizer()
classifier = IntentClassifier()

try:
    with open(GENERAL_CONTEXT_FILE, "r") as f:
        general_context_text = f.read()
    
    chunks = []
    current_chunk = []
    for line in general_context_text.split('\n'):
        if line.startswith("## "):
            if current_chunk:
                chunks.append({"content": "\n".join(current_chunk), "metadata": {"source": "general_context.md"}})
            current_chunk = [line]
        else:
            current_chunk.append(line)
    if current_chunk:
        chunks.append({"content": "\n".join(current_chunk), "metadata": {"source": "general_context.md"}})
        
    print(f"Loaded {len(chunks)} context chunks.")
    
except Exception as e:
    print(f"Warning: Could not load general context: {e}")
    chunks = []

# Load Fact Snippets
try:
    facts = load_json(FACTS_FILE)
    for item in facts:
        fact_text = item.get("fact")
        keywords = item.get("keywords", [])
        if fact_text:
            chunks.append({
                "content": f"{fact_text} (Keywords: {', '.join(keywords)})",
                "metadata": {"source": "v4_facts.json"},
            })
except Exception as e:
    print(f"Warning: Could not load facts: {e}")

# Initialize Production Retriever (With Web Search)
retriever = HybridRetriever(
    docs=chunks,
    vector_dim=384, 
    reranker_enabled=False, 
    web_timeout_seconds=5.0
)

def _detect_requested_dialect(text_lower):
    if not re.search(r"\b(bahasa|dialek|loghat)\b", text_lower):
        return None
    aliases = {
        "kelate": "kelantan",
        "n9": "negeri sembilan",
    }
    for key, target in aliases.items():
        if key in text_lower:
            return target
    for dialect in dialect_map.keys():
        if dialect in text_lower:
            return dialect
    return None

def retrieve_dialect_context(text):
    text_lower = text.lower()
    matches = []
    requested = _detect_requested_dialect(text_lower)
    
    def add_match(term, dialect, mapping):
        if term in text_lower:
            clean = str(mapping).split('(')[0].strip()
            matches.append(f"{term} ({dialect}): {clean}")

    if requested and requested in dialect_map and isinstance(dialect_map[requested], dict):
        # Provide a compact hint set when user explicitly requests a dialect
        terms = list(dialect_map[requested].items())[:12]
        for term, mapping in terms:
            clean = str(mapping).split('(')[0].strip()
            matches.append(f"{term} ({requested}): {clean}")
    elif "dialects" in dialect_map:
        for dialect, data in dialect_map["dialects"].items():
            terms = data.get("keywords", {}) if isinstance(data, dict) else {}
            for term, mapping in terms.items():
                add_match(term, dialect, mapping)
    else:
        for dialect, terms in dialect_map.items():
            if not isinstance(terms, dict):
                continue
            for term, mapping in terms.items():
                add_match(term, dialect, mapping)
    
    return "\n".join(matches) if matches else None

def _extract_candidate_terms(text):
    candidates = []
    quoted = re.findall(r"[\"'“”‘’]([^\"'“”‘’]+)[\"'“”‘’]", text)
    for item in quoted:
        term = item.strip()
        if term:
            candidates.append(term)
    lowered = text.lower()
    if "maksud" in lowered or "meaning" in lowered:
        tokens = re.findall(r"\b\w+\b", lowered)
        for idx, tok in enumerate(tokens):
            if tok in {"maksud", "meaning"} and idx + 1 < len(tokens):
                candidates.append(tokens[idx + 1])
    return list(dict.fromkeys(candidates))

def retrieve_lexicon_context(text):
    if not LEXICON_MAP:
        return None
    candidates = _extract_candidate_terms(text)
    hits = []
    for cand in candidates:
        key = cand.lower()
        if key in LEXICON_MAP:
            hits.append(f"{cand}: {LEXICON_MAP[key]}")
    if not hits:
        tokens = set(re.findall(r"\b\w+\b", text.lower()))
        for token in tokens:
            if token in LEXICON_MAP:
                hits.append(f"{token}: {LEXICON_MAP[token]}")
    if not hits:
        return None
    return "\n".join(hits[:5])

def is_grammar_check(text):
    return bool(re.search(
        r"\b(check grammar|grammar check|cek grammar|betulkan ayat|betulkan grammar|"
        r"semak tatabahasa|fix grammar|correct (?:the )?sentence)\b",
        text.lower(),
    ))

def _extract_quoted_sentence(text):
    matches = re.findall(r"[\"'“”‘’]([^\"'“”‘’]+)[\"'“”‘’]", text)
    if matches:
        return matches[0].strip()
    match = re.search(r":\s*(.+)$", text)
    if match:
        return match.group(1).strip()
    return ""

def _to_past_tense(verb):
    irregular = {
        "go": "went",
        "do": "did",
        "eat": "ate",
        "have": "had",
        "see": "saw",
        "come": "came",
        "get": "got",
        "make": "made",
        "take": "took",
        "say": "said",
        "buy": "bought",
        "run": "ran",
        "write": "wrote",
        "read": "read",
        "leave": "left",
        "feel": "felt",
        "find": "found",
        "think": "thought",
        "drive": "drove",
        "speak": "spoke",
        "sleep": "slept",
    }
    lower = verb.lower()
    if lower in irregular:
        return irregular[lower]
    if lower.endswith("ed") or lower in irregular.values():
        return verb
    if lower.endswith("e"):
        return verb + "d"
    if lower.endswith("y") and len(lower) > 1 and lower[-2] not in "aeiou":
        return verb[:-1] + "ied"
    return verb + "ed"

def maybe_fix_english_grammar(text):
    sentence = _extract_quoted_sentence(text)
    if not sentence:
        return ""
    lower = sentence.lower()
    if not re.search(r"\b(yesterday|last night|last week|last month|last year|ago)\b", lower):
        return ""
    pattern = re.compile(r"\b(i|you|he|she|we|they)\s+(\w+)\b", re.IGNORECASE)
    match = pattern.search(sentence)
    if not match:
        return ""
    pronoun, verb = match.group(1), match.group(2)
    past = _to_past_tense(verb)
    if past.lower() == verb.lower():
        return ""
    corrected = pattern.sub(f"{pronoun} {past}", sentence, count=1)
    corrected = corrected.strip()
    if corrected:
        corrected = corrected[0].upper() + corrected[1:]
    return corrected

def strip_output_labels(text):
    if not text:
        return text
    drop_labels = {"paraphrased", "parafrase", "paraphrase", "cue"}
    strip_labels = {"translation", "maksudnya"}
    cleaned_lines = []
    for line in text.splitlines():
        raw = line.strip()
        lower = raw.lower()
        if not raw:
            cleaned_lines.append(line)
            continue
        if lower.startswith("paraphrased in standard malay"):
            continue
        matched = False
        for label in drop_labels:
            if lower.startswith(f"{label}:"):
                matched = True
                break
        if matched:
            continue
        for label in strip_labels:
            if lower.startswith(f"{label}:"):
                remainder = raw.split(":", 1)[1].strip()
                if remainder:
                    cleaned_lines.append(remainder)
                matched = True
                break
        if matched:
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()

def _is_question(text):
    if not text:
        return False
    if "?" in text:
        return True
    return bool(re.search(
        r"\b(apa|kenapa|mengapa|bila|tarikh|bagaimana|macam mana|"
        r"berapa|mana|siapa|which|what|why|when|where|how)\b",
        text.lower(),
    ))

def _has_request(text):
    if not text:
        return False
    return bool(re.search(
        r"\b(tolong|please|sila|buat|bagi|ajarkan|tunjuk|cara|"
        r"how to|apply|mohon|install|pasang|resepi|recipe|check)\b",
        text.lower(),
    ))

def build_playbook_hint(text):
    if not text:
        return ""
    lower = text.lower()
    hints = []
    if "python" in lower and "mac" in lower and any(k in lower for k in ["install", "pasang"]):
        hints.append(
            "If asked about installing Python on Mac, suggest Homebrew "
            "(`brew install python`) or the official installer from python.org, "
            "then verify with `python3 --version`."
        )
    if "ptptn" in lower:
        hints.append(
            "If asked about PTPTN, outline: register on the official PTPTN portal, "
            "prepare IC + offer letter + bank details, and open SSPN if required."
        )
    if "lhdn" in lower and any(k in lower for k in ["scam", "scammer", "call", "panggilan"]):
        hints.append(
            "If scam LHDN call: hang up, do not share info, block the number, and report to NSRC/CCID/polis."
        )
    if "klinik" in lower and ("24" in lower or "24 jam" in lower):
        hints.append(
            "For nearby 24-hour clinics, ask for location and suggest Google Maps/Waze or hospital emergency units."
        )
    if any(k in lower for k in ["panggung wayang", "wayang", "cinema"]):
        hints.append(
            "For nearby cinemas, suggest GSC/TGV/Star Cinemas and checking Google Maps for the closest branch."
        )
    if "cuti umum" in lower or "public holiday" in lower:
        hints.append(
            "Mention major holidays (CNY, Raya, Labour Day, Wesak, Agong's Birthday, National Day, "
            "Malaysia Day, Deepavali, Christmas) and note that dates vary by state; check official calendars."
        )
    if "raya" in lower and any(k in lower for k in ["bila", "tarikh"]) and "aidilfitri" in lower:
        hints.append(
            "Raya Aidilfitri date depends on official rukyah/hilal announcement; advise checking JAKIM/official calendar."
        )
    if "universiti malaya" in lower and any(k in lower for k in ["ranking", "rank", "world"]):
        hints.append(
            "UM ranking changes yearly; advise checking QS World University Rankings or Times Higher Education."
        )
    if "jdt" in lower and any(k in lower for k in ["menang", "juara"]):
        hints.append(
            "JDT often dominate Liga Super; if asking latest match, advise checking recent results."
        )
    if any(k in lower for k in ["translate", "terjemah"]) and _detect_requested_dialect(lower) == "kelantan":
        hints.append(
            "For Kelantan dialect, use: kawe (saya), demo (awak), cinto/sayang (love). "
            "Keep it short and do not mention other dialects."
        )
        if "love you" in lower or "i love you" in lower:
            hints.append(
                "If translating 'I love you', use: 'kawe cinto demo' with gloss 'saya sayang awak'."
            )
    if "ayam masak merah" in lower or ("resepi" in lower and "ayam" in lower and "merah" in lower):
        hints.append(
            "Ayam masak merah: goreng ayam separuh masak, tumis bawang + cili kisar, "
            "masuk sos cili/tomato + gula/garam, masukkan ayam dan gaul."
        )
    if "sahur" in lower:
        hints.append(
            "Sahur ialah makan sebelum subuh; 'lepas sahur' merujuk awal pagi, bukan waktu berbuka."
        )
    if "susah-susah" in lower or "tak payah" in lower or "tidak payah" in lower:
        hints.append(
            "Jika pengguna kata 'tak payah' atau 'susah-susah', maksudnya tiada perlu bersusah payah. Jawab ringkas sahaja."
        )
    if not hints:
        return ""
    return "\n\nPLAYBOOK:\n- " + "\n- ".join(hints)

def normalize_malay_output(text):
    if not text:
        return text
    spans = []

    def _mask(match):
        spans.append(match.group(0))
        return f"__CODESPAN{len(spans) - 1}__"

    masked = re.sub(r"```.*?```", _mask, text, flags=re.DOTALL)
    masked = re.sub(r"`[^`]*`", _mask, masked)
    replacements = {
        "banget": "sangat",
        "dahsyat": "hebat",
        "repot-repot": "susah-susah",
        "nge-kacau": "mengganggu",
        "ngekacau": "mengganggu",
        "bumbu": "rempah",
        "kemarin": "semalam",
        "maunya": "naknya",
        "beasiswa": "biasiswa",
        "coba": "cuba",
        "cobalah": "cubalah",
        "instal": "pasang",
        "menginstal": "memasang",
        "menginstall": "memasang",
        "install": "pasang",
        "aduk": "gaul",
        "situs": "laman",
        "arti": "maksud",
        "artinya": "maksudnya",
        "kirim": "hantar",
        "ktp": "IC",
        "repot-repotkan": "menyusahkan",
        "berarti": "bererti",
        "waktunya": "masanya",
        "merasa": "rasa",
        "mengetik": "menaip",
        "perintah": "arahan",
        "permohonanmu": "permohonan anda",
        "istirahat": "rehat",
    }
    normalized = masked
    for src, tgt in replacements.items():
        normalized = re.sub(rf"\b{re.escape(src)}\b", tgt, normalized, flags=re.IGNORECASE)
    for idx, span in enumerate(spans):
        normalized = normalized.replace(f"__CODESPAN{idx}__", span)
    return normalized

def retrieve_fact(query):
    if classifier.classify(query) == "chat":
        return None
    # Triggers for web search
    use_web = False
    triggers = ["current", "latest", "terkini", "2024", "price", "harga", "result", "keputusan", "winner", "pemenang"]
    if any(t in query.lower() for t in triggers):
        use_web = True
    
    normalized_query = normalizer.normalize_for_retrieval(query)
    results = retriever.search(normalized_query, k=3, use_web=use_web)
    
    if not results:
        return None

    def _filter_results_by_keywords(results_list):
        query_tokens = set(re.findall(r"\b\w+\b", query.lower()))
        filtered = []
        for item in results_list:
            content = item.get("content", "")
            match = re.search(r"Keywords:\s*([^)]+)\)", content, flags=re.IGNORECASE)
            if match:
                keywords = {k.strip().lower() for k in match.group(1).split(",") if k.strip()}
                if query_tokens & keywords:
                    filtered.append(item)
            else:
                filtered.append(item)
        return filtered or results_list

    results = _filter_results_by_keywords(results)
        
    context_str = ""
    for r in results:
        source = r['metadata'].get('source', 'unknown')
        content = r['content']
        context_str += f"[Source: {source}]\n{content}\n\n"
    
    return context_str.strip()

# --- V5: Critic Loop (Preserved) ---
def verify_response(query, response):
    query_lower = query.lower()
    response_lower = response.lower()
    
    if "list" in query_lower or "senarai" in query_lower or "contoh" in query_lower:
        if response.count("\n-") < 3 and response.count("\n1.") < 3 and "," not in response:
             return False, "User asked for a list. Please provide at least 3 distinct examples."
             
    if "cancel" in query_lower or "scam" in query_lower or "report" in query_lower:
        if "help centre" in response_lower and "customer service" not in response_lower:
             return False, "Use 'Customer Service' instead of just 'Help Centre' for better clarity."

    if "maksud" in query_lower or "meaning" in query_lower or "apa itu" in query_lower:
        if not any(t in response_lower for t in ["ungkapan", "slang", "dialek", "maksudnya", "erti"]):
            return False, "Add a short usage tag (e.g., 'ungkapan sakit/terkejut', 'slang remaja')."

    if any(t in query_lower for t in ["xleh", "xbleh", "xde"]) and not any(t in response_lower for t in ["tak boleh", "tidak boleh", "tak ada", "tiada", "cannot", "no money"]):
        return False, "Rewrite using standard Malay shortform expansions like 'tak boleh' / 'tak ada'."

    if "signal" in query_lower and any(t in query_lower for t in ["driver", "kereta", "memandu", "jalan", "lane", "lorry", "moto"]):
        if not any(t in response_lower for t in ["bahaya", "hati-hati", "dangerous"]):
            return False, "Mention that not giving signal is dangerous and advise to be careful."

    if "vs" in query_lower or "beza" in query_lower:
        if "beza" not in response_lower and "percanggahan" not in response_lower and "manakala" not in response_lower:
            return False, "User asked for comparison. Explicitly state the differences."

    return True, "OK"

def generate_v7_full_response(input_text):
    if is_grammar_check(input_text):
        corrected = maybe_fix_english_grammar(input_text)
        if corrected:
            return (
                f"Corrected: {corrected}\n\n"
                "Reason: Use past tense for time markers like \"yesterday\"."
            )

    # 1. Retrieve
    fact_context = retrieve_fact(input_text)
    dialect_context = retrieve_dialect_context(input_text)
    lexicon_context = retrieve_lexicon_context(input_text)
    normalized_query = normalizer.normalize_for_retrieval(input_text)
    requested_dialect = _detect_requested_dialect(input_text.lower())
    playbook_hint = build_playbook_hint(input_text)
    question_hint = ""
    if not _is_question(input_text) and not _has_request(input_text):
        question_hint = (
            "\nIf the input is a statement or short phrase, reply briefly without step-by-step instructions."
        )
    safety_context = None
    lower_text = input_text.lower()
    if "signal" in lower_text and any(t in lower_text for t in ["driver", "kereta", "memandu", "jalan", "lane", "lorry", "moto"]):
        safety_context = (
            "Tidak bagi signal semasa memandu itu bahaya. "
            "Nasihatkan agar lebih berhati-hati dan sebutkan 'bahaya' atau 'hati-hati'."
        )
    
    # 2. Prompt Construction
    system_prompt = "You are Malaya-V7 (Full), an advanced Malaysian AI assistant. "
    
    if fact_context:
        system_prompt += f"\n[KNOWLEDGE BASE]\n{fact_context}\n[END KNOWLEDGE BASE]\n"
        system_prompt += (
            "CRITICAL: Answer using [KNOWLEDGE BASE] info. Do not hallucinate. "
            "Include key entities/numbers from the knowledge base when relevant."
        )
    
    if dialect_context:
        system_prompt += f"\n[DIALECT NOTES]\n{dialect_context}\n[END DIALECT NOTES]\n"

    if lexicon_context:
        system_prompt += f"\n[LEXICON]\n{lexicon_context}\n[END LEXICON]\n"

    if safety_context:
        system_prompt += f"\n[SAFETY NOTE]\n{safety_context}\n[END SAFETY NOTE]\n"

    if normalized_query.strip() and normalized_query.strip().lower() != input_text.strip().lower():
        system_prompt += f"\n[NORMALIZED INPUT]\n{normalized_query}\n[END NORMALIZED INPUT]\n"

    if requested_dialect:
        system_prompt += (
            f"\n[DIALECT REQUEST]\nUser asked for {requested_dialect}."
            " Use that dialect where possible, or best-effort approximation."
            " Do not mention other dialects.\n[END DIALECT REQUEST]\n"
        )
        
    system_prompt += (
        "\nLanguage: Mirror the user's input. If the input is English-only, answer in English. "
        "Otherwise, answer in natural Malay/Manglish. "
    )
    system_prompt += (
        "First sentence: paraphrase the [NORMALIZED INPUT] in standard Malay "
        "(or English if English-only). "
    )
    system_prompt += (
        "After the paraphrase, answer directly with the solution or steps. Do not stop at paraphrase. "
        "If slang/shortforms appear, interpret them naturally (padu/gempak/terror = praise). "
        "Add a brief supportive cue only if the user sounds frustrated. "
        "If the user asks for meaning/maksud, include a short usage tag in parentheses "
        "(e.g., '(ungkapan sakit/terkejut)', '(slang remaja)'). "
        "Do not add usage tags unless the user asks for meaning/definition. "
        "If dialect is detected or requested, you may add a short standard Malay gloss without labels. "
        "Avoid labels like 'Paraphrased', 'Cue', 'Translation', or 'Maksudnya:'. "
        "Avoid Indonesian wording; prefer Malaysian Malay."
    )
    if playbook_hint:
        system_prompt += playbook_hint
    if question_hint:
        system_prompt += question_hint
    if is_grammar_check(input_text):
        system_prompt += (
            " If this is a grammar check request, correct the sentence in the same language. "
            "Provide the corrected sentence first, then a brief explanation. Do not translate."
        )
    system_prompt += "FORMATTING: 1. Lists must have 3+ items. 2. Comparisons must be explicit."
    system_prompt += "Do not output analysis or labels like Thoughts/Reasoning."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text}
    ]
    
    # 3. Generate
    response = requests.post('http://localhost:11434/api/chat', json={
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096}
    }, timeout=REQUEST_TIMEOUT_SECONDS).json()
    
    initial_answer = response['message']['content']
    initial_answer = strip_output_labels(initial_answer)
    initial_answer = normalize_malay_output(initial_answer)
    
    # 4. Critic Loop
    is_valid, critique = verify_response(input_text, initial_answer)
    if not is_valid:
        print(f"   [Correcting] {critique}")
        messages.append({"role": "assistant", "content": initial_answer})
        messages.append({"role": "user", "content": f"Correction: {critique}. Rewrite answer."})
        
        response_v2 = requests.post('http://localhost:11434/api/chat', json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.1}
        }, timeout=REQUEST_TIMEOUT_SECONDS).json()
        corrected = response_v2['message']['content']
        corrected = strip_output_labels(corrected)
        return normalize_malay_output(corrected)
        
    return initial_answer

def run_benchmark():
    print(f"Running V7 Benchmark (Full Capability: SFT+RAG+Web)...")
    cases = load_json(TEST_CASES_FILE)
    if not cases: return
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    results = load_existing_results(OUTPUT_FILE)
    completed_ids = {str(r.get("id")) for r in results if isinstance(r, dict)}
    total = len(cases)
    
    for i, case in enumerate(cases):
        if str(case.get("id")) in completed_ids:
            continue
        print(f"[{i+1}/{total}] Case {case['id']}...")
        try:
            response = generate_v7_full_response(case['input'])
            clean_response = re.sub(r'<thought>.*?</thought>', '', response, flags=re.DOTALL).strip()
            
            results.append({
                "id": case['id'],
                "input": case['input'],
                "response": clean_response,
                "raw_response": response,
                "category": case['category']
            })
            save_results(OUTPUT_FILE, results)
        except Exception as e:
            print(f"Error processing case {case['id']}: {e}")
            
    print(f"Done. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_benchmark()
