#!/usr/bin/env python3
"""Test Malaya NLP and FAISS imports."""

print("Testing imports...")

try:
    import malaya
    print(f"✅ malaya version: {malaya.__version__}")
except ImportError as e:
    print(f"❌ malaya import failed: {e}")

try:
    import faiss
    print(f"✅ faiss loaded successfully")
except ImportError as e:
    print(f"❌ faiss import failed: {e}")

print("\nTesting malaya.normalizer...")
try:
    normalizer = malaya.normalizer.rules.load()
    test_input = "xleh la bro, xde duit"
    result = normalizer.normalize(test_input)
    print(f"  Input:  '{test_input}'")
    print(f"  Output: '{result}'")
    print("✅ Normalizer works!")
except Exception as e:
    print(f"❌ Normalizer failed: {e}")

print("\n--- Test Complete ---")
