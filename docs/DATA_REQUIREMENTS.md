# Malaya LLM Data Requirements Specification
## Production-Grade Malaysian AI Chatbot

**Version**: 1.0
**Date**: 2026-01-12
**Target**: 95%+ accuracy on Malaysian/Manglish understanding

---

## Overview

This document specifies the data required to build a production-grade Malaysian AI chatbot that can:
- Understand ALL Malaysian dialects (Kelantan, Terengganu, Penang, N9, Sabah, Sarawak)
- Understand Malaysian slang, shortforms, and code-switching (Manglish)
- Know Malaysian facts, culture, history, and current events
- Respond naturally in the user's language/dialect

---

## 1. SHORTFORMS DICTIONARY

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 10,000+ entries minimum |
| **Format** | JSON |
| **File** | `data/dictionaries/shortforms.json` |

### Schema
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

### Categories Required
| Category | Min Entries | Examples |
|----------|-------------|----------|
| **Common Shortforms** | 3,000 | xde, nk, tk, dh, jd, bg, lg |
| **Number Substitutions** | 500 | 4u (for you), 2 (to), b4 (before) |
| **Vowel Drops** | 2,000 | org (orang), brg (barang), krg (kurang) |
| **Consonant Substitutions** | 1,000 | k (ok), r (are), u (you) |
| **Repeated Letters** | 500 | bestttt, sedapppp, cantikkk |
| **Malay-English Hybrid** | 2,000 | psl (pasal/because), sbb (sebab) |
| **Social Media Style** | 1,000 | omg, btw, fyi in Malay context |

### Priority List (MUST HAVE)
```
xde → tidak ada / takde
xleh → tak boleh
nk → nak
tk → tak
dh → dah / sudah
jd → jadi
bg → bagi / abang
lg → lagi
sgt → sangat
mcm → macam
cmne → macam mana
ape → apa
ni → ini
tu → itu
je → sahaja
la/lah → particle
tp → tapi
sbb → sebab
psl → pasal
klu → kalau
blh → boleh
xpe → tak apa
nnt → nanti
skrg → sekarang
hr → hari
mgu → minggu
bln → bulan
thn → tahun
```

---

## 2. DIALECT DICTIONARIES

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 2,000+ entries per dialect (6 dialects) |
| **Total** | 12,000+ entries |
| **Format** | JSON |
| **Files** | `data/dictionaries/dialects/{dialect}.json` |

### Schema
```json
{
  "dialect": "kelantan",
  "words": [
    {
      "dialect_word": "gapo",
      "standard_malay": "apa",
      "english": "what",
      "pronunciation_hint": "ga-po",
      "usage_examples": ["gapo khabar?", "demo buat gapo?"],
      "notes": "Very common, used in all contexts"
    }
  ],
  "phrases": [
    {
      "dialect_phrase": "demo nok gi mano",
      "standard_malay": "awak nak pergi mana",
      "english": "where are you going",
      "context": "casual greeting"
    }
  ],
  "grammar_notes": [
    "Kelantanese often drops final consonants",
    "'R' at end of words often becomes 'gh' sound"
  ]
}
```

### Dialect Requirements

#### 2.1 Kelantan (Kelate)
| Type | Min Entries |
|------|-------------|
| Words | 2,500 |
| Phrases | 500 |
| Grammar Rules | 50 |

**Must Include:**
- ambo/kawe = saya
- demo = awak
- gapo = apa
- guano = macam mana
- make/gok = makan
- nok = nak
- dop = tidak
- mugo = muka
- kito = kita
- ore = orang

#### 2.2 Terengganu (Ganu)
| Type | Min Entries |
|------|-------------|
| Words | 2,000 |
| Phrases | 400 |
| Grammar Rules | 40 |

**Must Include:**
- mung = awak
- kekgi = nanti
- dok = tidak/sedang
- wak = buat
- ning = ini
- tu = itu
- guane = macam mana
- bakpe = kenapa
- sokmo = selalu

