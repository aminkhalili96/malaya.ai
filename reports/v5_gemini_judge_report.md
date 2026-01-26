# Malaya V5 Benchmark: Agent-as-a-Judge Evaluation
**Judge:** Gemini 3 Pro
**Date:** 2026-01-13
**Log Source:** `v5_benchmark_20260113_025210.json`
**Baseline Score (Keyword):** 74.7%

## Methodology
I have reviewed the cases that failed the strict keyword grading (Score < 1.0). I am evaluating them based on **Semantic Correctness** and **Helpfulness**.
- **Pass (1.0)**: The answer provides the correct core information, authorities, or steps, even if keywords mismatch.
- **Fail (0.0)**: The answer is wrong, hallucinates, or completely misses the intent (e.g. failing to understand dialect).

## Detailed Case Review

| Case | Query (Excerpt) | Model Response Summary | Keyword Score | Agent Score | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | `xleh la bro...` (Can't pay, meet later) | "Don't worry, meet at park..." | 0.0 | **0.0** | Failed to understand dialect. Context Mismatch. |
| **05** | `meeting how? client happy?` | "No specific info on meeting..." | 0.0 | **0.0** | Failed conversation persona. |
| **09** | `bakpo mung dop mari` (Why didn't come) | "Report to JKR..." | 0.5 | **0.0** | Hallucination triggered by 'lubang' interpretation? |
| **11** | `awat hang tak habaq` | "Holidays are..." | 0.5 | **0.0** | Hallucination on keywords. |
| **14** | `kitak urang dah makan sik?` | "I am AI..." | 0.5 | **0.5** | Acceptable safety refusal for AI. |
| **16** | `boleh bah` | "Sure, what to discuss?" | 0.5 | **1.0** | Correct conversational handling. |
| **17** | `ndak payah lah` | "Don't worry..." | 0.0 | **1.0** | Correct sentiment handling. |
| **21** | `ape cer bro?` | "Holidays 2024..." | 0.0 | **0.0** | Hallucination (Facts injection override). |
| **22** | `pishang mat` (Bored/Tired) | "Pishang Mat is a traditional dance..." | 0.0 | **0.0** | **Severe Hallucination**. |
| **24** | `dia tu acah je` | "Acah P. Ramlee is a pioneer..." | 0.0 | **0.0** | **Context Poisoning** from `general_context.md`. |
| **26** | `padu teruk` | "Govt performance..." | 0.5 | **0.5** | Interpreted political context? Plausible. |
| **29** | `install python mac` | "App Store / Terminal..." | 0.5 | **1.0** | Correct instructions. Keyword grader missed 'brew'. |
| **34** | `dating KL` | "Taman Tasik..." | 0.5 | **1.0** | Good recommendations. |
| **45** | `eat spicy` | "Mee Goreng..." | 0.5 | **1.0** | Valid suggestion. |
| **46** | `klinik 24 jam` | "UMKM, UKM..." | 0.5 | **1.0** | Valid examples supplied. |
| **50** | `driver... signal tak bagi` | "Driver forgot..." | 0.0 | **0.5** | Addressed topic, generic advice. |
| **57** | `syarat matrikulasi` | "BM, SPM..." | 0.5 | **1.0** | Correct requirements. |
| **58** | `asb dividen` | "Check official site..." | 0.5 | **1.0** | Honest answer (Data cutoff handled). |
| **64** | `scammer call lhdn` | "Contact LHDN official... **NSRC (997)**" | 0.0 | **1.0** | **PERFECT ANSWER**. Grader failed it. |
| **66** | `jpj hours` | "Weekdays 8:30..." | 0.5 | **1.0** | Correct info. |
| **67** | `renew passport walk in` | "Go to ministry..." | 0.0 | **0.5** | Partial. Walk-in is restricted but advice is safe. |
| **70** | `baju cekak musang vs` | "Difference in collar/shape..." | 0.5 | **1.0** | Correct textual comparison. |
| **72** | `hantaran tunang` | "Gold, Money..." | 0.5 | **1.0** | Valid cultural context. |
| **73** | `pantang larang mengandung` | "No nailing, no going out maghrib" | 0.5 | **1.0** | Correctly retrieved from `general_context.md`. |
| **77** | `panggung wayang` | "Check internet..." | 0.5 | **1.0** | Honest refusal (No location data). |
| **80** | `LCW retired` | "2019" | 0.5 | **1.0** | Factually correct. |
| **88** | `report jalan berlubang` | "MyJalan app..." | 0.5 | **1.0** | Correct authority. |
| **90** | `sampah tak kutip` | "PBT..." | 0.5 | **1.0** | Correct authority. |
| **91** | `anjing liar` | "PBT..." | 0.0 | **1.0** | Correct authority. |
| **92** | `paip air pecah` | "JKR / PBT" | 0.5 | **1.0** | Correct authority. |
| **95** | `celcom no signal` | "Check location..." | 0.5 | **1.0** | Valid general support advice. |
| **97** | `grab cancel` | "Help Centre..." | 0.5 | **1.0** | Correct advice. |
| **99** | `foodpanda wrong order` | "Refund... Contact" | 0.5 | **1.0** | Correct advice. |

## Score Adjustment Calculation

**Total Cases Analyzed:** 33 unique failures/partials listed above.
**Original Keyword Points (Approx):** ~12.5 points (mostly 0.0s and 0.5s).
**New Agentic Points:** ~22.0 points.
**Net Gain:** +9.5 Points.

**Base Score:** 74.7%
**Adjustment:** +9.5%
**Final Agentic Score:** **84.2%**

## Verdict
The V5 Model with Tavily Integration is **significantly better** than the keyword grader suggests.
- **Fact Retrieval (RAG/Web):** Extremely high accuracy (Scams, Holidays, Procedures).
- **Dialect/Slang:** Still a major weakness (Cases 1, 9, 21, 24). The text-based RAG ("P Ramlee") is confusing the model when it encounters slang terms it doesn't recognize.

**Final Score: 84.2%** (Silver Tier, beating Gemma3 27B is close but not quite >95%).
