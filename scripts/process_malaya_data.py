
import sys
import json
import os

# Add local directory to path to allow importing data/malaya_raw files
sys.path.append(os.path.abspath("data/malaya_raw"))

try:
    import tatabahasa
    import rules
except ImportError as e:
    print(f"Error importing Malaya raw files: {e}")
    sys.exit(1)

def save_json(data, filename):
    path = os.path.join("data/dictionaries", filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {path}")

def main():
    print("Extracting data from Malaya raw files...")
    
    # 1. Extract Shortforms (Normalization Rules)
    if hasattr(rules, 'rules_normalizer'):
        shortforms_data = []
        for short, full in rules.rules_normalizer.items():
            shortforms_data.append({
                "short": short,
                "full": full,
                "context": "general"
            })
        
        # Save validation check
        if shortforms_data:
            save_json({"shortforms": shortforms_data}, "malaya_shortforms.json")
        else:
            print("No rules_normalizer found.")

    # 2. Extract Stopwords
    if hasattr(tatabahasa, 'stopwords'):
        # Convert set/list to list
        stopwords = list(tatabahasa.stopwords)
        stopwords.sort()
        save_json({"stopwords": stopwords}, "malaya_stopwords.json")

    # 3. Extract Grammar Lists
    grammar_data = {}
    grammar_keys = [
        "tanya_list", "perintah_list", "pangkal_list", "bantu_list",
        "penguat_list", "penegas_list", "nafi_list", "pemeri_list",
        "sendi_list", "pembenar_list", "gantinama_list", "penjodoh_bilangan"
    ]
    
    for key in grammar_keys:
        if hasattr(tatabahasa, key):
            val = getattr(tatabahasa, key)
            # Handle if it's a list or set
            if isinstance(val, (list, set, tuple)):
                grammar_data[key] = sorted(list(val))
    
    if grammar_data:
        save_json(grammar_data, "malaya_grammar.json")

    # 4. Extract Laughing/Noisy words (useful for filtering/detection)
    noise_data = {}
    if hasattr(tatabahasa, 'laughing'):
        noise_data['laughing'] = sorted(list(tatabahasa.laughing))
    
    if noise_data:
        save_json(noise_data, "malaya_noise.json")

    print("Data extraction complete.")

if __name__ == "__main__":
    main()