#### 2.3 Penang (Hokkien-Malay)
| Type | Min Entries |
|------|-------------|
| Words | 2,000 |
| Phrases | 400 |
| Grammar Rules | 30 |

**Must Include:**
- hang = awak/kamu
- pasai = pasal/kerana
- awat = kenapa
- habaq = cakap/beritahu
- mai = mari
- pi = pergi
- lagu mana = macam mana
- kang = nanti/kalau tidak

#### 2.4 Negeri Sembilan (N9)
| Type | Min Entries |
|------|-------------|
| Words | 1,500 |
| Phrases | 300 |
| Grammar Rules | 30 |

**Must Include:**
- den/aden = saya
- kau/ekau = awak
- apo = apa
- kono = betul/perlu
- ghoman = macam mana
- sodap = sedap
- tido = tidur

#### 2.5 Sabah (Sabahan)
| Type | Min Entries |
|------|-------------|
| Words | 2,000 |
| Phrases | 400 |
| Grammar Rules | 30 |

**Must Include:**
- bah = particle (like lah)
- sia/saya = saya
- kau/ko = awak
- buli = boleh
- nda/ndak = tidak
- bilang = cakap
- sudah bah = sudahlah
- sinun = sana
- sini = di sini

#### 2.6 Sarawak (Sarawakian)
| Type | Min Entries |
|------|-------------|
| Words | 2,000 |
| Phrases | 400 |
| Grammar Rules | 30 |

**Must Include:**
- kamek = saya
- kitak = awak
- sik = tidak
- maok = mahu
- dolok = dulu
- kelak = nanti
- apa hal = kenapa
- polah = buat
- agik = lagi

---

## 3. SLANG & COLLOQUIAL DICTIONARY

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 5,000+ entries |
| **Format** | JSON |
| **File** | `data/dictionaries/slang.json` |

### Schema
```json
{
  "slang_terms": [
    {
      "term": "padu",
      "meanings": ["awesome", "solid", "impressive"],
      "origin": "Malay",
      "usage": "casual",
      "sentiment": "positive",
      "examples": ["Padu gila performance dia!", "Kau memang padu la"],
      "similar_terms": ["power", "gempak", "terror"]
    }
  ]
}
```

### Categories Required

| Category | Min Entries | Description |
|----------|-------------|-------------|
| **Positive Expressions** | 500 | padu, gempak, terror, power, steady, best |
| **Negative Expressions** | 500 | koyak, fail, sial, celaka, bodoh |
| **Intensifiers** | 300 | gila, bapak, siot, teruk, habis |
| **Actions/Verbs** | 800 | lepak, yumcha, tapau, belanja |
| **Social Media Slang** | 500 | viral, cancel, slay (Malaysian context) |
| **Youth Slang (Gen Z)** | 500 | skibidi, rizz, lowkey in MY context |
| **Gaming Slang** | 300 | noob, carry, feed, gank |
| **Food/Eating** | 400 | makan, tapau, belanja, sedap |
| **Money/Work** | 400 | gaji, duit, broke, kaya |
| **Relationships** | 500 | couple, dating, single, crush |
| **Emotions** | 300 | stress, happy, sedih, geram |

---

## 4. MALAYSIAN PARTICLES

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 50+ particles with full analysis |
| **Format** | JSON |
| **File** | `data/dictionaries/particles.json` |

### Schema
```json
{
  "particles": [
    {
      "particle": "lah",
      "functions": ["softener", "emphasis", "persuasion"],
      "emotional_context": {
        "friendly": "Jom lah, kita pergi sama",
        "impatient": "Cepat lah!",
        "reassuring": "Takpe lah, next time"
      },
      "position": "end of sentence",
      "cannot_use_with": ["formal writing"],
      "combinations": ["kan lah", "je lah"]
    }
  ]
}
```

### Particles List (MUST INCLUDE ALL)
```
lah - softener/emphasis
meh - skepticism/invitation
lor - resignation/acceptance
kan - seeking confirmation
kot - uncertainty
gak/jugak - also/too
je/aje - only/just
pun - also/even
dah - already/done
nak - want/about to
per - (Penang) question marker
bah - (Sabah) emphasis
sik - (Sarawak) negation
eh - surprise/attention
wei/woi - calling attention
oi - calling someone
ya/ye - right?/yes?
ke - question marker
tak - negation/question
```

