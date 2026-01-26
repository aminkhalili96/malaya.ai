"""
Benchmark Tracker API Server
Real-time API for tracking Malaya LLM benchmark progress
"""
from flask import Flask, jsonify, request, send_from_directory
try:
    from flask_cors import CORS
except ImportError:  # pragma: no cover - optional dependency for local dev
    def CORS(app, *args, **kwargs):
        return app
import json
import subprocess
import threading
import time
import queue
import re
import shutil
from pathlib import Path
from collections import defaultdict

APP_DIR = Path(__file__).parent
ROOT_DIR = APP_DIR.parent
REPORTS_DIR = ROOT_DIR / "reports"
CASES_PATH = ROOT_DIR / "tests" / "fixtures" / "expanded_cases.json"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

DEFAULT_MODEL = "gpt-oss:20b"

MODEL_INFO = {
    "qwen3-vl": {"company": "Alibaba Cloud", "logo": "/static/logos/qwen.png"},
    "malaya-v2": {"company": "YTL AI Labs", "logo": "/static/logos/mesolitica.png"},
    "malaya": {"company": "YTL AI Labs", "logo": "/static/logos/mesolitica.png"},
    "qwen3": {"company": "Alibaba Cloud", "logo": "/static/logos/qwen.png"},
    "qwen2.5": {"company": "Alibaba Cloud", "logo": "/static/logos/qwen.png"},
    "qwen": {"company": "Alibaba Cloud", "logo": "/static/logos/qwen.png"},
    "gemma3": {"company": "Google DeepMind", "logo": "/static/logos/google.png"},
    "gemma2": {"company": "Google DeepMind", "logo": "/static/logos/google.png"},
    "gemma": {"company": "Google DeepMind", "logo": "/static/logos/google.png"},
    "llama3.2": {"company": "Meta", "logo": "/static/logos/meta.png"},
    "llama3.1": {"company": "Meta", "logo": "/static/logos/meta.png"},
    "llama3": {"company": "Meta", "logo": "/static/logos/meta.png"},
    "llama2": {"company": "Meta", "logo": "/static/logos/meta.png"},
    "llama": {"company": "Meta", "logo": "/static/logos/meta.png"},
    "deepseek-coder-v2": {"company": "DeepSeek", "logo": "/static/logos/deepseek.png"},
    "deepseek-coder": {"company": "DeepSeek", "logo": "/static/logos/deepseek.png"},
    "deepseek": {"company": "DeepSeek", "logo": "/static/logos/deepseek.png"},
    "mistral": {"company": "Mistral AI", "logo": "/static/logos/mistral.svg"},
    "mixtral": {"company": "Mistral AI", "logo": "/static/logos/mistral.svg"},
    "codestral": {"company": "Mistral AI", "logo": "/static/logos/mistral.svg"},
    "llava": {"company": "LLaVA Team", "logo": "/static/logos/llava.svg"},
    "mesolitica": {"company": "Mesolitica", "logo": "/static/logos/mesolitica.png"},
    "openai": {"company": "OpenAI", "logo": "/static/logos/openai.png"},
    "gpt-4o": {"company": "OpenAI", "logo": "/static/logos/openai.png"},
    "gpt-4": {"company": "OpenAI", "logo": "/static/logos/openai.png"},
    "gpt": {"company": "OpenAI", "logo": "/static/logos/openai.png"},
    "gpt-oss": {"company": "OpenAI OSS", "logo": "/static/logos/openai.png"},
    "malaya-v7": {"company": "YTL AI Labs", "logo": "/static/logos/mesolitica.png"},
}

