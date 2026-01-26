
import asyncio
import os
import sys
import logging
from pprint import pprint

# Ensure we can import src
sys.path.append(os.getcwd())

# Mock environment for testing without real LLM if needed, 
# but here we want to test the Engine wiring.
# We will use a mock LLM or rely on offline mode behavior to avoid heavy API calls if possible,
# or just run it and see the context construction.

from src.chatbot.engine import MalayaChatbot

async def verify_pipeline():
    print("🚀 Initializing Malaya LLM Pipeline...")
    bot = MalayaChatbot(config_path="config.yaml")
    
    # Check if RAG Service was loaded
    if hasattr(bot, 'rag_service'):
        print("✅ RAG Service Loaded into Engine")
        docs_count = len(bot.rag_service.get_retriever().docs)
        print(f"📊 Knowledge Base Size: {docs_count} docs")
    else:
        print("❌ RAG Service NOT Loaded (Using fallback HybridRetriever?)")
    
    # Check Normalization Service
    if bot.malaya_service:
        print("✅ Malaya Service (Normalization) Loaded")
    else:
        print("❌ Malaya Service NOT Loaded")

    # Test Case 1: Normalization + RAG
    # "xleh" -> "tak boleh" (Normalization)
    # "SMK Aminuddin Baki" -> Fact Retrieval (RAG)
    user_query = "aq xleh nk cari SMK Aminuddin Baki kat mana"
    print(f"\n🧪 Test Query: '{user_query}'")
    
    # We use 'process_query' but checking the internal steps via a dry run or by mocking LLM to just return context
    # For now, let's run it and intercept the response or just check logs if we enable them.
    # Actually, let's look at the result object.
    
    try:
        response = await bot.process_query(
            user_input=user_query,
            chat_history=[],
            model={"provider": "ollama", "name": "dummy"}, # Force simple path
            tools={"web_search": False} # Force usage of local knowledge
        )
        
        print("\n--- Pipeline Result ---")
        print(f"Normalized: {response.get('normalized_query')}")
        print(f"Detected Lang: {response.get('detected_language')}")
        
        # Check if RAG context was found (hard to check directly in response object depending on implementation)
        # But 'normalized_query' proving 'xleh' -> 'tak boleh' confirms MalayaService.
        
        norm_success = "tak boleh" in response.get('normalized_query', "").lower()
        if norm_success:
            print("✅ Normalization Working: 'xleh' -> 'tak boleh'")
        else:
            print(f"❌ Normalization Failed: Got '{response.get('normalized_query')}'")

    except Exception as e:
        print(f"❌ Runtime Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_pipeline())