---

## 5. MALAYSIAN KNOWLEDGE BASE

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 10,000+ facts |
| **Format** | JSON |
| **File** | `data/knowledge/malaysian_facts.json` |

### Schema
```json
{
  "facts": [
    {
      "id": "gov_001",
      "category": "government",
      "question_patterns": [
        "siapa PM malaysia",
        "sape PM sekarang",
        "who is the prime minister"
      ],
      "answer": "Dato' Seri Anwar Ibrahim",
      "context": "Dilantik pada 24 November 2022 sebagai Perdana Menteri ke-10 Malaysia",
      "last_verified": "2026-01-01",
      "source": "official"
    }
  ]
}
```

### Categories Required

#### 5.1 Government & Politics
| Sub-category | Min Entries |
|--------------|-------------|
| Current Government | 200 |
| State Governments | 150 |
| Government Agencies | 300 |
| Political Parties | 100 |
| Laws & Regulations | 200 |

#### 5.2 Geography
| Sub-category | Min Entries |
|--------------|-------------|
| States & Territories | 50 |
| Major Cities | 200 |
| Tourist Attractions | 500 |
| Districts | 200 |
| Landmarks | 300 |

#### 5.3 Culture & Traditions
| Sub-category | Min Entries |
|--------------|-------------|
| Festivals (all races) | 100 |
| Traditional Customs | 200 |
| Traditional Food | 500 |
| Traditional Attire | 100 |
| Arts & Music | 200 |
| Superstitions/Pantang | 200 |

#### 5.4 Education
| Sub-category | Min Entries |
|--------------|-------------|
| Education System | 100 |
| Universities | 200 |
| Examinations (UPSR, PT3, SPM, STPM) | 100 |
| Scholarships (PTPTN, JPA, etc) | 100 |
| Schools | 200 |

#### 5.5 Daily Life & Services
| Sub-category | Min Entries |
|--------------|-------------|
| Government Services (JPJ, JPN, etc) | 300 |
| Utilities (TNB, Syabas, etc) | 100 |
| Healthcare | 200 |
| Transportation | 200 |
| Banking | 150 |
| Telecommunications | 100 |

#### 5.6 History
| Sub-category | Min Entries |
|--------------|-------------|
| Pre-colonial History | 200 |
| Colonial Era | 200 |
| Independence | 100 |
| Modern History | 200 |
| Historical Figures | 300 |

#### 5.7 Food & Cuisine
| Sub-category | Min Entries |
|--------------|-------------|
| Dishes by State | 500 |
| Ingredients | 200 |
| Cooking Methods | 100 |
| Restaurants/Hawkers | 200 |
| Recipes | 300 |

#### 5.8 Sports
| Sub-category | Min Entries |
|--------------|-------------|
| National Athletes | 200 |
| Sports History | 100 |
| Stadiums & Venues | 50 |
| Achievements | 100 |

#### 5.9 Entertainment
| Sub-category | Min Entries |
|--------------|-------------|
| Local Artists | 300 |
| Movies & Drama | 200 |
| TV Shows | 100 |
| Music | 200 |

#### 5.10 Economy & Business
| Sub-category | Min Entries |
|--------------|-------------|
| Major Companies | 200 |
| Economic Terms | 100 |
| Currency/Finance | 100 |
| Industries | 150 |

---

## 6. CONVERSATION EXAMPLES

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 5,000+ conversation pairs |
| **Format** | JSONL |
| **File** | `data/conversations/malaysian_conversations.jsonl` |

### Schema
```json
{
  "id": "conv_001",
  "category": "casual_greeting",
  "language": "manglish",
  "user": "Eh bro, apa cerita?",
  "response": "Biasa je la, kau macam mana?",
  "tone": "friendly",
  "dialect": "standard",
  "context": "friends meeting"
}
```

