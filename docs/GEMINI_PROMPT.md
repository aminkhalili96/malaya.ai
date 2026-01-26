# PROMPT FOR GEMINI-3 PRO: Generate Malaysian Language Data

## YOUR TASK

I am building a production-grade Malaysian AI chatbot called **Malaya LLM**. I need you to generate comprehensive Malaysian language data that will be used to help an LLM (Qwen 2.5 7B) understand:
- Malaysian slang and shortforms
- All 6 major Malaysian dialects
- Malaysian facts and culture
- Manglish (Malaysian English)

**Target**: The chatbot must score 95%+ on understanding Malay/Manglish queries.

---

## TASK 1: SHORTFORMS DICTIONARY (10,000+ entries)

Generate a JSON file with Malaysian shortforms/abbreviations used in texting and social media.

**Output File**: `data/dictionaries/shortforms.json`

**Schema**:
```json
{
  "shortforms": [
    {
      "short": "xleh",
      "full": "tak boleh",
      "english": "cannot",
      "category": "common",
      "examples": ["xleh la bro", "aku xleh pergi"]
    }
  ]
}
```

**Requirements**:
- 10,000+ entries minimum
- Categories: common, vowel_drops, number_substitutions, hybrid
- Include ALL common Malaysian text abbreviations
- Must include: xde, nk, tk, dh, jd, bg, lg, sgt, mcm, cmne, ape, ni, tu, je, tp, sbb, psl, klu, blh, xpe, nnt, skrg, hr, mgu, bln, thn, org, brg, krg, yg, dgn, utk, kpd, drp, byk, skit, etc.

---

## TASK 2: DIALECT DICTIONARIES (2,000+ per dialect)

Generate 6 separate JSON files for each Malaysian dialect.

**Output Files**: 
- `data/dictionaries/dialects/kelantan.json`
- `data/dictionaries/dialects/terengganu.json`
- `data/dictionaries/dialects/penang.json`
- `data/dictionaries/dialects/negeri_sembilan.json`
- `data/dictionaries/dialects/sabah.json`
- `data/dictionaries/dialects/sarawak.json`

**Schema**:
```json
{
  "dialect": "kelantan",
  "words": [
    {
      "dialect_word": "gapo",
      "standard_malay": "apa",
      "english": "what",
      "usage_examples": ["gapo khabar?", "demo buat gapo?"]
    }
  ],
  "phrases": [
    {
      "dialect_phrase": "demo nok gi mano",
      "standard_malay": "awak nak pergi mana",
      "english": "where are you going"
    }
  ]
}
```

**Must Include for each dialect**:

### Kelantan:
ambo, kawe, demo, gapo, guano, make, gok, nok, dop, mugo, kito, ore, maghi, buleh, sapa, sokmo, toksey, ggaduh, nate, kecek, etc.

### Terengganu:
mung, kekgi, dok, wak, ning, guane, bakpe, sokmo, tranung, kelih, ghalik, etc.

### Penang:
hang, pasai, awat, habaq, mai, pi, lagu mana, kang, lor, apa pasal, etc.

### Negeri Sembilan:
den, aden, ekau, apo, kono, ghoman, sodap, tido, ghomah, etc.

### Sabah:
bah, sia, buli, nda, ndak, bilang, sana, sinun, tinguk, ko, kau, etc.

### Sarawak:
kamek, kitak, sik, maok, dolok, kelak, polah, agik, apa hal, nangga, etc.

---

## TASK 3: SLANG DICTIONARY (5,000+ entries)

Generate comprehensive Malaysian slang terms.

**Output File**: `data/dictionaries/slang.json`

**Schema**:
```json
{
  "slang_terms": [
    {
      "term": "padu",
      "meanings": ["awesome", "solid", "impressive"],
      "sentiment": "positive",
      "examples": ["Padu gila performance dia!", "Kau memang padu la"],
      "similar_terms": ["power", "gempak", "terror"]
    }
  ]
}
```

**Must Include**:
- Positive: padu, gempak, terror, power, steady, best, mantap, syok, havoc, solid, etc.
- Negative: koyak, fail, sial, celaka, hampeh, lembab, noob, etc.
- Intensifiers: gila, bapak, siot, teruk, habis, melampau, etc.
- Actions: lepak, yumcha, tapau, belanja, kantoi, etc.
- Youth slang, gaming terms, social media terms

