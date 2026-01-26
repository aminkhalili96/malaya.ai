# GPT-4o vs Qwen Model Comparison for Malay/Manglish Understanding

> **Date**: 2024-12-07  
> **Purpose**: Evaluate which LLM best understands Malaysian slang, shortforms, and cultural expressions  
> **Winner**: GPT-4o (4.79/5)

---

## Executive Summary

| Model | Score | Verdict |
|:------|:-----:|:--------|
| **GPT-4o** | **4.79/5** 🥇 | Best overall - understands slang AND responds coherently |
| **qwen3:14b** | **4.36/5** 🌟 | Best local model - very close to GPT-4o! |
| qwen2.5:14b | 3.71/5 | Good local option |
| Generic Qwen 2.5 7B | 3.07/5 | Uses Indonesian instead of Malaysian |
| Malaysian-Qwen 7B | 2.93/5 | Fine-tuned but worse - goes off-topic |
| Llama 3.2 3B | 2.71/5 | Too small for nuanced slang |
| QwQ:32b | N/A ❌ | Too slow (15min+ per response, impractical) |

**Key Findings**: 
1. **qwen3:14b is the best local model** - only 0.43 points behind GPT-4o!
2. Larger models (14B) significantly outperform 7B models
3. QwQ reasoning model is impractical for chat (constant timeouts)
4. Fine-tuning can degrade performance if not done carefully

---

## Test Methodology

### Scoring System (LLM-as-a-Judge)

GPT-4o evaluates each response using this rubric:

| Score | Meaning | Criteria |
|:-----:|:--------|:---------|
| **5** | Excellent | Fully understood all slang, particles, and cultural context |
| **4** | Good | Understood most slang and context, minor misses |
| **3** | Moderate | Got some slang but missed key terms |
| **2** | Poor | Partially understood, missed most slang meanings |
| **1** | Failed | Completely misunderstood, no comprehension |

### Evaluation Prompt Template

```
You are evaluating how well an AI model understood a Malaysian Malay/Manglish query.

Original Query: {query}
Expected Understanding: {expected}
Model's Response: {response}

Evaluation Criteria:
{specific_criteria}

Score the response from 1-5 and provide reasoning.
```

---

## Category Breakdown

### Scores by Category

| Category | GPT-4o | Generic Qwen | Malaysian-Qwen |
|:---------|:------:|:------------:|:--------------:|
| Shortforms | 5.0 | 3.0 | 2.0 |
| Particles | 4.33 | 1.67 | 2.0 |
| Cultural | 5.0 | 3.67 | 3.67 |
| Manglish | 4.67 | 3.33 | 3.0 |
| Sentiment | 5.0 | 4.0 | 4.5 |

---

## Complete Test Results

### Test 1: slang_01 (Shortforms)

**Query**: `xleh la bro, aku xde duit skrg. nnt la kita jmpa`

**Expected Understanding**: Cannot bro, I don't have money now. We'll meet later.

