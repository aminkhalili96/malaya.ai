import unittest
import os
import pytest
from src.validation.validator import validate_tool_call
from src.validation.reflexion import validate_with_reflexion
from dotenv import load_dotenv
load_dotenv()

try:
    from src.summarization.preprocessing import TextNormalizer
    MALAYA_AVAILABLE = True
except ImportError:
    MALAYA_AVAILABLE = False

# Mock Ragas/LangSmith if keys missing for now
class TestNorthStar(unittest.TestCase):
    
    def setUp(self):
        self.api_key_present = "TAVILY_API_KEY" in os.environ
        
    def test_q1_reflexion_auto_fix(self):
        """
        North Star: System must auto-correct common JSON errors (Int as String).
        """
        print("\n[North Star] Testing Q1 Reflexion...")
        payload = {"action": "search", "k": "5", "q": "test"} # k is string "5"
        clean, errors, history = validate_with_reflexion(payload)
        
        self.assertEqual(clean['k'], 5, "Reflexion should coerce '5' to 5")
        self.assertEqual(len(errors), 0, "Should have 0 errors after fix")
        print("PASS: Reflexion auto-fixed JSON.")

    def test_q3_malaya_normalization(self):
        """
        North Star: System must normalize 'Bahasa Rojak' to standard Malay.
        """
        print("\n[North Star] Testing Q3 Malaya Normalization...")
        if not MALAYA_AVAILABLE:
            print("SKIP: Malaya not installed")
            return

        normalizer = TextNormalizer()
        # Test case: "xleh" -> "tak boleh"
        inp = "Server xleh on"
        out = normalizer.normalize(inp)
        
        # We check if "tak boleh" is in the output
        self.assertTrue("tak boleh" in out.lower(), f"Failed to normalize 'xleh'. Got: {out}")
        print(f"PASS: Normalized '{inp}' to '{out}'")

    def test_rag_retrieval_relevance(self):
        """
        North Star: RAG must retrieve relevant parent context.
        (Simulated for now without real Vector DB populated)
        """
        print("\n[North Star] Testing RAG Retrieval...")
        # TODO: Implement full RAG integration test with Ragas
        pass

if __name__ == '__main__':
    unittest.main()