---

## TASK 4: PARTICLES DICTIONARY (50+ detailed entries)

Generate detailed analysis of Malaysian particles.

**Output File**: `data/dictionaries/particles.json`

**Schema**:
```json
{
  "particles": [
    {
      "particle": "lah",
      "functions": ["softener", "emphasis", "persuasion"],
      "emotional_examples": {
        "friendly": "Jom lah pergi sama",
        "impatient": "Cepat lah!",
        "reassuring": "Takpe lah"
      },
      "cannot_use_in": ["formal writing", "official documents"]
    }
  ]
}
```

**Must Include**:
lah, meh, lor, kan, kot, gak/jugak, je/aje, pun, dah, nak, bah (Sabah), sik (Sarawak), eh, wei/woi, oi, ya/ye, ke, tak, etc.

---

## TASK 5: MALAYSIAN FACTS DATABASE (10,000+ entries)

Generate a comprehensive Malaysian knowledge base.

**Output File**: `data/knowledge/malaysian_facts.json`

**Schema**:
```json
{
  "facts": [
    {
      "id": "gov_001",
      "category": "government",
      "question_patterns": ["siapa PM malaysia", "sape PM sekarang"],
      "answer": "Dato' Seri Anwar Ibrahim",
      "context": "Perdana Menteri ke-10, dilantik November 2022",
      "source": "official"
    }
  ]
}
```

**Categories Required** (with minimum entries):
- Government (500): PM, ministers, agencies, states
- Geography (500): States, cities, landmarks
- Culture (1000): Festivals, traditions, food
- Education (500): Schools, universities, examinations
- Daily Services (1000): JPJ, JPN, hospitals, banks
- History (500): Historical facts, figures
- Food (1000): Dishes, ingredients, recipes
- Sports (300): Athletes, achievements
- Entertainment (500): Artists, movies, music
- Economy (200): Companies, industries

---

## TASK 6: CONVERSATION EXAMPLES (5,000+ pairs)

Generate realistic Malaysian conversation pairs.

**Output File**: `data/conversations/malaysian_conversations.jsonl`

**Schema** (JSONL format, one JSON per line):
```json
{"category": "greeting", "language": "manglish", "user": "Eh bro, apa cerita?", "response": "Biasa je la, kau macam mana?", "tone": "friendly"}
```

**Categories**:
- Greetings (500)
- Asking for help (500)
- Food ordering (400)
- Complaints (400)
- Making plans (400)
- Seeking information (500)
- Dialect conversations (1000) - cover all 6 dialects
- Informal chat (1000)
- Formal requests (300)

---

## TASK 7: MANGLISH PATTERNS (2,000+ patterns)

Generate code-switching and Manglish grammar patterns.

**Output File**: `data/dictionaries/manglish_patterns.json`

**Schema**:
```json
{
  "patterns": [
    {
      "pattern": "Got {noun} or not?",
      "examples": ["Got parking or not?", "Got discount or not?"],
      "meaning": "Asking about availability",
      "standard_english": "Is there {noun}?"
    }
  ]
}
```

---

## IMPORTANT GUIDELINES

1. **Be Authentic**: Use real Malaysian expressions, not literal translations
2. **Be Comprehensive**: Cover ALL age groups (youth slang to formal)
3. **Be Current**: Include 2024-2026 current affairs for facts
4. **Be Diverse**: Cover all races (Malay, Chinese, Indian, East Malaysian)
5. **Include Examples**: Every entry should have usage examples
6. **Follow Schema Exactly**: Output must be valid JSON matching the schemas above

---

## OUTPUT ORDER

Generate in this order (can do across multiple responses):
1. Shortforms (most critical)
2. Dialects (6 files)
3. Slang
4. Particles
5. Malaysian Facts
6. Conversations
7. Manglish Patterns

---

## START NOW

Begin with **TASK 1: SHORTFORMS DICTIONARY**. Generate the first 500 entries in the exact JSON format specified. I will ask for more in batches.

Format your response as:
```json
{
  "shortforms": [
    ... entries here ...
  ]
}
```
