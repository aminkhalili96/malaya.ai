
import sys
import os

sys.path.append(os.path.abspath("data/malaya_raw"))

def count_entries(module_name, var_name="words"):
    try:
        module = __import__(module_name)
        data = getattr(module, var_name, [])
        return len(data)
    except Exception as e:
        return f"Error: {e}"

files_to_check = [
    ("kamus_dewan", "words", "Standard Dictionary"),
    ("words", "words", "General Vocabulary"),
    ("rules", "rules_normalizer", "Normalization Rules"),
    ("tatabahasa", "stopwords", "Stopwords"),
    ("tatabahasa", "tanya_list", "Kata Tanya"),
    ("tatabahasa", "laughing", "Noise/Laughing"),
    ("dbp", "words", "DBP Dictionary"),
    ("places", "places", "Places/Locations"),
    ("parlimen", "parlimen", "Parliament Info"),
    ("negeri", "negeri", "States Info"),
    ("city", "city", "Cities List"),
    # Derived from places.py via keyword counting
    ("places", "places", "Schools (est)", lambda x: len([i for i in x if 'sekolah' in i.lower()])),
    ("places", "places", "Hospitals/Clinics (est)", lambda x: len([i for i in x if 'hospital' in i.lower() or 'klinik' in i.lower()]))
]

for item in files_to_check:
    if len(item) == 4:
        mod, var, desc, func = item
        try:
            module = __import__(mod)
            data = getattr(module, var, [])
            count = func(data)
        except: count = "Error"
    else:
        mod, var, desc = item
        count = count_entries(mod, var)
    
    print(f"| {desc} | {mod}.py | {count} | Extracted from Malaya NLP |")
