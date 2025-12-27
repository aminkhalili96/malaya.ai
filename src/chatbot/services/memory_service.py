from typing import List, Dict, Any
import json
import os

class MemoryService:
    """
    Manages long-term user memories and preferences.
    """
    
    def __init__(self, memory_file="user_memory.json"):
        self.memory_file = memory_file
        self.memories = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {"facts": [], "preferences": {}}

    def save_memory(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.memories, f, indent=2)

    def add_fact(self, fact: str):
        """Add a factual memory (e.g., 'User lives in KL')."""
        if fact not in self.memories["facts"]:
            self.memories["facts"].append(fact)
            self.save_memory()

    def set_preference(self, key: str, value: str):
        """Set a structured preference (e.g., 'food_allergies': 'peanuts')."""
        self.memories["preferences"][key] = value
        self.save_memory()

    def get_context_string(self) -> str:
        """Returns a string to inject into the LLM System Prompt."""
        context = []
        if self.memories["facts"]:
            context.append("User Facts:\n- " + "\n- ".join(self.memories["facts"]))
        if self.memories["preferences"]:
            context.append("Preferences:\n" + "\n".join([f"- {k}: {v}" for k,v in self.memories["preferences"].items()]))
        
        return "\n\n".join(context)
