"""
Model Comparison: GPT-4o vs Qwen for Malay/Manglish
====================================================
Evaluates which model better understands Malaysian slang, shortforms, and cultural expressions.

Usage:
    # Compare with GPT-4o (default) vs Qwen via Ollama
    python tests/model_comparison.py
    
    # Compare with specific Qwen model
    python tests/model_comparison.py --qwen-model qwen2.5:7b

Prerequisites:
    1. OPENAI_API_KEY set in .env
    2. Ollama installed and running: `ollama serve`
    3. Qwen model pulled: `ollama pull qwen2.5:7b`
"""

import os
import json
import time
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# TEST CASES: Malay Slang & Cultural Understanding
# ============================================================

@dataclass
class TestCase:
    """A single test case for model comparison."""
    id: str
    category: str
    input_query: str
    expected_understanding: str  # What the model should understand
    evaluation_criteria: List[str]  # Criteria to judge response

TEST_CASES: List[TestCase] = [
    # ============================================================
    # Category 1: Shortforms (10 tests)
    # ============================================================
    TestCase(
        id="shortform_01",
        category="Shortforms",
        input_query="xleh la bro, aku xde duit skrg. nnt la kita jmpa",
        expected_understanding="Cannot bro, I don't have money now. We'll meet later.",
        evaluation_criteria=[
            "Understands 'xleh' = tak boleh (cannot)",
            "Understands 'xde' = tiada (don't have)",
            "Understands 'skrg' = sekarang (now)",
            "Understands 'nnt' = nanti (later)",
            "Understands 'jmpa' = jumpa (meet)"
        ]
    ),
    TestCase(
        id="shortform_02",
        category="Shortforms",
        input_query="mcm mane nk buat ni? aku dh try byk kali tp xjd",
        expected_understanding="How to do this? I've tried many times but it didn't work.",
        evaluation_criteria=[
            "Understands 'mcm mane' = macam mana (how)",
            "Understands 'nk' = nak (want to)",
            "Understands 'dh' = dah/sudah (already)",
            "Understands 'tp' = tapi (but)",
            "Understands 'xjd' = tak jadi (didn't work)"
        ]
    ),
    TestCase(
        id="shortform_03",
        category="Shortforms",
        input_query="ko dtg x ptg ni? ktorg tunggu kt mamak",
        expected_understanding="Are you coming this evening? We're waiting at the mamak stall.",
        evaluation_criteria=[
            "Understands 'ko' = kau (you)",
            "Understands 'dtg' = datang (come)",
            "Understands 'x' = tak (not) - question marker",
            "Understands 'ptg' = petang (evening)",
            "Understands 'ktorg' = kitorang (we/us)"
        ]
    ),
    TestCase(
        id="shortform_04",
        category="Shortforms",
        input_query="xtau la bro, aku xphm lgsg apa yg dia ckp",
        expected_understanding="I don't know bro, I don't understand at all what he said.",
        evaluation_criteria=[
            "Understands 'xtau' = tak tahu (don't know)",
            "Understands 'xphm' = tak faham (don't understand)",
            "Understands 'lgsg' = langsung (at all)",
            "Understands 'yg' = yang (that/which)",
            "Understands 'ckp' = cakap (said/talk)"
        ]
    ),
    TestCase(
        id="shortform_05",
        category="Shortforms",
        input_query="sbb tu la aku xnk pgi, mls sgt dh",
        expected_understanding="That's why I don't want to go, too lazy already.",
        evaluation_criteria=[
            "Understands 'sbb' = sebab (because)",
            "Understands 'xnk' = tak nak (don't want)",
            "Understands 'pgi' = pergi (go)",
            "Understands 'mls' = malas (lazy)"
        ]
    ),
    TestCase(
        id="shortform_06",
        category="Shortforms",
        input_query="tgk la dulu, nnt klu ok baru bgtau",
        expected_understanding="Check first, if okay then tell me later.",
        evaluation_criteria=[
            "Understands 'tgk' = tengok (look/check)",
            "Understands 'klu' = kalau (if)",
            "Understands 'bgtau' = beritahu (tell)"
        ]
    ),
    TestCase(
        id="shortform_07",
        category="Shortforms",
        input_query="blh tlg aku x? aku tgh sibuk sgt ni",
        expected_understanding="Can you help me? I'm very busy right now.",
        evaluation_criteria=[
            "Understands 'blh' = boleh (can)",
            "Understands 'tlg' = tolong (help)",
            "Understands 'tgh' = tengah (currently)"
        ]
    ),
    TestCase(
        id="shortform_08",
        category="Shortforms",
        input_query="jgn lupa bwk brg tu, pntg sgt",
        expected_understanding="Don't forget to bring that thing, very important.",
        evaluation_criteria=[
            "Understands 'jgn' = jangan (don't)",
            "Understands 'bwk' = bawa (bring)",
            "Understands 'brg' = barang (thing/item)",
            "Understands 'pntg' = penting (important)"
        ]
    ),
    TestCase(
        id="shortform_09",
        category="Shortforms",
        input_query="smpi ke? lmbt sgt la ko ni",
        expected_understanding="Have you arrived? You're so late.",
        evaluation_criteria=[
            "Understands 'smpi' = sampai (arrive)",
            "Understands 'lmbt' = lambat (late)"
        ]
    ),
    TestCase(
        id="shortform_10",
        category="Shortforms",
        input_query="sy xfhm knp dia mrah sgt dgn sy",
        expected_understanding="I don't understand why he's so angry with me.",
        evaluation_criteria=[
            "Understands 'sy' = saya (I)",
            "Understands 'xfhm' = tak faham (don't understand)",
            "Understands 'knp' = kenapa (why)",
            "Understands 'mrah' = marah (angry)",
            "Understands 'dgn' = dengan (with)"
        ]
    ),
    
    # ============================================================
    # Category 2: Particles & Emphasis (8 tests)
    # ============================================================
    TestCase(
        id="particle_01",
        category="Particles",
        input_query="best gila siot benda ni!",
        expected_understanding="This thing is extremely awesome!",
        evaluation_criteria=[
            "Understands 'best gila' = extremely good/awesome",
            "Understands 'siot' = emphasis particle (like 'damn' but casual)",
            "Recognizes overall positive excitement"
        ]
    ),
    TestCase(
        id="particle_02",
        category="Particles",
        input_query="apahal la kau ni? pelik je",
        expected_understanding="What's wrong with you? You're being weird.",
        evaluation_criteria=[
            "Understands 'apahal' = what's wrong/what's the matter",
            "Understands 'la' = emphasis particle",
            "Understands 'pelik je' = just weird/strange"
        ]
    ),
    TestCase(
        id="particle_03",
        category="Particles",
        input_query="takkan la dia buat mcm tu kot",
        expected_understanding="It can't be that he did it like that, surely.",
        evaluation_criteria=[
            "Understands 'takkan' = impossible/can't be",
            "Understands 'la' = emphasis",
            "Understands 'kot' = hedging particle (maybe/surely)"
        ]
    ),
    TestCase(
        id="particle_04",
        category="Particles",
        input_query="dah la tu, jangan nak drama lagi meh",
        expected_understanding="Enough already, stop being dramatic.",
        evaluation_criteria=[
            "Understands 'dah la tu' = enough already",
            "Understands 'meh' = dismissive particle"
        ]
    ),
    TestCase(
        id="particle_05",
        category="Particles",
        input_query="confirm ke ni? sure ke bro?",
        expected_understanding="Is this confirmed? Are you sure bro?",
        evaluation_criteria=[
            "Understands 'confirm' used as Manglish",
            "Understands 'ke' = question particle"
        ]
    ),
    TestCase(
        id="particle_06",
        category="Particles",
        input_query="teruk gila wei performance dia malam ni",
        expected_understanding="His performance tonight was terrible.",
        evaluation_criteria=[
            "Understands 'teruk gila' = terribly bad",
            "Understands 'wei' = attention particle"
        ]
    ),
    TestCase(
        id="particle_07",
        category="Particles",
        input_query="ish, malas nya nak buat benda ni kan",
        expected_understanding="Ugh, don't feel like doing this, right?",
        evaluation_criteria=[
            "Understands 'ish' = expression of annoyance",
            "Understands 'malas nya' = how lazy/reluctant",
            "Understands 'kan' = tag question particle"
        ]
    ),
    TestCase(
        id="particle_08",
        category="Particles",
        input_query="weh, legit ke info ni? jangan tipu la",
        expected_understanding="Hey, is this info legit? Don't lie.",
        evaluation_criteria=[
            "Understands 'weh' = hey (attention getter)",
            "Understands 'legit' = Manglish slang for legitimate"
        ]
    ),
    
    # ============================================================
    # Category 3: Cultural References (10 tests)
    # ============================================================
    TestCase(
        id="culture_01",
        category="Cultural",
        input_query="lepak mamak jom, aku belanja teh tarik",
        expected_understanding="Let's hang out at the mamak stall, I'll treat you to teh tarik.",
        evaluation_criteria=[
            "Understands 'lepak' = hang out/chill",
            "Understands 'mamak' = Indian-Muslim restaurant",
            "Understands 'jom' = let's go",
            "Understands 'belanja' = treat (pay for someone)",
            "Knows 'teh tarik' = Malaysian pulled milk tea"
        ]
    ),
    TestCase(
        id="culture_02",
        category="Cultural",
        input_query="abang, nak tapau nasi lemak satu",
        expected_understanding="Brother, I want to takeaway one nasi lemak.",
        evaluation_criteria=[
            "Understands 'abang' = polite address to male vendor",
            "Understands 'tapau' = takeaway (from Cantonese)",
            "Knows 'nasi lemak' = Malaysian coconut rice dish"
        ]
    ),
    TestCase(
        id="culture_03",
        category="Cultural",
        input_query="jangan kacau aku, aku tengah mengantuk gila lepas sahur",
        expected_understanding="Don't disturb me, I'm extremely sleepy after sahur.",
        evaluation_criteria=[
            "Understands 'kacau' = disturb",
            "Understands 'mengantuk gila' = extremely sleepy",
            "Knows 'sahur' = pre-dawn meal during Ramadan"
        ]
    ),
    TestCase(
        id="culture_04",
        category="Cultural",
        input_query="balik kampung raya ni x? rindu mak ayah",
        expected_understanding="Going back to hometown this Eid? Miss mom and dad.",
        evaluation_criteria=[
            "Knows 'balik kampung' = return to hometown",
            "Knows 'raya' = Eid celebration",
            "Understands family context"
        ]
    ),
    TestCase(
        id="culture_05",
        category="Cultural",
        input_query="nak pergi kenduri kawin jiran petang ni",
        expected_understanding="Going to neighbor's wedding feast this evening.",
        evaluation_criteria=[
            "Knows 'kenduri' = feast/celebration",
            "Knows 'kenduri kawin' = wedding feast",
            "Understands 'jiran' = neighbor"
        ]
    ),
    TestCase(
        id="culture_06",
        category="Cultural",
        input_query="makcik, roti canai kosong dua dengan teh o",
        expected_understanding="Auntie, two plain roti canai with black tea.",
        evaluation_criteria=[
            "Understands 'makcik' = auntie (polite address)",
            "Knows 'roti canai kosong' = plain flatbread",
            "Knows 'teh o' = black tea without milk"
        ]
    ),
    TestCase(
        id="culture_07",
        category="Cultural",
        input_query="dah solat maghrib ke belum?",
        expected_understanding="Have you prayed Maghrib yet or not?",
        evaluation_criteria=[
            "Knows 'solat' = prayer",
            "Knows 'maghrib' = evening prayer time",
            "Understands religious context"
        ]
    ),
    TestCase(
        id="culture_08",
        category="Cultural",
        input_query="jaga adik kejap, aku nak pegi pasar malam",
        expected_understanding="Watch your sibling for a bit, I'm going to the night market.",
        evaluation_criteria=[
            "Understands 'jaga adik' = watch younger sibling",
            "Knows 'pasar malam' = night market"
        ]
    ),
    TestCase(
        id="culture_09",
        category="Cultural",
        input_query="bila nak bagi angpow ni? CNY dah dekat",
        expected_understanding="When will you give red packets? Chinese New Year is near.",
        evaluation_criteria=[
            "Knows 'angpow' = red envelope/packet (CNY tradition)",
            "Knows 'CNY' = Chinese New Year"
        ]
    ),
    TestCase(
        id="culture_10",
        category="Cultural",
        input_query="tolong beli kuih raya kat kedai tu",
        expected_understanding="Please buy festive cookies at that shop.",
        evaluation_criteria=[
            "Knows 'kuih raya' = festive cookies/snacks for Eid"
        ]
    ),
    
    # ============================================================
    # Category 4: Manglish Code-Switching (10 tests)
    # ============================================================
    TestCase(
        id="manglish_01",
        category="Manglish",
        input_query="eh bro, that meeting just now how ah? client happy tak?",
        expected_understanding="Hey bro, how was that meeting? Was the client happy?",
        evaluation_criteria=[
            "Handles English-Malay code-switching naturally",
            "Understands 'how ah' = question marker",
            "Understands 'tak' at end = question (yes/no)"
        ]
    ),
    TestCase(
        id="manglish_02",
        category="Manglish",
        input_query="wah macam best je! can recommend tempat makan nearby tak?",
        expected_understanding="Wow, looks nice! Can you recommend a place to eat nearby?",
        evaluation_criteria=[
            "Handles seamless code-switching",
            "Understands 'macam best' = looks nice/seems good",
            "Understands 'tempat makan' = place to eat"
        ]
    ),
    TestCase(
        id="manglish_03",
        category="Manglish",
        input_query="sorry la bro, i terlupa pasal our appointment. my bad gila",
        expected_understanding="Sorry bro, I forgot about our appointment. Totally my bad.",
        evaluation_criteria=[
            "Understands 'terlupa' = forgot",
            "Understands 'pasal' = about/regarding",
            "Understands 'gila' as intensifier = very/totally"
        ]
    ),
    TestCase(
        id="manglish_04",
        category="Manglish",
        input_query="actually kan, i rasa macam something wrong je",
        expected_understanding="Actually, I feel like something is wrong.",
        evaluation_criteria=[
            "Handles 'actually kan' = conversational opener",
            "Understands 'rasa macam' = feel like"
        ]
    ),
    TestCase(
        id="manglish_05",
        category="Manglish",
        input_query="this one confirm boleh punya, trust me bro",
        expected_understanding="This one definitely can work, trust me bro.",
        evaluation_criteria=[
            "Understands 'confirm boleh punya' = definitely can",
            "Handles mixed English-Malay reassurance"
        ]
    ),
    TestCase(
        id="manglish_06",
        category="Manglish",
        input_query="later we discuss ok? now i busy sikit",
        expected_understanding="We'll discuss later ok? I'm a bit busy now.",
        evaluation_criteria=[
            "Understands 'busy sikit' = a bit busy",
            "Handles temporal code-switching"
        ]
    ),
    TestCase(
        id="manglish_07",
        category="Manglish",
        input_query="the problem is dia tak nak dengar langsung",
        expected_understanding="The problem is he doesn't want to listen at all.",
        evaluation_criteria=[
            "Handles mid-sentence code-switch",
            "Understands 'tak nak dengar' = doesn't want to listen"
        ]
    ),
    TestCase(
        id="manglish_08",
        category="Manglish",
        input_query="why la you always macam ni? annoying tau",
        expected_understanding="Why are you always like this? It's annoying you know.",
        evaluation_criteria=[
            "Understands frustration tone",
            "Understands 'macam ni' = like this",
            "Understands 'tau' = you know"
        ]
    ),
    TestCase(
        id="manglish_09",
        category="Manglish",
        input_query="i think kita should try different approach la",
        expected_understanding="I think we should try a different approach.",
        evaluation_criteria=[
            "Understands 'kita' = we",
            "Handles suggestion with code-switch"
        ]
    ),
    TestCase(
        id="manglish_10",
        category="Manglish",
        input_query="so basically dia expect kita settle by friday",
        expected_understanding="Basically he expects us to settle it by Friday.",
        evaluation_criteria=[
            "Understands professional Manglish context",
            "Handles workplace code-switching"
        ]
    ),
    
    # ============================================================
    # Category 5: Sentiment & Tone (8 tests)
    # ============================================================
    TestCase(
        id="sentiment_01",
        category="Sentiment",
        input_query="bodoh punya system, hangat dah aku",
        expected_understanding="Stupid system, I'm already pissed off.",
        evaluation_criteria=[
            "Detects negative sentiment (frustration)",
            "Understands 'hangat' = angry/heated",
            "Appropriate empathetic response"
        ]
    ),
    TestCase(
        id="sentiment_02",
        category="Sentiment",
        input_query="geram betul la dengan service ni, lambat macam siput",
        expected_understanding="Really frustrated with this service, slow like a snail.",
        evaluation_criteria=[
            "Detects frustration",
            "Understands 'geram' = frustrated",
            "Understands 'macam siput' = like a snail"
        ]
    ),
    TestCase(
        id="sentiment_03",
        category="Sentiment",
        input_query="terharu gila aku tengok video tu, sampai nangis",
        expected_understanding="I was so touched watching that video, even cried.",
        evaluation_criteria=[
            "Detects emotional/positive sentiment",
            "Understands 'terharu' = touched/moved"
        ]
    ),
    TestCase(
        id="sentiment_04",
        category="Sentiment",
        input_query="teruja nya! xleh tido malam ni",
        expected_understanding="So excited! Can't sleep tonight.",
        evaluation_criteria=[
            "Detects excitement",
            "Understands 'teruja' = excited"
        ]
    ),
    TestCase(
        id="sentiment_05",
        category="Sentiment",
        input_query="sedih gila bro, dia dah tak nak kawan",
        expected_understanding="So sad bro, they don't want to be friends anymore.",
        evaluation_criteria=[
            "Detects sadness",
            "Appropriate empathetic response"
        ]
    ),
    TestCase(
        id="sentiment_06",
        category="Sentiment",
        input_query="syok nya dapat cuti panjang!",
        expected_understanding="So nice to get a long holiday!",
        evaluation_criteria=[
            "Detects positive sentiment",
            "Understands 'syok' = enjoyable/nice"
        ]
    ),
    TestCase(
        id="sentiment_07",
        category="Sentiment",
        input_query="kecewa sangat dengan result ni",
        expected_understanding="Very disappointed with this result.",
        evaluation_criteria=[
            "Detects disappointment",
            "Understands 'kecewa' = disappointed"
        ]
    ),
    TestCase(
        id="sentiment_08",
        category="Sentiment",
        input_query="bangga sgt dgn anak, dapat dean's list",
        expected_understanding="So proud of my child, got dean's list.",
        evaluation_criteria=[
            "Detects pride/positive sentiment",
            "Understands 'bangga' = proud"
        ]
    ),
    
    # ============================================================
    # Category 6: Sarcasm & Irony (4 tests) - HARDEST
    # ============================================================
    TestCase(
        id="sarcasm_01",
        category="Sarcasm",
        input_query="pandai nya kau, boleh la jadi menteri",
        expected_understanding="(Sarcastic) Oh you're so smart, you could be a minister.",
        evaluation_criteria=[
            "Detects sarcasm - not genuine praise",
            "Understands the mocking tone",
            "Responds appropriately to sarcasm"
        ]
    ),
    TestCase(
        id="sarcasm_02",
        category="Sarcasm",
        input_query="bagus la tu, teruskan perangai macam tu",
        expected_understanding="(Ironic) Great, keep acting like that.",
        evaluation_criteria=[
            "Detects irony - not genuine approval",
            "Understands disapproval masked as praise"
        ]
    ),
    TestCase(
        id="sarcasm_03",
        category="Sarcasm",
        input_query="wah rajin nya, baru bangun pukul 2 petang",
        expected_understanding="(Sarcastic) So hardworking, just woke up at 2pm.",
        evaluation_criteria=[
            "Detects sarcasm about laziness",
            "Understands contradiction between 'rajin' and waking late"
        ]
    ),
    TestCase(
        id="sarcasm_04",
        category="Sarcasm",
        input_query="hebat sangat la kau ni, semua orang salah",
        expected_understanding="(Ironic) You're so great, everyone else is wrong.",
        evaluation_criteria=[
            "Detects mocking/dismissive tone",
            "Understands criticism of arrogance"
        ]
    ),
]


