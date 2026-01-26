
import os
import sys
import logging
import time

# Configure verbose logging to see where it hangs
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

print("🚀 Starting Malaya Environment Fixer...")
print("1. Checking Environment Variables...")
# Unset force mock if set
if "MALAYA_FORCE_MOCK" in os.environ:
    print("   - Removing MALAYA_FORCE_MOCK")
    del os.environ["MALAYA_FORCE_MOCK"]

print("2. Importing Malaya (this may take time)...")
start_time = time.time()

try:
    # Try importing common modules to see which one triggers download
    import malaya
    print(f"   ✅ 'malaya' package imported in {time.time() - start_time:.2f}s")
    
    print("3. Initializing Normalizer (triggers dictionary download)...")
    # This usually downloads 'open-subs-dictionary' and 'bahasa-wiki'
    rules = malaya.normalizer.rules.load(date = False)
    print("   ✅ Normalizer rules loaded.")
    
    print("4. Initializing Toxicity (triggers BERT download)...")
    # This downloads the toxicity model
    model = malaya.toxicity.transformer(model = 'bert', quantized = True)
    print("   ✅ Toxicity model loaded.")
    
    print("\n🎉 SUCCESS! Malaya environment is ready. You can now run the benchmark without Mock Mode.")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

except KeyboardInterrupt:
    print("\n⚠️ Interrupted by user.")
