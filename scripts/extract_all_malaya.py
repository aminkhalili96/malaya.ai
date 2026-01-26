
import sys
import json
import os
import re

# Add local directory to path to allow importing data/malaya_raw files
sys.path.append(os.path.abspath("data/malaya_raw"))

def save_json(data, folder, filename):
    path = os.path.join(folder, filename)
    os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {path} with {len(data) if isinstance(data, list) else len(data.keys())} entries")

def extract_set_to_list(module, var_name):
    if hasattr(module, var_name):
        val = getattr(module, var_name)
        return sorted(list(val))
    return []

def main():
    print("Starting Massive Malaya Data Extraction...")
    
    # Import modules dynamically to avoid crashing if one is missing
    try:
        import kamus_dewan
        import dbp
        import words
        import rules
        import tatabahasa
        import places
        import parlimen
        import city
        import negeri
        import country
    except ImportError as e:
        print(f"Error importing modules: {e}")
        return

    # 1. Standard Dictionary (Kamus Dewan)
    print("Extracting Standard Dictionary...")
    standard_words = extract_set_to_list(kamus_dewan, 'words')
    save_json({"words": standard_words}, "data/dictionaries", "malaya_standard.json")

    # 2. DBP Formal Terms
    print("Extracting DBP Terms...")
    dbp_words = extract_set_to_list(dbp, 'words')
    save_json({"words": dbp_words}, "data/dictionaries", "malaya_formal.json")

    # 3. General Vocabulary
    print("Extracting General Vocab...")
    gen_words = extract_set_to_list(words, 'words')
    save_json({"words": gen_words}, "data/dictionaries", "malaya_vocab.json")

    # 4. Shortforms (Normalization)
    print("Extracting Shortforms...")
    if hasattr(rules, 'rules_normalizer'):
        shortforms_data = []
        for short, full in rules.rules_normalizer.items():
            shortforms_data.append({
                "short": short,
                "full": full,
                "context": "general"
            })
        save_json({"shortforms": shortforms_data}, "data/dictionaries", "malaya_shortforms.json")

    # 5. Places (Filtered)
    print("Extracting Places & Entities...")
    all_places = []
    if hasattr(places, 'places'):
        all_places = sorted(list(places.places))
        
        # Filter Schools
        schools = [p for p in all_places if 'sekolah' in p.lower() or 'smk' in p.lower() or 'sk ' in p.lower()]
        save_json({"entities": schools, "type": "school"}, "data/knowledge", "entities_schools.json")
        
        # Filter Medical
        medical = [p for p in all_places if 'hospital' in p.lower() or 'klinik' in p.lower() or 'pusat perubatan' in p.lower()]
        save_json({"entities": medical, "type": "medical"}, "data/knowledge", "entities_medical.json")
        
        # Save All Places
        save_json({"places": all_places}, "data/knowledge", "locations_malaysia.json")

    # 6. Cities
    print("Extracting Cities...")
    cities = extract_set_to_list(city, 'city')
    save_json({"cities": cities}, "data/knowledge", "cities.json")

    # 7. Parliament
    print("Extracting Parse...")
    parlimen_data = []
    if hasattr(parlimen, 'parlimen'):
        p_data = parlimen.parlimen
        # Convert to list of objects if it's a dict or just keys
        if isinstance(p_data, dict):
             # assuming dict is state -> list of parliaments or similar
             # Let's flatten if needed, but if it's simple usage, just dump it
             # Actually p_data might be a set of parliament names. Let's check type safely.
             pass 
        if isinstance(p_data, (set, list)):
            parlimen_list = sorted(list(p_data))
            # Wrap as objects
            parlimen_data = [{"seat": p} for p in parlimen_list]
    
    if parlimen_data:
        save_json({"parliament_seats": parlimen_data}, "data/knowledge", "politics.json")

    # 8. Geography (States & Countries)
    print("Extracting Geography...")
    states = extract_set_to_list(negeri, 'negeri')
    countries = extract_set_to_list(country, 'country')
    
    geo_data = {
        "states": states,
        "countries": countries
    }
    save_json(geo_data, "data/knowledge", "geography.json")

    # 9. Stopwords (Redoing for completeness)
    print("Extracting Stopwords...")
    stopwords = extract_set_to_list(tatabahasa, 'stopwords')
    save_json({"stopwords": stopwords}, "data/dictionaries", "malaya_stopwords.json")

    print("Massive Extraction Complete!")

if __name__ == "__main__":
    main()