# ============================================================
# MODEL CLIENTS
# ============================================================

def call_gpt4o(query: str, system_prompt: str = "") -> Dict:
    """Call GPT-4o via OpenAI API."""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=query))
    
    start = time.time()
    response = llm.invoke(messages)
    latency = time.time() - start
    
    return {
        "model": "gpt-4o",
        "response": response.content,
        "latency_ms": round(latency * 1000, 2)
    }


def call_qwen_ollama(query: str, model: str = "qwen2.5:7b", system_prompt: str = "") -> Dict:
    """Call Qwen via Ollama local API."""
    import requests
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt} if system_prompt else None,
            {"role": "user", "content": query}
        ],
        "stream": False
    }
    payload["messages"] = [m for m in payload["messages"] if m]
    
    start = time.time()
    try:
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        latency = time.time() - start
        
        return {
            "model": model,
            "response": data.get("message", {}).get("content", ""),
            "latency_ms": round(latency * 1000, 2)
        }
    except Exception as e:
        return {
            "model": model,
            "response": f"ERROR: {e}",
            "latency_ms": -1
        }


# ============================================================
# EVALUATION
# ============================================================

EVALUATION_PROMPT = """You are evaluating how well an AI model understood a Malaysian Malay/Manglish query.

Original Query: {query}
Expected Understanding: {expected}

Model's Response:
{response}

Evaluation Criteria:
{criteria}

Score the response from 1-10:
1-2 = Completely misunderstood, no comprehension of slang
3-4 = Partially understood, missed most slang meanings
5-6 = Moderate understanding, got some slang but missed key terms
7-8 = Good understanding, understood most slang and context
9-10 = Excellent, fully understood all slang, particles, and cultural context

Respond in this exact JSON format:
{{"score": <1-10>, "reasoning": "<brief explanation>"}}
"""

