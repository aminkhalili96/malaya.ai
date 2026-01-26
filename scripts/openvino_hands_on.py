
import time
import sys
import subprocess
import numpy as np
from pathlib import Path

# --- Dependency Check & Auto-Install ---
REQUIRED = ["optimum-intel", "openvino", "transformers", "torch", "sentence-transformers"]
def check_dependencies():
    missing = []
    for pkg in REQUIRED:
        try:
            if pkg == "optimum-intel":
                import optimum.intel
            elif pkg == "openvino":
                import openvino
            elif pkg == "transformers":
                import transformers
            elif pkg == "torch":
                import torch
            elif pkg == "sentence-transformers":
                import sentence_transformers
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"📦 Installing missing dependencies for OpenVINO Lab: {', '.join(missing)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("✅ Dependencies installed! Restarting script...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

import os
check_dependencies()

from transformers import AutoTokenizer, AutoModel
from optimum.intel import OVModelForFeatureExtraction

# --- Configuration ---
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"  # Small, fast model
EXPORT_PATH = Path("openvino_model")
TEST_SENTENCE = "Malaya LLM is a sovereign AI project for Malaysia."

def benchmark_pytorch():
    """Run standard PyTorch inference."""
    print(f"\n🔥 [Baseline] Loading PyTorch Model: {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModel.from_pretrained(MODEL_ID)
    
    inputs = tokenizer(TEST_SENTENCE, return_tensors="pt")
    
    # Warmup
    for _ in range(5):
        _ = model(**inputs)
        
    print("   Running benchmark (100 iterations)...")
    start = time.perf_counter()
    for _ in range(100):
        with torch.no_grad():
            _ = model(**inputs)
    end = time.perf_counter()
    
    avg_ms = ((end - start) / 100) * 1000
    print(f"   👉 PyTorch Average Latency: {avg_ms:.2f} ms")
    return avg_ms

def benchmark_openvino():
    """Run OpenVINO inference via Optimum."""
    print(f"\n🚀 [OpenVINO] converting & loading Model...")
    
    # This automatically exports PyTorch -> OpenVINO IR (.xml)
    ov_model = OVModelForFeatureExtraction.from_pretrained(MODEL_ID, export=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    # Compile model for CPU (this creates the executable network)
    ov_model.to("CPU")
    
    inputs = tokenizer(TEST_SENTENCE, return_tensors="pt")
    
    # Warmup
    for _ in range(5):
        _ = ov_model(**inputs)
        
    print("   Running benchmark (100 iterations)...")
    start = time.perf_counter()
    for _ in range(100):
        _ = ov_model(**inputs)
    end = time.perf_counter()
    
    avg_ms = ((end - start) / 100) * 1000
    print(f"   👉 OpenVINO Average Latency: {avg_ms:.2f} ms")
    
    # Feature 2: Inspecting the IR
    print("\n🧐 [Hands-On] Inspecting the exported model...")
    # Optimum saves it to a cache, but let's save explicitly to see files
    ov_model.save_pretrained("./my_openvino_model")
    print("   Saved model to ./my_openvino_model/")
    print("   Files generated:")
    for f in os.listdir("./my_openvino_model"):
        if f.endswith(".xml") or f.endswith(".bin"):
            print(f"    - {f} (The {'Topology' if 'xml' in f else 'Weights'})")
            
    return avg_ms

if __name__ == "__main__":
    print("🎓 OpenVINO Hands-On Lab")
    print("========================")
    print("Goal: Compare PyTorch vs OpenVINO inference speed on CPU.\n")
    
    pt_lat = benchmark_pytorch()
    ov_lat = benchmark_openvino()
    
    speedup = pt_lat / ov_lat
    print("\n🏆 RESULTS")
    print(f"   Speedup Factor: {speedup:.2f}x")
    
    if speedup > 1.0:
        print("   ✅ OpenVINO is faster! This is what you tell the interviewer.")
    else:
        print("   ⚠️ Speeds are similar (common for very small batch=1 inputs on fast CPUs).")
        print("      Try increasing batch size or using quantized INT8 models for bigger gains.")