HISTORICAL_SCORES = {
    "gemma3:27b": {"accuracy": 89.0, "semantic_accuracy": 64.6, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "mesolitica-grpo:7b": {"accuracy": 80.0, "semantic_accuracy": 65.2, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "malaya-v3:7b": {"accuracy": 80.0, "semantic_accuracy": 50.0, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "gpt-oss:20b": {"accuracy": 83.0, "semantic_accuracy": 60.2, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "qwen3:14b": {"accuracy": 77.0, "semantic_accuracy": 64.4, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "qwen2.5:14b": {"accuracy": 82.7, "semantic_accuracy": 65.0, "cases": 98, "status": "complete", "judge": "Gemini 3 Pro"},
    "llama3.1:8b": {"accuracy": 66.0, "semantic_accuracy": 63.6, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "qwen2.5:7b": {"accuracy": 62.0, "semantic_accuracy": 62.0, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "deepseek-coder-v2:16b": {"accuracy": 61.0, "semantic_accuracy": 63.0, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "llama3.2:3b": {"accuracy": 59.0, "semantic_accuracy": 61.1, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "phi3:14b": {"accuracy": 33.0, "semantic_accuracy": 58.0, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "malaya-v2:7b": {"accuracy": 2.0, "semantic_accuracy": 45.0, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro"},
    "malaya-v7:7b": {"accuracy": 2.0, "semantic_accuracy": 10.0, "cases": 100, "status": "complete", "judge": "Gemini 3 Pro (Audit)"},
}

state_lock = threading.Lock()
queued_models = set()
running_benchmarks = {}
benchmark_queue = queue.PriorityQueue()


def load_test_cases():
    if not CASES_PATH.exists():
        return []
    try:
        with open(CASES_PATH, "r") as handle:
            return json.load(handle)
    except Exception:
        return []


def build_case_lookup(cases):
    return {case.get("id"): case for case in cases if "id" in case}


def safe_model_name(model_name):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", model_name)


def meta_path(model_name):
    return REPORTS_DIR / f"benchmark_meta_{safe_model_name(model_name)}.json"


def report_path(model_name):
    return REPORTS_DIR / f"benchmark_competitor_{safe_model_name(model_name)}.jsonl"


def write_meta(model_name, payload):
    try:
        with open(meta_path(model_name), "w") as handle:
            json.dump(payload, handle)
    except Exception:
        return


def load_meta(model_name):
    path = meta_path(model_name)
    if not path.exists():
        return {}
    try:
        with open(path, "r") as handle:
            return json.load(handle)
    except Exception:
        return {}


def get_latest_meta_model():
    latest = None
    latest_ts = 0
    for path in REPORTS_DIR.glob("benchmark_meta_*.json"):
        try:
            with open(path, "r") as handle:
                meta = json.load(handle)
            ts = meta.get("start_time") or meta.get("queued_at") or meta.get("completed_at") or 0
            if ts > latest_ts:
                latest_ts = ts
                latest = meta.get("model")
        except Exception:
            continue
    return latest


def get_model_family(model_name):
    base = model_name.split(":")[0].lower()
    for family in sorted(MODEL_INFO.keys(), key=len, reverse=True):
        if base.startswith(family):
            return family
    return None


def get_model_info(model_name):
    family = get_model_family(model_name)
    if family and family in MODEL_INFO:
        return MODEL_INFO[family]
    return {"company": "Unknown", "logo": "/static/logos/opensource.png"}


def get_model_size_priority(model_name):
    match = re.search(r"(\d+(?:\.\d+)?)b", model_name.lower())
    if match:
        return float(match.group(1))
    return 999.0


def get_model_size_label(model_name):
    match = re.search(r"(\d+(?:\.\d+)?)b", model_name.lower())
    return f"{match.group(1)}B" if match else "Unknown"


def get_benchmark_results(model_name):
    results = []
    path = report_path(model_name)
    if not path.exists():
        return results
    try:
        with open(path, "r") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []
    return results


def dedupe_results(results):
    ordered_ids = []
    result_map = {}
    for result in results:
        case_id = result.get("id")
        if case_id is None:
            continue
        if case_id not in result_map:
            ordered_ids.append(case_id)
        result_map[case_id] = result
    return [result_map[case_id] for case_id in ordered_ids]


def get_all_benchmark_results(total_cases):
    results = {}
    
    # Pre-computed semantic similarity scores (from dual_grader.py analysis)
    SEMANTIC_SCORES = {
        "gemma3:27b": 64.6,
        "gpt-oss:20b": 60.2,
        "malaysian-qwen-grpo:7b": 65.2,
        "qwen3:14b": 64.4,
        "llama3.1:8b": 63.6,
        "deepseek-coder-v2:16b": 63.0,
        "llama3.2:3b": 61.1,
        "phi3:14b": 58.0,
        "malaya-v2:7b": 45.0,
        "qwen3-vl:8b": 66.0,
    }
    
    for path in REPORTS_DIR.glob("benchmark_competitor_*.jsonl"):
        model_name = path.stem.replace("benchmark_competitor_", "").replace("_", ":")
        entries = []
        try:
            with open(path, "r") as handle:
                for line in handle:
                    try:
                        entries.append(json.loads(line.strip()))
                    except Exception:
                        continue
        except Exception:
            continue
        if entries:
            unique_entries = dedupe_results(entries)
            score = sum(entry.get("score", 0) for entry in unique_entries)
            accuracy = (score / len(unique_entries)) * 100 if unique_entries else 0
            status = "complete" if total_cases and len(unique_entries) >= total_cases else "incomplete"
            
            # Get semantic score (from pre-computed or estimate)
            semantic_score = SEMANTIC_SCORES.get(model_name, 60.0)
            
            results[model_name] = {
                "accuracy": round(accuracy, 1),
                "semantic_accuracy": round(semantic_score, 1),
                "cases": len(unique_entries),
                "score": score,
                "status": status,
            }
    return results


def load_report_entries(report_file):
    entries = []
    try:
        with open(report_file, "r") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return []
    return dedupe_results(entries)


def build_category_stats(entries):
    categories = defaultdict(lambda: {"correct": 0, "total": 0})
    for entry in entries:
        cat = entry.get("category", "Unknown")
        categories[cat]["total"] += 1
        categories[cat]["correct"] += entry.get("score", 0)
    enriched = {}
    for name, stats in categories.items():
        total = stats["total"]
        accuracy = (stats["correct"] / total * 100) if total else 0
        enriched[name] = {
            "correct": stats["correct"],
            "total": total,
            "accuracy": round(accuracy, 1),
        }
    return enriched


def get_installed_models():
    if not shutil.which("ollama"):
        print("Error: 'ollama' executable not found in PATH")
        return []
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"Error running 'ollama list': {result.stderr}")
            return []
        lines = result.stdout.strip().split("\n")[1:]
        models = []
        for line in lines:
            parts = line.split()
            if parts:
                name = parts[0]
                size = "Unknown"
                if len(parts) >= 4:
                    size = f"{parts[2]} {parts[3]}"
                models.append({"name": name, "size": size})
        
        # Inject Malaya v2
        models.append({"name": "malaya-v2", "size": "7B (Hybrid)"})
        
        return models
    except Exception as e:
        print(f"Exception in get_installed_models: {e}")
        return []

@app.route("/api/debug/models")
def debug_models():
    if not shutil.which("ollama"):
        return jsonify({"error": "ollama not found", "path": shutil.which("ollama")})
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except Exception as e:
        return jsonify({"error": str(e)})


def benchmark_worker():
    while True:
        item = benchmark_queue.get()
        if len(item) == 3:
            _, _, model_name = item
            restart = False
        else:
            _, _, model_name, restart = item
        try:
            with state_lock:
                queued_models.discard(model_name)

            try:
                import ollama
            except Exception as exc:
                write_meta(model_name, {
                    "status": "error",
                    "model": model_name,
                    "error": f"Ollama unavailable: {exc}",
                    "completed_at": time.time(),
                })
                continue

            cases = TEST_CASES
            if not cases:
                write_meta(model_name, {
                    "status": "error",
                    "model": model_name,
                    "error": "No test cases found",
                    "completed_at": time.time(),
                })
                continue

            total_cases = len(cases)
            report_file = report_path(model_name)
            existing_results = []
            completed_ids = set()
            resume = False

            if report_file.exists() and not restart:
                existing_results = get_benchmark_results(model_name)
                completed_ids = {r.get("id") for r in existing_results if r.get("id") is not None}
                if completed_ids and len(completed_ids) < total_cases:
                    resume = True
                elif completed_ids and len(completed_ids) >= total_cases:
                    restart = True

            if restart and report_file.exists():
                report_file.unlink()
                completed_ids = set()
                resume = False

            completed_count = len(completed_ids)
            with state_lock:
                running_benchmarks[model_name] = {"status": "running", "progress": completed_count}

            existing_meta = load_meta(model_name)
            start_time = existing_meta.get("start_time") if resume else time.time()
            if not start_time:
                start_time = time.time()

            write_meta(model_name, {
                "status": "running",
                "model": model_name,
                "start_time": start_time,
                "resumed_at": time.time() if resume else None,
                "resume_from": completed_count if resume else 0,
                "total_cases": total_cases,
            })

            # Check for Malaya v2
            malaya_bot = None
            if model_name == "malaya-v2":
                try:
                    import asyncio
                    import os
                    import sys
                    # Add ROOT_DIR to sys.path so we can import src
                    if str(ROOT_DIR) not in sys.path:
                        sys.path.insert(0, str(ROOT_DIR))

                    # CRITICAL: Check if 'malaya' causes a segfault/crash BEFORE importing
                    # Run a subprocess to test import. If it crashes (exit code < 0 or non-zero), abort.
                    try:
                        check_malaya = subprocess.run(
                            [sys.executable, "-c", "import malaya"], 
                            capture_output=True, 
                            timeout=10
                        )
                        if check_malaya.returncode != 0:
                            raise RuntimeError(f"Malaya library is broken (Exit Code {check_malaya.returncode}). Check environment.")
                    except subprocess.SubprocessError as e:
                        raise RuntimeError(f"Malaya safety check failed: {e}")

                    # FORCE NATIVE MODE (0)
                    os.environ["MALAYA_FORCE_MOCK"] = "0" 
                    from src.chatbot.engine import MalayaChatbot
                    # Use config_7b for benchmark
                    config_path = ROOT_DIR / "config_7b.yaml"
                    malaya_bot = MalayaChatbot(config_path=str(config_path))
                except Exception as e:
                    write_meta(model_name, {
                        "status": "error",
                        "model": model_name,
                        "error": f"Malaya v2 Init Failed: {e}",
                        "completed_at": time.time(),
                    })
                    continue

            for index, case in enumerate(cases):
                case_id = case.get("id")
                if case_id in completed_ids:
                    continue
                case_start = time.time()
                output = ""
                score = 0
                error_message = None
                try:
                    if malaya_bot:
                        # Use Malaya v2 Pipeline
                        output = asyncio.run(malaya_bot.process_query(
                            case.get("input", ""), 
                            user_id="benchmark_tester"
                        ))
                    else:
                        # Use Raw Ollama
                        resp = ollama.chat(
                            model=model_name,
                            messages=[{"role": "user", "content": case.get("input", "")}],
                        )
                        output = resp.get("message", {}).get("content", "")
                    
                    response_lower = output.lower()
                    neg_match = any(
                        neg.lower() in response_lower for neg in case.get("negative_keywords", [])
                    )
                    if not neg_match:
                        score = 1 if any(
                            kw.lower() in response_lower
                            for kw in case.get("expected_keywords", [])
                        ) else 0
                except Exception as exc:
                    error_message = str(exc)
                duration = time.time() - case_start

                entry = {
                    "id": case.get("id"),
                    "model": model_name,
                    "score": score,
                    "output": output,
                    "category": case.get("category", "General"),
                    "duration": duration,
                }
                if error_message:
                    entry["error"] = error_message

                try:
                    with open(report_file, "a") as handle:
                        handle.write(json.dumps(entry) + "\n")
                except Exception:
                    pass

                if case_id is not None:
                    completed_ids.add(case_id)

                with state_lock:
                    if model_name in running_benchmarks:
                        running_benchmarks[model_name]["progress"] = len(completed_ids)

            write_meta(model_name, {
                "status": "complete",
                "model": model_name,
                "start_time": start_time,
                "completed_at": time.time(),
                "total_cases": total_cases,
            })
        except Exception as exc:
            write_meta(model_name, {
                "status": "error",
                "model": model_name,
                "error": str(exc),
                "completed_at": time.time(),
            })
        finally:
            with state_lock:
                running_benchmarks.pop(model_name, None)
            benchmark_queue.task_done()


TEST_CASES = load_test_cases()
TEST_CASE_LOOKUP = build_case_lookup(TEST_CASES)
TOTAL_CASES = len(TEST_CASES)

worker_thread = threading.Thread(target=benchmark_worker, daemon=True)
worker_thread.start()


@app.route("/")
def index():
    return send_from_directory(APP_DIR, "index.html")


@app.route("/api/benchmark")
def get_benchmark():
    requested_model = request.args.get("model")
    active_model = requested_model

    with state_lock:
        running_models = list(running_benchmarks.keys())
        queued = set(queued_models)

    if not active_model or active_model == "auto":
        if running_models:
            active_model = running_models[0]
        elif queued:
            active_model = sorted(queued)[0]
        else:
            latest = get_latest_meta_model()
            active_model = latest or DEFAULT_MODEL

    model_info = get_model_info(active_model)
    meta = load_meta(active_model)

    total_cases = TOTAL_CASES
    results = dedupe_results(get_benchmark_results(active_model))

    status = meta.get("status")
    is_running = active_model in running_models
    is_queued = active_model in queued

    if status == "queued" and not is_running:
        results = []

    completed = len(results)
    score = sum(result.get("score", 0) for result in results)
    accuracy = (score / completed * 100) if completed > 0 else 0.0

    start_time_ts = meta.get("start_time")

    avg_time_per_case = None
    if completed > 0:
        recent = [r.get("duration", 0) for r in results[-10:] if r.get("duration")]
        if recent:
            avg_time_per_case = sum(recent) / len(recent)
        elif start_time_ts:
            avg_time_per_case = (time.time() - start_time_ts) / completed
    if avg_time_per_case is None:
        avg_time_per_case = 20

    remaining = max(total_cases - completed, 0)
    eta_minutes = int(round(remaining * avg_time_per_case / 60)) if remaining else 0

    if is_running:
        status = "running"
    elif is_queued:
        status = "queued"
    elif meta.get("status") == "error":
        status = "error"
    elif completed and completed >= total_cases and total_cases:
        status = "complete"
    elif completed:
        status = "incomplete"
    else:
        status = "idle"

    categories = defaultdict(lambda: {"correct": 0, "total": 0})
    for result in results:
        cat = result.get("category", "Unknown")
        categories[cat]["total"] += 1
        categories[cat]["correct"] += result.get("score", 0)

    enriched_results = []
    for result in results:
        case = TEST_CASE_LOOKUP.get(result.get("id"), {})
        enriched_results.append({
            **result,
            "input": case.get("input", ""),
            "expected": ", ".join(case.get("expected_keywords", [])),
            "negative": ", ".join(case.get("negative_keywords", [])),
        })

    return jsonify({
        "requested_model": requested_model,
        "model": active_model,
        "model_size": get_model_size_label(active_model),
        "model_info": model_info,
        "status": status,
        "running": is_running,
        "queued": is_queued,
        "total": total_cases,
        "completed": completed,
        "score": score,
        "accuracy": round(accuracy, 1),
        "eta_minutes": eta_minutes,
        "start_time_ts": start_time_ts,
        "categories": dict(categories),
        "results": enriched_results,
    })


@app.route("/api/models")
def get_models():
    installed = get_installed_models()
    benchmarked = get_all_benchmark_results(TOTAL_CASES)

    models = []
    with state_lock:
        running = set(running_benchmarks.keys())
        queued = set(queued_models)

    for model in installed:
        name = model["name"]
        info = get_model_info(name)
        bench_data = benchmarked.get(name, benchmarked.get(name.replace(":", "_")))
        progress = None
        if name in running:
            rb = running_benchmarks.get(name, {})
            progress = rb.get("progress", 0)
        models.append({
            "name": name,
            "size": model["size"],
            "company": info["company"],
            "logo": info["logo"],
            "benchmarked": bench_data is not None,
            "benchmark": bench_data,
            "running": name in running,
            "queued": name in queued,
            "progress": progress,
            "total_cases": TOTAL_CASES,
        })

    return jsonify({"models": models})


@app.route("/api/queue")
def get_queue():
    """Get currently running model and queue status."""
    with state_lock:
        running = list(running_benchmarks.keys())
        queued = list(queued_models)

    # Currently running model(s)
    running_list = []
    for model_name in running:
        info = get_model_info(model_name)
        rb = running_benchmarks.get(model_name, {})
        progress = rb.get("progress", 0)
        running_list.append({
            "name": model_name,
            "company": info["company"],
            "logo": info["logo"],
            "progress": progress,
            "total_cases": TOTAL_CASES,
            "status": "running",
        })

    # Queued models (sorted alphabetically since we don't have priority access)
    queued_list = []
    for model_name in sorted(queued):
        info = get_model_info(model_name)
        meta = load_meta(model_name)
        queued_list.append({
            "name": model_name,
            "company": info["company"],
            "logo": info["logo"],
            "queued_at": meta.get("queued_at"),
            "status": "queued",
        })

    return jsonify({
        "running": running_list,
        "queued": queued_list,
    })


@app.route("/api/test-cases")
def get_test_cases():
    """Get all test cases."""
    return jsonify({
        "total": TOTAL_CASES,
        "cases": TEST_CASES
    })

@app.route("/api/leaderboard")
def get_leaderboard():
    benchmarked = get_all_benchmark_results(TOTAL_CASES)
    all_scores = {**HISTORICAL_SCORES}
    all_scores.update(benchmarked)

    leaderboard = []
    for model, data in all_scores.items():
        info = get_model_info(model)
        leaderboard.append({
            "model": model,
            "company": info["company"],
            "logo": info["logo"],
            "accuracy": data.get("accuracy", 0),
            "semantic_accuracy": data.get("semantic_accuracy", 60.0),
            "cases": data.get("cases", 0),
            "status": data.get("status", "complete"),
        })

    leaderboard.sort(key=lambda x: x["accuracy"], reverse=True)
    return jsonify({"leaderboard": leaderboard})


@app.route("/api/analysis")
def get_analysis():
    models = []
    global_score = 0
    global_cases = 0
    global_categories = defaultdict(lambda: {"correct": 0, "total": 0})

    for report_file in REPORTS_DIR.glob("benchmark_competitor_*.jsonl"):
        model_name = report_file.stem.replace("benchmark_competitor_", "").replace("_", ":")
        entries = load_report_entries(report_file)
        if not entries:
            continue

        score = sum(entry.get("score", 0) for entry in entries)
        cases = len(entries)
        accuracy = (score / cases * 100) if cases else 0
        status = "complete" if TOTAL_CASES and cases >= TOTAL_CASES else "incomplete"
        durations = [entry.get("duration") for entry in entries if entry.get("duration") is not None]
        avg_duration = sum(durations) / len(durations) if durations else None
        last_case_id = max((entry.get("id", 0) for entry in entries), default=0)
        last_updated = int(report_file.stat().st_mtime)
        categories = build_category_stats(entries)

        for cat, stats in categories.items():
            global_categories[cat]["total"] += stats["total"]
            global_categories[cat]["correct"] += stats["correct"]

        global_score += score
        global_cases += cases

        info = get_model_info(model_name)
        models.append({
            "model": model_name,
            "company": info["company"],
            "logo": info["logo"],
            "accuracy": round(accuracy, 1),
            "cases": cases,
            "score": score,
            "status": status,
            "avg_duration": round(avg_duration, 2) if avg_duration is not None else None,
            "last_case_id": last_case_id,
            "last_updated": last_updated,
            "categories": categories,
        })

    models.sort(key=lambda x: x["accuracy"], reverse=True)

    overall_accuracy = (global_score / global_cases * 100) if global_cases else 0
    summary_categories = {}
    for name, stats in global_categories.items():
        total = stats["total"]
        accuracy = (stats["correct"] / total * 100) if total else 0
        summary_categories[name] = {
            "correct": stats["correct"],
            "total": total,
            "accuracy": round(accuracy, 1),
        }

    summary = {
        "models": len(models),
        "total_cases": TOTAL_CASES,
        "total_completed_cases": global_cases,
        "overall_accuracy": round(overall_accuracy, 1),
        "categories": summary_categories,
    }

    return jsonify({"summary": summary, "models": models})


@app.route("/api/run-benchmark", methods=["POST"])
def run_benchmark():
    data = request.get_json(silent=True) or {}
    model_name = data.get("model")
    restart = bool(data.get("restart"))

    if not model_name:
        return jsonify({"error": "Model name required"}), 400

    with state_lock:
        if model_name in running_benchmarks:
            return jsonify({"error": "Benchmark already running for this model"}), 400
        if model_name in queued_models:
            return jsonify({"error": "Model already in queue"}), 400

        report_file = report_path(model_name)
        existing_results = []
        if report_file.exists() and not restart:
            existing_results = get_benchmark_results(model_name)
            unique_existing = dedupe_results(existing_results)
            if unique_existing and len(unique_existing) >= TOTAL_CASES:
                restart = True

        priority = get_model_size_priority(model_name)
        timestamp = time.time()
        benchmark_queue.put((priority, timestamp, model_name, restart))
        queued_models.add(model_name)

    resume_from = 0
    if report_file.exists() and not restart:
        resume_from = len(dedupe_results(existing_results))

    write_meta(model_name, {
        "status": "queued",
        "model": model_name,
        "queued_at": time.time(),
        "total_cases": TOTAL_CASES,
        "resume_from": resume_from,
        "restart": restart,
    })

    return jsonify({
        "status": "queued",
        "model": model_name,
        "priority": priority,
        "resume_from": resume_from,
        "restart": restart,
    })


@app.route("/api/run-model", methods=["POST"])
def run_model():
    payload = request.get_json(silent=True) or {}
    model_name = payload.get("model")
    prompt = payload.get("prompt")
    system_prompt = payload.get("system")
    temperature = payload.get("temperature")

    if not model_name:
        return jsonify({"error": "Model name required"}), 400
    if not prompt:
        return jsonify({"error": "Prompt required"}), 400

    installed = {m["name"] for m in get_installed_models()}
    if installed and model_name not in installed:
        return jsonify({"error": "Model is not installed"}), 400

    try:
        import ollama
    except Exception as exc:
        return jsonify({"error": f"Ollama unavailable: {exc}"}), 500

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    options = {}
    if temperature is not None:
        try:
            options["temperature"] = float(temperature)
        except (TypeError, ValueError):
            pass

    start = time.time()
    try:
        kwargs = {"model": model_name, "messages": messages}
        if options:
            kwargs["options"] = options
        resp = ollama.chat(**kwargs)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    output = resp.get("message", {}).get("content", "")
    latency = time.time() - start

    return jsonify({
        "model": model_name,
        "output": output,
        "latency": round(latency, 2),
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "ollama_cli": bool(shutil.which("ollama")),
        "cases": TOTAL_CASES,
    })


if __name__ == "__main__":
    print("Benchmark Tracker API starting on http://localhost:5050")
    print(f"Reports directory: {REPORTS_DIR}")
    # usage_reloader=False prevents 'Operation not permitted' errors on some macOS systems
    app.run(host="0.0.0.0", port=5050, debug=True, use_reloader=False)
