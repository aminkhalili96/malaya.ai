import os
import yaml
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.summarization.preprocessing import TextNormalizer
from src.rag.retrieval import HybridRetriever

# Optional DSPy enhancement
try:
    from src.chatbot.dspy_optimizer import get_enhanced_prompt, preprocess_query as dspy_preprocess
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

class MalayaChatbot:
    def __init__(self, config_path="config.yaml", use_dspy: bool = False):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        # DSPy enhancement (optional, additive - does not replace LangChain)
        self.use_dspy = use_dspy and DSPY_AVAILABLE
        if self.use_dspy:
            # Get DSPy-enhanced system prompt (better slang understanding)
            self._dspy_enhanced_prompt = get_enhanced_prompt()
        else:
            self._dspy_enhanced_prompt = None
            
        self.normalizer = TextNormalizer()
        self.llm_error = None
        try:
            self.llm = ChatOpenAI(
                model=self.config["model"]["name"],
                temperature=self.config["model"]["temperature"]
            )
        except Exception as exc:
            # Keep the app running and show a friendly error inside the UI
            self.llm = None
            self.llm_error = str(exc)

        # We use a retriever wrapper that can work with or without Tavily
        trusted_domains = self.config.get("rag", {}).get("trusted_domains", [])
        excluded_domains = self.config.get("rag", {}).get("excluded_domains", [])
        self.retriever = HybridRetriever([], trusted_domains=trusted_domains, excluded_domains=excluded_domains)

    def _detect_language(self, text: str) -> str:
        """
        Detect the language of input text.
        Returns: 'malay', 'english', or 'manglish'
        """
        text_lower = text.lower()
        
        # Common Malay-only words/patterns
        malay_indicators = [
            "apa", "bagaimana", "mengapa", "siapa", "bila", "mana", "boleh",
            "tidak", "saya", "kamu", "anda", "dia", "mereka", "kami", "kita",
            "sudah", "belum", "sedang", "akan", "telah", "pernah",
            "selamat", "terima kasih", "tolong", "maaf",
            "baik", "buruk", "besar", "kecil", "banyak", "sedikit",
            "ini", "itu", "sini", "sana", "mahu", "hendak"
        ]
        
        # Common English-only words/patterns
        english_indicators = [
            "what", "how", "why", "who", "when", "where", "which",
            "is", "are", "was", "were", "have", "has", "had",
            "the", "a", "an", "this", "that", "these", "those",
            "can", "could", "would", "should", "will", "shall",
            "please", "thank", "sorry", "hello", "good", "morning", "afternoon", "evening",
            "yes", "no", "maybe", "very", "much", "many", "few"
        ]
        
        # Count matches
        malay_count = sum(1 for word in malay_indicators if word in text_lower)
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        # Check for Manglish patterns (mixing)
        has_malay = malay_count > 0
        has_english = english_count > 0
        
        # Manglish indicators: particles like 'lah', 'kan', 'meh', 'lor'
        manglish_particles = ["lah", "la", "kan", "meh", "lor", "leh", "geh", "hor", "weh", "wei"]
        has_manglish_particle = any(f" {p}" in text_lower or text_lower.endswith(p) for p in manglish_particles)
        
        if has_malay and has_english:
            return "manglish"
        elif has_manglish_particle:
            return "manglish"
        elif malay_count > english_count:
            return "malay"
        elif english_count > malay_count:
            return "english"
        else:
            # Default: check the greeting itself
            malay_greetings = ["halo", "hai", "apa khabar", "selamat"]
            if any(g in text_lower for g in malay_greetings):
                return "malay"
            return "english"

    def process_query(self, user_input: str, chat_history: List[Dict] = []) -> dict:
        """
        1. Detect Language
        2. Normalize (Manglish -> Malay)
        3. Chitchat Detection (Dynamic)
        4. Search (Tavily)
        5. Generate (OpenAI with Citations + Memory + Language Mirroring)
        """
        # Step 0: Detect user's language BEFORE normalization
        detected_language = self._detect_language(user_input)
        
        # Step 1: Normalize
        normalized_query = self.normalizer.normalize(user_input)
        
        if not self.llm:
            return {
                "original_query": user_input,
                "normalized_query": normalized_query,
                "answer": "LLM is not configured. Please set OPENAI_API_KEY and reload.",
                "sources": []
            }

        # Step 1.5: Chitchat Detection (before RAG)
        greeting_patterns = [
            "hi", "hello", "halo", "hey", "hai",
            "apa khabar", "selamat pagi", "selamat petang", "selamat malam",
            "good morning", "good afternoon", "good evening"
        ]
        
        normalized_lower = normalized_query.lower().strip()
        is_greeting = any(normalized_lower == pattern or normalized_lower.startswith(pattern + " ") 
                         for pattern in greeting_patterns)
        
        # Only intercept if it's a SHORT greeting (likely just "Hi" or "Apa khabar")
        # If it's long (e.g. "Hi, what is this?"), let it fall through to RAG.
        is_short = len(normalized_lower.split()) <= 5
        
        if is_greeting and is_short:
            # Build language-aware greeting prompt
            if detected_language == "malay":
                lang_instruction = "The user speaks MALAY. Reply fully in Malay. Do NOT use English."
            elif detected_language == "english":
                lang_instruction = "The user speaks ENGLISH. Reply fully in English. Do NOT use Malay."
            else:
                lang_instruction = "The user speaks MANGLISH (mix of Malay and English). Reply in a casual, fun Manglish style."
            
            greeting_system_prompt = f"""You are Malaya.ai, a witty, friendly AI assistant.
The user just said hello. {lang_instruction}
Be brief (1-2 sentences). Ask a fun follow-up question about their day or what they need help with.
Do NOT be robotic. Be human-like and have 'vibe'."""
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", greeting_system_prompt),
                ("user", "{input}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            
            try:
                greeting_response = chain.invoke({"input": user_input})
            except Exception as e:
                # Fallback if LLM fails - also language-aware
                print(f"Dynamic Greeting Error: {e}")
                if detected_language == "malay":
                    greeting_response = "Halo! Apa khabar? Saya Malaya.ai. Ada apa-apa yang boleh saya bantu?"
                elif detected_language == "english":
                    greeting_response = "Hello! How are you? I'm Malaya.ai. How can I help you today?"
                else:
                    greeting_response = "Halo! Apa khabar? I'm Malaya.ai lah. So, what can I help you with today?"

            return {
                "original_query": user_input,
                "normalized_query": normalized_query,
                "answer": greeting_response,
                "sources": [],
                "detected_language": detected_language
            }

        # Step 2: Contextualize Query (if history exists)
        search_query = normalized_query
        if chat_history:
            search_query = self._condense_question(normalized_query, chat_history)
            print(f"Condensed Query: {search_query}")  # Debug log

        # Step 3: Search (Tavily + local chunks) using the contextualized query
        search_results = self.retriever.search(search_query, k=self.config["rag"]["k"])

        if not search_results:
            return {
                "original_query": user_input,
                "normalized_query": normalized_query,
                "answer": "No context found. Add documents in Q2 or set TAVILY_API_KEY for web search.",
                "sources": []
            }

        context_str, sources_list = self._build_context(search_results)

        # Step 4: Generate Answer (with Memory + Language Mirroring)
        # Use DSPy-enhanced prompt if available (better slang understanding)
        if self.use_dspy and self._dspy_enhanced_prompt:
            system_prompt = self._dspy_enhanced_prompt
        else:
            system_prompt = self.config["system_prompts"]["chatbot"]
        
        # Add language mirroring instruction based on detected language
        if detected_language == "malay":
            lang_hint = "\n\nIMPORTANT: The user is speaking MALAY. Reply fully in Malay."
        elif detected_language == "english":
            lang_hint = "\n\nIMPORTANT: The user is speaking ENGLISH. Reply fully in English."
        else:
            lang_hint = "\n\nIMPORTANT: The user is speaking MANGLISH. Reply in a casual Manglish style."
        
        enhanced_prompt = system_prompt + lang_hint
        
        # Format chat history for prompt
        history_str = ""
        if chat_history:
            # Take last 4 messages to avoid context limit issues
            recent_history = chat_history[-4:]
            for msg in recent_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_str += f"{role}: {msg['content']}\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", enhanced_prompt),
            ("user", "Previous Conversation:\n{chat_history}\n\nContext:\n{context}\n\nQuestion: {question}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        try:
            answer = chain.invoke({
                "chat_history": history_str,
                "context": context_str,
                "question": user_input  # Use original query to preserve language
            })
        except Exception as exc:
            answer = f"LLM error: {exc}"

        # Refusal Logic: If the answer contains refusal phrases, suppress citations
        refusal_phrases = [
            "i don't know", "i do not know", "saya tidak tahu", "tiada maklumat", 
            "tidak mempunyai maklumat", "i'm sorry", "maaf", "cannot answer",
            "tidak pasti", "not sure"
        ]
        
        # Check if answer is short and contains refusal (heuristic)
        is_refusal = any(phrase in answer.lower() for phrase in refusal_phrases)
        
        # Citation Filtering Logic:
        # 1. If refusal, clear sources.
        # 2. If answer does NOT contain citation markers (e.g. [1]), clear sources.
        # This ensures we don't show citations for chitchat/advice where LLM didn't use them.
        import re
        has_citation = bool(re.search(r'\[\d+\]', answer))
        
        if is_refusal or not has_citation:
            sources_list = []

        return {
            "original_query": user_input,
            "normalized_query": normalized_query,
            "answer": answer,
            "sources": sources_list,
            "context": context_str
        }

    def _build_context(self, search_results):
        context_parts = []
        sources_list = []
        source_index_map = {}

        for res in search_results:
            metadata = res.get("metadata", {}) or {}
            source_label = metadata.get("source") or metadata.get("parent_id") or "local"
            if source_label not in source_index_map:
                source_index_map[source_label] = len(sources_list) + 1
                sources_list.append({
                    "index": source_index_map[source_label],
                    "url": metadata.get("source", "Local context")
                })

            idx = source_index_map[source_label]
            score_suffix = ""
            if "scores" in metadata:
                score_suffix = f" (combined score: {metadata['scores'].get('combined')})"
            context_parts.append(f"Source [{idx}]{score_suffix}:\n{res.get('content', '')}")

        context_str = "\n\n".join(context_parts)
        return context_str, sources_list

    def _condense_question(self, question: str, chat_history: List[Dict]) -> str:
        """
        Uses LLM to rewrite a follow-up question into a standalone question.
        """
        if not chat_history:
            return question
            
        # Format history for prompt
        history_str = ""
        # Take last 4 messages
        recent_history = chat_history[-4:]
        for msg in recent_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_str += f"{role}: {msg['content']}\n"

        condense_prompt = self.config["system_prompts"].get("condense_question", 
            "Rephrase the follow-up question to be a standalone question.\nChat History:\n{chat_history}\nFollow Up Input: {question}\nStandalone question:")
            
        prompt = ChatPromptTemplate.from_template(condense_prompt)
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            standalone_question = chain.invoke({
                "chat_history": history_str,
                "question": question
            })
            return standalone_question
        except Exception as e:
            print(f"Condense Error: {e}")
            return question