**Evaluation Criteria**:
- Understands 'xleh' = tak boleh (cannot)
- Understands 'xde' = tiada (don't have)
- Understands 'skrg' = sekarang (now)
- Understands 'nnt' = nanti (later)
- Understands 'jmpa' = jumpa (meet)

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Okay, aku faham yang kau takde duit sekarang, so tak boleh jumpa lagi. Takpe, kita boleh plan lain kali bila kau dah ready." | **5/5** |
| Generic Qwen | "Bro, aku faham, **enggak** ada duit sekarang je. Tapi okay, nanti kita jumpa!" | 4/5 |
| Malaysian-Qwen | "Oi, takpe lah! Jom kite pegi kat kedai makan tu dulu. Aku dah simpan sikit untuk kite berborak..." | **1/5** ❌ |

**Analysis**: Malaysian-Qwen completely ignored that the user said they have no money and invited them to eat instead.

---

### Test 2: slang_02 (Shortforms)

**Query**: `mcm mane nk buat ni? aku dh try byk kali tp xjd`

**Expected Understanding**: How to do this? I've tried many times but it didn't work.

**Evaluation Criteria**:
- Understands 'mcm mane' = macam mana (how)
- Understands 'nk' = nak (want to)
- Understands 'dh' = dah/sudah (already)
- Understands 'tp' = tapi (but)
- Understands 'xjd' = tak jadi (didn't work)

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Okay, aku faham yang kau dah cuba banyak kali tapi masih tak jadi. Boleh tak kau bagi tau sikit apa yang kau cuba buat tu?" | **5/5** |
| Generic Qwen | "Hehe, entahlah nak. Cikgu ada tips kecapi pula tak? Saya juga cuba-cuba tapi gak jumpa hasil." | 3/5 |
| Malaysian-Qwen | [Long PHP code tutorial about database updates - completely off-topic] | 2/5 |

---

### Test 3: slang_03 (Shortforms)

**Query**: `ko dtg x ptg ni? ktorg tunggu kt mamak`

**Expected Understanding**: Are you coming this evening? We're waiting at the mamak stall.

**Evaluation Criteria**:
- Understands 'ko' = kau (you)
- Understands 'dtg' = datang (come)
- Understands 'x' = tak (not) - question marker
- Understands 'ptg' = petang (evening)
- Understands 'ktorg' = kitorang (we/us)
- Understands 'mamak' = Indian-Muslim restaurant

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Saya faham yang awak tanya sama ada saya akan datang petang ni sebab korang tengah tunggu kat mamak. Sorry, saya tak boleh datang, tapi enjoy lepak kat mamak!" | **5/5** |
| Generic Qwen | "Hi there! Saya faham bahawa kamu datang ke Mamak tetapi tidak ada pertemuan dengan org lain, ya?" | 2/5 |
| Malaysian-Qwen | "Oi bro! Aku tak tau ape yg hang cakap tadi tu, tapi aku nak terangkan sikit la..." | 3/5 |

---

### Test 4: particle_01 (Particles)

**Query**: `best gila siot benda ni!`

**Expected Understanding**: This thing is extremely awesome!

**Evaluation Criteria**:
- Understands 'best gila' = extremely good/awesome
- Understands 'siot' = emphasis particle (like 'damn' but casual)
- Recognizes overall positive excitement

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Nampaknya awak betul-betul teruja dengan benda tu! Apa yang best sangat pasal benda tu? Cerita sikit." | **5/5** |
| Generic Qwen | "Hehe, takut-takutlah nih! Tiap-tiap orang mempunyai pilihan makanan favoritnya sendiri." | **1/5** ❌ |
| Malaysian-Qwen | "Eh, hang tau tak? Masa aku tengah makan nasi lemak tu, tiba-tiba aku kena pening kepala la." | **1/5** ❌ |

**Analysis**: Both Qwen models completely failed this test. Generic Qwen talked about food preferences, Malaysian-Qwen talked about getting dizzy while eating nasi lemak.

---

### Test 5: particle_02 (Particles)

**Query**: `apahal la kau ni? pelik je`

**Expected Understanding**: What's wrong with you? You're being weird.

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Saya faham, awak rasa saya ni pelik sikit. Mungkin ada yang saya buat tak kena ke?" | 4/5 |
| Generic Qwen | "Oh hehe, kau buat apa ne? Sama2 lah, kita cek cerita apa yang nak share..." | 2/5 |
| Malaysian-Qwen | "Eh! Aku takde apa-apa pun, okay? Mana ada nak buat perangai pelik-pelik macam tu." | **4/5** |

**Analysis**: Malaysian-Qwen did well on this test - correctly understood the accusation of being weird.

---

### Test 6: particle_03 (Particles)

**Query**: `takkan la dia buat mcm tu kot`

**Expected Understanding**: It can't be that he did it like that, surely.

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Awak rasa macam tak percaya yang dia buat macam tu, kan? Memang kadang-kadang susah nak terima..." | 4/5 |
| Generic Qwen | "Ah, kau bermaksud bilang dia tak akanbuat seperti itu, ya? Jangan stress..." | 2/5 |
| Malaysian-Qwen | [Long unrelated advice about socializing and making friends] | **1/5** ❌ |

---

### Test 7: culture_01 (Cultural)

**Query**: `lepak mamak jom, aku belanja teh tarik`

**Expected Understanding**: Let's hang out at the mamak stall, I'll treat you to teh tarik.

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Oh, nak lepak mamak eh? Best jugak tu! Teh tarik on you, nice lah. Bila nak pergi?" | **5/5** |
| Generic Qwen | "Wah, lepak! Saya tahu tehatar enak di sana. Kamu nak saya bantu macam mana?" | 3/5 |
| Malaysian-Qwen | "Oi! Mampus la korang ni. Nak kene lepak kat Mamak jom? Aku pun nak belanja teh tarik sekali." | 4/5 |

---

### Test 8: culture_02 (Cultural)

**Query**: `abang, nak tapau nasi lemak satu`

**Expected Understanding**: Brother, I want to takeaway one nasi lemak.

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Okay, you want to tapau one nasi lemak. Nak sambal lebih ke, atau ada request lain?" | **5/5** |
| Generic Qwen | "Ya, abang! Saya tahu apa yang anda maksud... [suggested restaurant locations]" | 4/5 |
| Malaysian-Qwen | "Aiyah! Tak pe lah, aku boleh tolong abang. Nak apa lagi? Nasi lemak ke, atau makanan lain?" | 3/5 |

---

### Test 9: culture_03 (Cultural)

**Query**: `jangan kacau aku, aku tengah mengantuk gila lepas sahur`

**Expected Understanding**: Don't disturb me, I'm extremely sleepy after sahur.

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Faham, lepas sahur memang rasa mengantuk tu biasa. Kalau boleh, cuba rehat sekejap..." | **5/5** |
| Generic Qwen | "Hehe, faham tu. Kita nak beri istirahat kat badan ni selepas sahur." | 4/5 |
| Malaysian-Qwen | "Eh, sorry la bro. Aku ni tak sengaja nak ganggu ko pun... boleh la makan pisang dan kopi." | 4/5 |

---

### Test 10: manglish_01 (Manglish)

**Query**: `eh bro, that meeting just now how ah? client happy tak?`

**Expected Understanding**: Hey bro, how was that meeting? Was the client happy?

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Oh, you nak tahu pasal meeting tadi. Client nampak happy je, dia puas hati dengan presentation kita." | **5/5** |
| Generic Qwen | "Eh bro, that meeting kena lah! Rasa macam tu, klient senang tak?" | 3/5 |
| Malaysian-Qwen | "Eh, sihat la tu! Tapi aku nak tau apa jadi masa meeting tadi..." | 2/5 |

---

### Test 11: manglish_02 (Manglish)

**Query**: `wah macam best je! can recommend tempat makan nearby tak?`

**Expected Understanding**: Wow, looks nice! Can you recommend a place to eat nearby?

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Oh, you're looking for a good place to eat nearby! Boleh, of course. Kalau you suka makanan Melayu, boleh try Restoran Rebung..." | **5/5** |
| Generic Qwen | "Ah, best already! Macam la, tu. Ada papa ni tempat makan dekat sana yang boleh saya rekomende?" | 3/5 |
| Malaysian-Qwen | "Eh, aku boleh rekod ni la! Ada banyak tempat makan kat sini yang oghang suka..." | 3/5 |

---

### Test 12: manglish_03 (Manglish)

**Query**: `sorry la bro, i terlupa pasal our appointment. my bad gila`

**Expected Understanding**: Sorry bro, I forgot about our appointment. Totally my bad.

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "No worries, bro! I faham, benda boleh jadi. Bila nak reschedule our appointment?" | 4/5 |
| Generic Qwen | "Tak apa-apa bro, faham pun saya. Terus kan kita cari tarikh baru yang betul saih?" | **4/5** |
| Malaysian-Qwen | "Tak pe lah, saya paham situasi ni. Dah leh? Jangan kan nak sibuk sangat pun." | **4/5** |

---

### Test 13: sentiment_01 (Sentiment)

**Query**: `bodoh punya system, hangat dah aku`

**Expected Understanding**: Stupid system, I'm already pissed off/angry.

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Nampaknya awak tengah marah dengan sistem ni. Ada apa yang boleh saya bantu untuk selesaikan masalah awak?" | **5/5** |
| Generic Qwen | "Ah, kau marah kerana sistem itu kan? Kalau begitu, coba ceritak lagi tu. Saya boleh cuba bantu." | 4/5 |
| Malaysian-Qwen | "Eh bro! Nampak macam hang habis terlepoih kot? Sistem tu memang lah tak best sikit, tapi jangan nak marah sangat la." | 4/5 |

---

### Test 14: sentiment_02 (Sentiment)

**Query**: `geram betul la dengan service ni, lambat macam siput`

**Expected Understanding**: I'm really frustrated with this service, it's slow like a snail.

| Model | Response | Score |
|:------|:---------|:-----:|
| **GPT-4o** | "Nampaknya awak memang tak puas hati dengan servis yang lambat tu, kan? Memang frust bila kena tunggu lama." | **5/5** |
| Generic Qwen | "Geram betul je la, service itu memang lambat macam siput. Kalau ada apa-apa masalah, kita boleh cari solusinya bersama." | 4/5 |
| Malaysian-Qwen | "Wah, korang dah mengadui pasal perkhidmatan tu ke? Memang la tak best kalau dia slow macam siput tu kan." | **5/5** |

---

## Why Malaysian-Qwen Underperformed

### 1. Catastrophic Forgetting

Fine-tuning on 1.5B Malaysian tokens caused the model to lose instruction-following ability:

| Capability | Before Fine-tuning | After Fine-tuning |
|:-----------|:-------------------|:------------------|
| Following instructions | ✅ Good | ❌ Degraded |
| Staying on topic | ✅ Good | ❌ Goes off-topic |
| Coherent responses | ✅ Good | ⚠️ Sometimes rambles |
| Malaysian dialect | ⚠️ Limited | ✅ Good |

### 2. Training Data Quality Issues

The model's responses suggest training data included:
- Casual conversations that go off-topic
- Long-form explanations (e.g., coding tutorials)
- "Chatty" patterns that don't match Q&A format

### 3. Example of the Problem

**Query**: "best gila siot benda ni!" (This thing is awesome!)

**Malaysian-Qwen's Response**: "Eh, hang tau tak? Masa aku tengah makan nasi lemak tu, tiba-tiba aku kena pening kepala la. Macam mana nak sambung lagi kalau dah macam tu?"

This response:
- Uses correct Malaysian dialect ✅
- Completely ignores the query ❌
- Talks about getting dizzy while eating ❌

---

## Conclusion

### Final Rankings

| Rank | Model | Score | Best For |
|:----:|:------|:-----:|:---------|
| 🥇 | **GPT-4o** | 4.79/5 | Production use - best accuracy + coherence |
| 🥈 | **qwen3:14b** | 4.36/5 | **Best local model** - excellent for data sovereignty |
| 🥉 | qwen2.5:14b | 3.71/5 | Good local alternative |
| 4 | Generic Qwen 2.5 7B | 3.07/5 | Budget local option |
| 5 | Malaysian-Qwen 7B | 2.93/5 | Not recommended |
| 6 | Llama 3.2 3B | 2.71/5 | Too small for this task |
| ❌ | QwQ:32b | N/A | Impractical (all tests timeout) |

### Key Insights

| Finding | Implication |
|:--------|:------------|
| **qwen3:14b is only 0.43 behind GPT-4o** | Viable for data-sovereign production use |
| **14B models >> 7B models** | +0.6-1.3 score improvement with 2x params |
| **QwQ reasoning model fails** | Don't use reasoning models for chat |
| **Fine-tuning can hurt** | Malaysian-Qwen < Generic Qwen |

### Recommendations

1. **Production (best quality)**: Use GPT-4o
2. **Data sovereignty**: Use **qwen3:14b** locally via Ollama
3. **Cost-sensitive**: qwen2.5:14b is a good fallback
4. **Avoid**: QwQ (too slow), Malaysian-Qwen (quality issues)

---

## DSPy & Few-Shot Prompt Experiments

> **Date**: 2024-12-08  
> **Goal**: Test if DSPy prompt optimization or few-shot examples improve Malay understanding

### DSPy Experiment Results

We tested DSPy (with slang dictionary prompt) vs simple prompt:

| Model | Without DSPy | With DSPy | Change |
|:------|:------------:|:---------:|:------:|
| GPT-4o | **8.3/10** | 6.8/10 | -1.5 ⚠️ |
| qwen3:14b | 7.2/10 | **7.8/10** | **+0.7 ✅** |
| qwen2.5:14b | **8.3/10** | 7.2/10 | -1.2 ⚠️ |
| llama3.2:3b | 3.7/10 | 2.2/10 | -1.5 ⚠️ |

**Key Finding**: DSPy only helps qwen3:14b. Other models perform worse with longer prompts.

---

### Few-Shot Prompt Experiment Results

Added Malay vs Indonesian few-shot examples:

| Model | Simple Prompt | With Few-Shot | Change |
|:------|:-------------:|:-------------:|:------:|
| GPT-4o | **8.3/10** | 7.7/10 | -0.6 ⚠️ |
| qwen3:14b | 7.2/10 | 7.2/10 | 0 |
| qwen2.5:14b | **8.3/10** | 6.8/10 | -1.5 ⚠️ |
| llama3.2:3b | 3.7/10 | 4.0/10 | +0.3 ✅ |

**Key Finding**: Few-shot examples only help weak models (llama3.2). Strong models already know Malay.

---

### Why Advanced Prompts Hurt Strong Models

| Phenomenon | Explanation |
|:-----------|:------------|
| GPT-4o drops with DSPy | Already knows Malay slang; extra rules cause confusion |
| qwen3 improves with DSPy | Has gaps in Malay training; benefits from explicit rules |
| llama3.2 improves with few-shot | Too small; needs explicit examples |

---

### Final Prompt Recommendation

| Model | Best Approach | Score |
|:------|:--------------|:-----:|
| **GPT-4o** | Simple prompt (no DSPy, no few-shot) | **8.3/10** |
| **qwen3:14b** | With DSPy | 7.8/10 |
| qwen2.5:14b | Simple prompt | 8.3/10 |
| llama3.2:3b | With few-shot | 4.0/10 |

---

## Appendix: Test Script

The comparison test script is located at: `tests/model_comparison.py`

Run with:
```bash
python tests/model_comparison.py --qwen-model <model_name> --output results.json
```

