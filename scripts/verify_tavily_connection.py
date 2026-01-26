import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# 1. Load Environment
load_dotenv()

# 2. Setup Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.rag.retrieval import HybridRetriever

def verify():
    print(f"Checking TAVILY_API_KEY: {'Perceptible' if 'TAVILY_API_KEY' in os.environ else 'MISSING'}")
    
    # 3. Initialize Retriever
    try:
        retriever = HybridRetriever(docs=[], web_timeout_seconds=5.0)
        
        # 4. Run Search
        query = "Siapa pemenang AJL 38 2024?"
        print(f"Running search for: {query}")
        
        results = retriever._web_search(query)
        
        if results:
            print("\nSUCCESS: Web Search functionality confirmed.")
            for r in results:
                print(f"- {r['content'][:100]}...")
        else:
            print("\nFAILURE: Web Search returned no results.")
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")

if __name__ == "__main__":
    verify()