def evaluate_response(test_case: TestCase, response: str, evaluator_model: str = "gpt-4o") -> Dict:
    """Use LLM as judge to evaluate response quality.
    
    Supports:
    - gpt-4o, gpt-5.1, gpt-5.2 (OpenAI)
    - gemini-3-pro, gemini-2.0-flash (Google)
    - claude-opus-4.5 (Anthropic)
    """
    import re
    
    criteria_str = "\n".join(f"- {c}" for c in test_case.evaluation_criteria)
    
    prompt = EVALUATION_PROMPT.format(
        query=test_case.input_query,
        expected=test_case.expected_understanding,
        response=response,
        criteria=criteria_str
    )
    
    try:
        if evaluator_model.startswith("gemini"):
            # Use Google Generative AI
            import google.generativeai as genai
            import os
            
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            
            # Map friendly names to model IDs
            model_map = {
                "gemini-3-pro": "gemini-2.0-flash-exp",  # Use available model
                "gemini-2.0-flash": "gemini-2.0-flash-exp",
                "gemini-1.5-pro": "gemini-1.5-pro",
            }
            model_id = model_map.get(evaluator_model, "gemini-2.0-flash-exp")
            
            model = genai.GenerativeModel(model_id)
            result = model.generate_content(prompt)
            content = result.text
            
        elif evaluator_model.startswith("claude"):
            # Use Anthropic
            import anthropic
            import os
            
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            model_map = {
                "claude-opus-4.5": "claude-opus-4-5-20251101",
                "claude-sonnet-4.5": "claude-sonnet-4-5-20241022",
            }
            model_id = model_map.get(evaluator_model, "claude-opus-4-5-20251101")
            
            message = client.messages.create(
                model=model_id,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            content = message.content[0].text
            
        else:
            # Use OpenAI (default)
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(model=evaluator_model, temperature=0)
            result = llm.invoke(prompt)
            content = result.content
        
        # Parse JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
            
    except Exception as e:
        print(f"Evaluation error: {e}")
    
    return {"score": 0, "reasoning": "Failed to parse evaluation"}


def run_comparison(qwen_model: str = "qwen2.5:7b", output_file: str = "model_comparison_results.json", judge_model: str = "gpt-4o"):
    """Run full comparison between GPT-4o and Qwen."""
    
    system_prompt = """You are a helpful AI assistant that understands Malaysian Malay, English, and Manglish (mixed language).
When the user writes in Malay or Manglish, demonstrate your understanding by:
1. First, acknowledge what you understood from their message
2. Then respond appropriately in their language

Be natural and conversational."""

    results = []
    
    print("=" * 60)
    print(f"Model Comparison: GPT-4o vs {qwen_model} for Malay/Manglish")
    print(f"Judge: {judge_model}")
    print("=" * 60)
    
    for i, tc in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Testing: {tc.id} ({tc.category})")
        print(f"Query: {tc.input_query}")
        
        # Get responses
        gpt_result = call_gpt4o(tc.input_query, system_prompt)
        qwen_result = call_qwen_ollama(tc.input_query, qwen_model, system_prompt)
        
        print(f"  GPT-4o: {gpt_result['response'][:100]}...")
        print(f"  Qwen:   {qwen_result['response'][:100]}...")
        
        # Evaluate both using specified judge
        gpt_eval = evaluate_response(tc, gpt_result["response"], judge_model)
        qwen_eval = evaluate_response(tc, qwen_result["response"], judge_model)
        
        print(f"  Scores - GPT-4o: {gpt_eval['score']}/10, Qwen: {qwen_eval['score']}/10")
        
        results.append({
            "test_case": asdict(tc),
            "gpt4o": {**gpt_result, "evaluation": gpt_eval},
            "qwen": {**qwen_result, "evaluation": qwen_eval}
        })
    
    # Calculate summary
    gpt_scores = [r["gpt4o"]["evaluation"]["score"] for r in results]
    qwen_scores = [r["qwen"]["evaluation"]["score"] for r in results]
    
    summary = {
        "total_tests": len(TEST_CASES),
        "gpt4o": {
            "avg_score": round(sum(gpt_scores) / len(gpt_scores), 2),
            "scores_by_category": _group_scores_by_category(results, "gpt4o")
        },
        "qwen": {
            "model": qwen_model,
            "avg_score": round(sum(qwen_scores) / len(qwen_scores), 2),
            "scores_by_category": _group_scores_by_category(results, "qwen")
        },
        "winner": "gpt4o" if sum(gpt_scores) > sum(qwen_scores) else "qwen" if sum(qwen_scores) > sum(gpt_scores) else "tie"
    }
    
    output = {"summary": summary, "results": results}
    
    # Save results
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"GPT-4o Average Score: {summary['gpt4o']['avg_score']}/5")
    print(f"Qwen ({qwen_model}) Average Score: {summary['qwen']['avg_score']}/5")
    print(f"Winner: {summary['winner'].upper()}")
    print(f"\nDetailed results saved to: {output_file}")
    
    return output


