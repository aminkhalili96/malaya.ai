
from rank_bm25 import BM25Okapi
import re

print("🧪 Debugging BM25...")

lexicon = [
    {"term": "gostan", "definition": "Reverse or move backward (driving). From British nautical term 'go astern'."},
    {"term": "tapau", "definition": "Takeaway food. From Cantonese 打包 (dá bāo)."}
]

# Corpus Construction
corpus = [f"{e['term']} {e['definition']}" for e in lexicon]
print(f"Doc 0: '{corpus[0]}'")

# Tokenization
tokenized_corpus = [re.findall(r"\w+", doc.lower()) for doc in corpus]
print(f"Tokens 0: {tokenized_corpus[0]}")

# Init BM25
bm25 = BM25Okapi(tokenized_corpus)

# Query
query = "reverse car"
tokenized_query = re.findall(r"\w+", query.lower())
print(f"Query Tokens: {tokenized_query}")

# Search
scores = bm25.get_scores(tokenized_query)
print(f"Scores: {scores}")

# Check match
if scores[0] > 0:
    print("✅ MATCH!")
else:
    print("❌ NO MATCH")
