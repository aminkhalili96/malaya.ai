
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def run_verification():
    print("=== Native Malaya 'Max Power' Verification ===")
    
    from src.chatbot.services.malaya_service import MalayaService
    from src.rag.vector_service import VectorRAGService
    
    # 1. Initialize Service (Downloads models if needed)
    print("\n[1] Initializing MalayaService (This may take time for 1st download)...")
    malaya = MalayaService()
    
    if not malaya._available:
        print("❌ MalayaService failed to initialize.")
        return

    # 2. Test Normalization
    print("\n[2] Testing Normalization...")
    slang = "tak xleh la bro"
    norm = malaya.normalize_text(slang)
    print(f"   Input: '{slang}'")
    print(f"   Output: '{norm}'")
    if "tidak boleh" in norm:
        print("   ✅ Normalization Pass")
    else:
        print("   ⚠️ Normalization Check (Verify output manually)")

    # 3. Test Toxicity
    print("\n[3] Testing Toxicity...")
    toxic_text = "kau ni bodoh la"
    clean_text = "saya sayang malaysia"
    
    is_toxic = malaya.check_toxicity(toxic_text)
    print(f"   '{toxic_text}' -> Toxic? {is_toxic}")
    if is_toxic: print("   ✅ Toxicity Pass (Positive)")
    
    is_toxic_clean = malaya.check_toxicity(clean_text)
    print(f"   '{clean_text}' -> Toxic? {is_toxic_clean}")
    if not is_toxic_clean: print("   ✅ Toxicity Pass (Negative)")

    # 4. Test Sentiment
    print("\n[4] Testing Sentiment...")
    text = "Aku suka makan nasi lemak sedap gila"
    sentiment = malaya.analyze_sentiment(text)
    print(f"   '{text}' -> {sentiment}")
    
    # 5. Test Paraphrasing
    print("\n[5] Testing Paraphrasing...")
    para_input = "Saya nak pergi pasar beli ikan."
    variations = malaya.generate_paraphrases(para_input, n=2)
    print(f"   Input: '{para_input}'")
    for i, v in enumerate(variations):
        print(f"   Var {i+1}: '{v}'")

    # 6. Test Vector RAG (Semantic Search)
    print("\n[6] Testing Vector RAG (Semantic Search)...")
    rag = VectorRAGService() # Should trigger model load
    query = "reversing car backward"
    print(f"   Query: '{query}'")
    results = rag.search(query)
    found_gostan = False
    for res in results:
        print(f"   Match: {res['term']} ({res['score']:.4f})")
        if "gostan" in res['term'].lower():
            found_gostan = True
            
    if found_gostan:
        print("   ✅ Semantic Search Pass (Found 'gostan' from 'reversing car')")
    else:
        print("   ⚠️ Semantic Search Check (Did not find gostan)")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    run_verification()
