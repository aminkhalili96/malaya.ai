
import json
import re

KNOWLEDGE_FILE = "data/knowledge/v4_facts.json"

def load_json(path):
    with open(path, 'r') as f: return json.load(f)

knowledge_base = load_json(KNOWLEDGE_FILE)

def retrieve_fact(query):
    query_lower = query.lower()
    facts = []
    # Handle list-based knowledge base (v4_facts.json structure)
    if isinstance(knowledge_base, list):
        for item in knowledge_base:
            # Check keywords against query
            if 'keywords' in item and 'fact' in item:
                for kw in item['keywords']:
                    # Use word boundary check or simple inclusion? Simple inclusion is safer for short keywords, 
                    # but word boundary is better for precision. Let's use simple inclusion as previously intended but broken.
                    if kw.lower() in query_lower:
                        facts.append(item['fact'])
                        break # One match per fact is enough to include it
    return "\n".join(facts) if facts else None

# Test Cases
queries = [
    "paip air pecah, syabas contact number",
    "sape PM malaysia sekarang?",
    "concert coldplay malaysia ticket price",
    "sampah tak kutip seminggu, nak adu kat mana?"
]

print(f"Loaded {len(knowledge_base)} facts.")
if isinstance(knowledge_base, list):
    print("Knowledge base is a LIST.")
else:
    print(f"Knowledge base is a {type(knowledge_base)}.")

for q in queries:
    print(f"\nQuery: {q}")
    fact = retrieve_fact(q)
    print(f"Retrieved: {fact}")
