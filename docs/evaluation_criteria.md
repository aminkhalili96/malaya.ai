# Evaluation Criteria: Malaya LLM Benchmark

**Goal**: Evaluate AI models "as a normal Malay user would," prioritizing intent understanding, cultural context, and factual accuracy over robotic keyword matching.

> **Method**: These criteria are encoded in `scripts/tier1_grader.py` using a Hybrid Logic (Rule-Based + Keyword Saturation).
> **Note**: For agent-based judging, Expected Keywords should be treated as the primary signal if reference answers are misaligned.

---

## 1. General Conversation (Shortforms, Manglish)
**Rule**: Does the model understand the intent of the slang/shortform?

*   **PASS (Score 1.0 - 0.8)**:
    *   Response addresses the core issue (e.g., "xleh" -> Model understands "refusal/cannot").
    *   Response contains **2+ relevant keywords** (e.g., Input: "lapar gila" -> Response: "makan" + "kedai").
    *   *Note*: We do not penalize if the model replies in full sentences instead of returning the slang.
*   **FAIL (Score 0.0)**:
    *   Response is completely off-topic.
    *   Response fails to identify the core intent (e.g., treats "xleh" as a typo/unknown).
    *   Response uses **Negative Keywords** (e.g., confusing "Siapa" with "Siapa nama kamu").

## 2. Factual Accuracy (Strict)
**Rule**: No compromise on facts.

*   **PASS (Score 1.0)**:
    *   Example: "Siapa PM?" -> Mentions "Anwar" or "Anwar Ibrahim".
*   **FAIL (Score 0.0)**:
    *   Mentions outdated leaders ("Ismail Sabri", "Muhyiddin", "Mahathir").
    *   Hallucinates a generic answer ("The PM is the head of government...").

## 3. Dialect Understanding (Kelantan, Sarawak, etc.)
**Rule**: Did the model understand the *meaning* of the dialect input?

*   **PASS (Score 1.0)**:
    *   Model replies in the correct dialect (Authentic).
    *   Model replies in **Standard Malay** but correctly addresses the question (e.g., Input: "Demo tokene?" -> Reply: "Saya tak makan lagi"). **(This was relaxed from strict dialect-only)**.
*   **FAIL (Score 0.0)**:
    *   Model claims it doesn't understand ("Maaf, saya tidak faham").
    *   Model misinterprets dialect words as English (e.g., "Demo" -> "Demonstration").

## 4. Translation & Nuance
**Rule**: Does the translation capture the *spirit*, not just literal words?

*   **PASS (Score 1.0)**:
    *   "I love you" in Kelantan -> "Kawe sayang demo" (Authentic).
    *   "Kawe sayang demo" -> "Kawe/Ambo" keywords present.
*   **PARTIAL (Score 0.5)**:
    *   Translates to Standard Malay ("Saya sayang awak") when Dialect was requested. (Technically correct meaning, but wrong style).

---

## Scoring Rubric (Encoded via Keyword Saturation)
To approximate human judgment with a script:

| Condition | Score | Reasoning |
| :--- | :--- | :--- |
| **Saturation** (2+ Hits) | **100%** | If model hits 2 distinct relevant concepts, it definitely understood the prompt. |
| **Single Hit** (1 Hit) | **80%** | Likely understood, but response was brief or less detailed. |
| **No Hits** | **0%** | Failed to address the topic. |
| **Negative Keyword** | **0%** | Actively misunderstood (e.g., "Java" for "Python" prompt). |

## Summary of Changes
*   **Old Way**: Required *Exact Match* of specific arbitrary keywords.
*   **New Way (Agent Proxy)**: 
    *   Checks **Understanding** (Topic Match).
    *   Checks **Context** (Dialect Match or Standard Replacement).
    *   Checks **Truth** (Hard Fact Check).
    *   Uses **Expected Keywords** as ground truth when reference answers are inconsistent.


---

## 5. Production Readiness Standards

What score is "Good Enough"?

| Tier | Score Range | Verdict | Description |
| :--- | :--- | :--- | :--- |
| **Platinum** | **> 85%** | **Enterprise Ready** | Capable of autonomous handling of slang, complex reasoning, and strict facts. Trustworthy. |
| **Gold** | **75% - 85%** | **Production Ready** | Reliable for most users. Rare failures usually involve very deep dialect or obscure facts. (e.g., Gemma3, GPT-OSS). |
| **Silver** | **65% - 75%** | **Beta / Pilot** | Good for "Copilots" where a human verifies. Great for general Malay but may miss nuance. (e.g., Qwen3, GRPO). |
| **Bronze** | **< 65%** | **Research Only** | Requires significant tuning. Not safe for unmonitored production use. |

### Why 75%?
A score of **75%** in this benchmark means the model:
1.  Never hallucinates the PM (Critical Trust).
2.  Understands >90% of common Shortforms (Usability).
3.  Respects Dialects >50% of the time (Cultural Fit).

Below 75%, users will frequently encounter "Robot Malay" or hallucinations, leading to churn.
