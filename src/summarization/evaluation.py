import random
from typing import Dict

class Evaluator:
    def evaluate(self, summary: str, source_text: str) -> Dict[str, float]:
        """
        Simulates Ragas evaluation.
        Metrics: Faithfulness, Entity Preservation.
        """
        # Mock scores
        faithfulness = round(random.uniform(0.85, 0.99), 2)
        entity_preservation = round(random.uniform(0.80, 0.95), 2)
        
        return {
            "faithfulness": faithfulness,
            "entity_preservation": entity_preservation
        }
