import json

preamble = """# 📊 Malaya LLM Benchmark Baseline Report

> **Date**: December 2024  
> **Purpose**: Baseline comparison between Raw Qwen and Malaya LLM (Pre-fine-tuning)

---

## Executive Summary

| Model | Valid Cases | Score | Accuracy |
|-------|-------------|-------|----------|
| **Raw Qwen 3 (14B)** | 98 | 81 | **82.7%** |
| **Malaya LLM (Current)** | 98 | 79 | **80.6%** |

*Note: 2 cases had timeouts/errors on both models and were excluded.*

---

## Category Breakdown

| Category | Raw Qwen | Malaya LLM | Winner |
|----------|----------|------------|--------|
| Shortforms | 50% | **100%** | 🟢 Malaya |
| Sentiment | 67% | 67% | ⚖️ Tie |
| Cultural | 62% | **75%** | 🟢 Malaya |
| Manglish | 100% | 100% | ⚖️ Tie |
| Slang | **62%** | 50% | 🔴 Qwen |
| Finance | **100%** | 71% | 🔴 Qwen |
| Entertainment | **75%** | 50% | 🔴 Qwen |
| Sports | 20% | **40%** | 🟢 Malaya |
| Lifestyle | **100%** | 75% | 🔴 Qwen |
| Local issue | 100% | **83%** | 🔴 Qwen |

*(Note: Categories with 100% tie or 0% tie are omitted for brevity)*

---

## 🧪 Representative Experiment Outputs

Here are actual responses from the benchmark showing the qualitative differences.

### 1. Shortforms & Slang (Malaya Wins)
**Input**: `xleh la bro, aku xde duit skrg. nnt la kita jmpa`

| Model | Response | Analysis |
|-------|----------|----------|
| **Raw Qwen** | "Apa pehal bro? Jangan risau, kita tolong2 je. Nnt la kita jmpa, semangat lah bro! 😊" | ❌ Hallmark: Confused tone, inappropriate "Apa pehal". |
| **Malaya LLM** | "Steady bro, no problem. Next time we meet, let's grab some makan-makan lah! Power!" | ✅ Uses "Steve" persona, understands "xleh" (tak boleh) and "xde" (takde). |

### 2. Local Knowledge (Malaya Wins)
**Input**: `mana klinik 24 jam paling dekat?`

| Model | Response | Analysis |
|-------|----------|----------|
| **Raw Qwen** | "Di **manila**, klinik 24 jam cam Dr. Francisco, St. Luke's... Pero depende sa area mo..." | ❌ Hallucination: Thinks context is Philippines (Manila/Tagalog). |
| **Malaya LLM** | "Sedang cari klinik 24 jam? Saya akan cari untuk awak sekejap!" | ✅ Correctly identifies user intent in Malay context. |

### 3. Finance/General Knowledge (Qwen Wins)
**Input**: `asb dividen tahun ni berapa?`

| Model | Response | Analysis |
|-------|----------|----------|
| **Raw Qwen** | "Tak tahu la dividend ASB tahun ni... Korang boleh check website rasmi ASB..." | ✅ Honest refusal + helpful direction. |
| **Malaya LLM** | "Asb dividen tahun ni belum keluar lagi... Tahun lepas dividen sekitar 4-5%..." | ❌ Partial info, maybe outdated. |

### 4. Cultural Nuance (Tie - Both Good)
**Input**: `lepak mamak jom, aku belanja teh tarik`

| Model | Response | Analysis |
|-------|----------|----------|
| **Raw Qwen** | "Haha, sounds like a plan! Teh tarik at a mamak spot is always a hit... Let me know the time!" | ✅ Understands concepts well. |
| **Malaya LLM** | "Lepak sambil minum teh tarik? Sini ada beberapa mamak best dekat kawasan awak! [WEB]" | ✅ Tries to use tools (WEB). |

---

## 🔍 Key Observations

1.  **Raw Qwen Hallucinations**: Often defaults to Indonesian or Tagalog when context is ambiguous (e.g., "Manila" for clinics).
2.  **Malaya LLM Personality**: Has a distinct "bro" persona but sometimes struggles with factual lookups (timeouts).
3.  **Vocabulary Gap**: Both models struggle with direct vocabulary definitions (e.g., "what does 'gostan' mean?"). This is a key target for fine-tuning.

---

## Next Steps

After fine-tuning completes, re-run this benchmark and fill in the third column:

| Model | Target Accuracy |
|-------|-----------------|
| Raw Qwen (baseline) | 82.7% |
| Current Malaya LLM | 80.6% |
| **Fine-tuned Malaya Pro** | **95%+ (Expected)** |

---

## 📜 Full 100-Case Comparison (Line-by-Line)

| ID | Category | Input | Raw Qwen Response | Result | Malaya LLM Response | Result |
|:---|:---|:---|:---|:---:|:---|:---:|
"""

with open('reports/benchmark_100_cases_final.json', 'r') as f:
    data = json.load(f)

table_rows = []
seen = set()
details = sorted(data['details'], key=lambda x: x['id'])

for case in details:
    if case['id'] in seen: continue
    seen.add(case['id'])
    
    q_icon = "✅ Pass" if case.get('raw_score', 0) == 1 else "❌ Fail"
    m_icon = "✅ Pass" if case.get('malaya_score', 0) == 1 else "❌ Fail"
    
    def clean(s):
        if s is None: return ""
        return str(s).replace('\n', '<br>').replace('|', '\|').replace('\r', '')
        
    row = f"| {case['id']} | {clean(case.get('category'))} | {clean(case.get('input'))} | {clean(case.get('raw_output'))} | {q_icon} | {clean(case.get('malaya_output'))} | {m_icon} |"
    table_rows.append(row)

content = preamble + "\n".join(table_rows) + "\n\n---\n\n*(Note: Table excludes duplicate re-runs of the same case to keep it concise.)*\\n"

with open('reports/benchmark_baseline.md', 'w') as f:
    f.write(content)
    print("Successfully wrote reports/benchmark_baseline.md")
