
import sys
import time

print("🧪 Testing Light Dependencies...")

print("1. Testing rank_bm25...")
try:
    from rank_bm25 import BM25Okapi
    print("   ✅ rank_bm25 imported.")
except ImportError:
    print("   ❌ rank_bm25 MISSING.")
except Exception as e:
    print(f"   ❌ rank_bm25 ERROR: {e}")

print("2. Testing sentence_transformers (Torch)...")
try:
    from sentence_transformers import SentenceTransformer
    print("   ✅ sentence_transformers imported (Torch is working).")
except ImportError:
    print("   ❌ sentence_transformers MISSING.")
except Exception as e:
    print(f"   ❌ sentence_transformers ERROR: {e}")

print("3. Testing Shortforms Data...")
try:
    import json
    with open("src/data/shortforms.json", "r") as f:
        data = json.load(f)
    print(f"   ✅ loaded {len(data)} shortforms.")
except Exception as e:
    print(f"   ❌ Shortforms ERROR: {e}")