### Categories Required

| Category | Min Pairs | Description |
|----------|-----------|-------------|
| **Casual Greetings** | 500 | Apa khabar, apa cerita, etc |
| **Asking for Help** | 500 | Tolong, macam mana nak... |
| **Giving Directions** | 300 | Pi straight, belok kiri... |
| **Food Ordering** | 400 | Satu teh tarik, boss... |
| **Complaints** | 400 | Lambat gila, service teruk... |
| **Expressing Emotions** | 500 | Happy, sad, angry... |
| **Making Plans** | 400 | Jom lepak, nak pergi... |
| **Seeking Information** | 500 | Macam mana nak, kat mana... |
| **Giving Opinions** | 400 | Best gila, tak best la... |
| **Negotiations** | 300 | Boleh kurang tak, mahal... |
| **Formal Requests** | 300 | Saya ingin mohon... |
| **Dialect Conversations** | 1,000 | All 6 dialects |

---

## 7. MANGLISH PATTERNS

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 2,000+ patterns |
| **Format** | JSON |
| **File** | `data/dictionaries/manglish_patterns.json` |

### Schema
```json
{
  "patterns": [
    {
      "pattern": "{english} + lah",
      "examples": ["Cannot lah", "Sure lah", "OK lah"],
      "meaning": "Softened English statement",
      "frequency": "very common"
    },
    {
      "pattern": "Got {noun} or not?",
      "examples": ["Got parking or not?", "Got discount or not?"],
      "meaning": "Asking about availability",
      "standard_english": "Is there {noun}?"
    }
  ]
}
```

### Pattern Categories
| Category | Min Patterns |
|----------|--------------|
| Question Formations | 300 |
| Code-Switching Rules | 400 |
| Particle Usage | 200 |
| Grammar Deviations | 300 |
| Common Expressions | 500 |
| Sentence Structures | 300 |

---

## 8. SENTIMENT & EMOTION MAPPINGS

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 3,000+ expressions |
| **Format** | JSON |
| **File** | `data/dictionaries/sentiment_expressions.json` |

### Schema
```json
{
  "expressions": [
    {
      "expression": "geram betul",
      "sentiment": "negative",
      "emotion": "anger",
      "intensity": "high",
      "appropriate_response_tone": "calming, apologetic",
      "example_responses": [
        "Sabar je la, aku faham frustration tu",
        "Memang la menyampah, tapi cuba cool down dulu"
      ]
    }
  ]
}
```

---

## 9. CULTURAL CONTEXT DATA

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 1,000+ cultural notes |
| **Format** | JSON |
| **File** | `data/knowledge/cultural_context.json` |

### Schema
```json
{
  "cultural_notes": [
    {
      "topic": "pantang_larang_mengandung",
      "description": "Traditional pregnancy taboos",
      "content": [
        "Jangan duduk di tangga - dipercayai susah nak bersalin",
        "Jangan makan nanas - dipercayai boleh keguguran",
        "Jangan keluar waktu maghrib"
      ],
      "modern_perspective": "Many are superstitions without scientific basis, but deeply respected",
      "response_guidance": "Be respectful of traditional beliefs while acknowledging modern views"
    }
  ]
}
```

---

## 10. ERROR CORRECTION PAIRS

### Requirements
| Attribute | Value |
|-----------|-------|
| **Quantity** | 2,000+ pairs |
| **Format** | JSON |
| **File** | `data/training/error_corrections.json` |

### Schema
```json
{
  "corrections": [
    {
      "incorrect_response": "I don't understand Malaysian slang",
      "context": "User asked using 'xleh'",
      "correct_response": "Faham, takpe. Kita reschedule je la.",
      "issue": "Model failed to understand shortform 'xleh'",
      "lesson": "xleh = tak boleh (cannot)"
    }
  ]
}
```

---

## SUMMARY: TOTAL DATA REQUIREMENTS