def _group_scores_by_category(results: List[Dict], model_key: str) -> Dict:
    """Group scores by test category."""
    from collections import defaultdict
    
    cat_scores = defaultdict(list)
    for r in results:
        cat = r["test_case"]["category"]
        score = r[model_key]["evaluation"]["score"]
        cat_scores[cat].append(score)
    
    return {cat: round(sum(scores)/len(scores), 2) for cat, scores in cat_scores.items()}


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare GPT-4o vs Qwen on Malay/Manglish understanding")
    parser.add_argument("--qwen-model", default="qwen2.5:7b", help="Qwen model name in Ollama")
    parser.add_argument("--judge", default="gpt-4o", help="Judge model: gpt-4o, gemini-3-pro, claude-opus-4.5")
    parser.add_argument("--output", default="model_comparison_results.json", help="Output file path")
    args = parser.parse_args()
    
    # Check prerequisites based on judge
    if args.judge.startswith("gpt") and not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set (required for GPT judge)")
        exit(1)
    if args.judge.startswith("gemini") and not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY not set (required for Gemini judge)")
        exit(1)
    if args.judge.startswith("claude") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set (required for Claude judge)")
        exit(1)
    
    run_comparison(qwen_model=args.qwen_model, output_file=args.output, judge_model=args.judge)

