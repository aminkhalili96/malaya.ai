
import os
import asyncio
import logging
import sys
from pathlib import Path

# Fix path to include project root
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Force Mock (Lite) Mode
os.environ["MALAYA_FORCE_MOCK"] = "1"

async def main():
    print("🚀 Verifying Lite Mode Implementation...")
    
    # 1. Test LiteNormalizer
    print("\n[1] Testing LiteNormalizer...")
    from src.chatbot.services.malaya_service import MalayaService
    malaya_service = MalayaService()
    
    # Test cases from shortforms.json logic
    test_inputs = [
        "saya xleh pergi",
        "camne nak buat?",
        "ok tq bro",
        "aq tak tau"
    ]
    
    for text in test_inputs:
        normalized = malaya_service.normalize_text(text)
        print(f"   '{text}' -> '{normalized}'")
        
        # Validation checks
        if "xleh" in text and "tak boleh" not in normalized:
            print("   ❌ FAILED: xleh not expanded")
        if "camne" in text and "macam mana" not in normalized:
            print("   ❌ FAILED: camne not expanded")

    # 2. Test Lite Toxicity
    print("\n[2] Testing LiteToxicity...")
    toxic_text = "kau memang bodoh la"
    is_toxic, score, cat = malaya_service.check_toxicity(toxic_text)
    print(f"   Input: '{toxic_text}' -> Toxic: {is_toxic}, Score: {score}")
    if not is_toxic:
        print("   ❌ FAILED: Toxic word 'bodoh' not detected")

    # 3. Test LiteVectorSearch (Lexicon)
    print("\n[3] Testing LiteVectorSearch (Lexicon)...")
    from src.rag.vector_service import VectorRAGService
    vector_service = VectorRAGService()
    
    # Search for known term
    query = "reverse car"
    results = vector_service.search(query)
    print(f"   Query: '{query}'")
    for res in results:
        print(f"   - Found: {res['term']} ({res['definition'][:50]}...) Score: {res.get('score', 0):.4f}")
    
    # Setup Check
    found_gostan = any("gostan" in res['term'].lower() for res in results)
    if found_gostan:
        print("   ✅ SUCCESS: Found 'gostan' definition via BM25")
    else:
        print("   ❌ FAILED: Did not find 'gostan' for 'reverse car'")

if __name__ == "__main__":
    asyncio.run(main())