| Category | Quantity | Format |
|----------|----------|--------|
| Shortforms | 10,000+ | JSON |
| Dialect Words (6 dialects) | 12,000+ | JSON |
| Slang Terms | 5,000+ | JSON |
| Particles | 50+ (detailed) | JSON |
| Malaysian Facts | 10,000+ | JSON |
| Conversation Pairs | 5,000+ | JSONL |
| Manglish Patterns | 2,000+ | JSON |
| Sentiment Expressions | 3,000+ | JSON |
| Cultural Notes | 1,000+ | JSON |
| Error Corrections | 2,000+ | JSON |
| **TOTAL** | **~50,000+ entries** | Mixed |

---

## FILE STRUCTURE

```
data/
├── dictionaries/
│   ├── shortforms.json
│   ├── slang.json
│   ├── particles.json
│   ├── manglish_patterns.json
│   ├── sentiment_expressions.json
│   └── dialects/
│       ├── kelantan.json
│       ├── terengganu.json
│       ├── penang.json
│       ├── negeri_sembilan.json
│       ├── sabah.json
│       └── sarawak.json
├── knowledge/
│   ├── malaysian_facts.json
│   └── cultural_context.json
├── conversations/
│   └── malaysian_conversations.jsonl
└── training/
    └── error_corrections.json
```

---

## QUALITY STANDARDS

1. **Accuracy**: All facts must be verifiable
2. **Recency**: Government/current affairs must be up to date (2024-2026)
3. **Authenticity**: Slang/dialect must reflect actual usage, not dictionary definitions
4. **Diversity**: Cover all major ethnic groups (Malay, Chinese, Indian, East Malaysian)
5. **Completeness**: Each entry should have examples, not just definitions
6. **Consistency**: Follow the schema exactly for easy parsing

---

## NOTES FOR DATA GENERATOR

1. **Don't translate literally** - Capture the feel and context
2. **Include regional variations** - Same word may differ by state
3. **Cover all age groups** - Youth slang differs from older generation
4. **Include code-switching** - Real Malaysians mix languages constantly
5. **Be culturally sensitive** - Avoid stereotypes, respect all races
6. **Include practical info** - How to renew license, pay bills, etc.

---

*This document specifies the data requirements for Malaya LLM v3 - Production Grade Malaysian AI*

---

## 11. INTEGRATED EXTERNAL DATA (Malaya NLP)

Data extracted from `malaya` library version 5.1.1.

| File | Description | Source | Count | Usage |
|------|-------------|--------|-------|-------|
| `data/dictionaries/malaya_standard.json` | Standard Malay Dictionary | `malaya..kamus_dewan` | **57,632** | Vocabulary Validation |
| `data/dictionaries/malaya_formal.json` | DBP Official Terms | `malaya..dbp` | **48,341** | Formal Language RAG |
| `data/dictionaries/malaya_vocab.json` | General Vocabulary | `malaya..words` | **24,421** | Synonyms / Expansion |
| `data/knowledge/locations_malaysia.json` | Places & Locations | `malaya..places` | **43,834** | Geo-Entity Recognition |
| `data/dictionaries/malaya_shortforms.json` | Shortform Rules | `malaya..rules` | **3,374** | Text Normalization |
| `data/dictionaries/malaya_stopwords.json` | Stopwords | `malaya..tatabahasa` | **1,253** | RAG Filtering |
| `data/knowledge/entities_schools.json` | Schools (est) | `malaya..places` (filtered) | **~358** | Entity Recon |
| `data/knowledge/entities_medical.json` | Hospitals/Clinics (est) | `malaya..places` (filtered) | **~96** | Entity Recon |
| `data/knowledge/cities.json` | Cities List | `malaya..city` | **445** | Geo-Entity Recognition |
| `data/knowledge/politics.json` | Parliament Info | `malaya..parlimen` | **222** | Political Context |
| `data/knowledge/geography.json` | States & Countries | `malaya..negeri/country` | **~250** | Geo-Context |
| `data/dictionaries/malaya_grammar.json` | Grammar Rules | `malaya..tatabahasa` | **50+** | Syntax Checking |

**Total Extracted Entries: ~180,000+**



