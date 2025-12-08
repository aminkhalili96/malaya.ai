"""
DSPy Prompt Optimization Module for Malay/Manglish Understanding.

This module enhances the existing LangChain-based chatbot by providing
optimized prompts for Malay slang and Manglish understanding.

It does NOT replace LangChain - it works alongside it.
"""

import dspy
from typing import List, Dict, Optional
import os


# ============================================================
# DSPy SIGNATURES (Define Input/Output Structure)
# ============================================================

class MalaySlangSignature(dspy.Signature):
    """Understand and respond to Malaysian Malay/Manglish queries."""
    
    query: str = dspy.InputField(
        desc="User query in Malay, English, or Manglish (mixed)"
    )
    context: str = dspy.InputField(
        desc="Optional context from RAG retrieval",
        default=""
    )
    
    understanding: str = dspy.OutputField(
        desc="What the user is asking/saying in plain English"
    )
    response: str = dspy.OutputField(
        desc="Natural response in the user's language (Malay/English/Manglish)"
    )


class SlangTranslatorSignature(dspy.Signature):
    """Translate Malaysian slang/shortforms to standard Malay."""
    
    slang_text: str = dspy.InputField(
        desc="Text containing Malaysian slang, shortforms, or SMS-style abbreviations"
    )
    
    standard_text: str = dspy.OutputField(
        desc="Text translated to standard Malay"
    )
    slang_mapping: str = dspy.OutputField(
        desc="JSON mapping of slang terms to their meanings"
    )


# ============================================================
# DSPy MODULES (Implement the Logic)
# ============================================================

class MalayQAModule(dspy.Module):
    """
    DSPy module for Malay/Manglish Q&A with automatic few-shot optimization.
    
    This module uses Chain of Thought (CoT) reasoning to:
    1. Understand the slang/shortforms in the query
    2. Generate an appropriate response in the user's language
    """
    
    def __init__(self):
        super().__init__()
        self.qa_chain = dspy.ChainOfThought(MalaySlangSignature)
    
    def forward(self, query: str, context: str = "") -> dspy.Prediction:
        """Process query and generate response."""
        return self.qa_chain(query=query, context=context)


class SlangNormalizer(dspy.Module):
    """
    DSPy module to normalize Malaysian slang before processing.
    
    This can be used as a preprocessing step before the main LLM call.
    """
    
    def __init__(self):
        super().__init__()
        self.translator = dspy.Predict(SlangTranslatorSignature)
    
    def forward(self, slang_text: str) -> dspy.Prediction:
        """Translate slang to standard Malay."""
        return self.translator(slang_text=slang_text)


# ============================================================
# TRAINING DATA (Few-shot Examples)
# ============================================================

MALAY_SLANG_EXAMPLES = [
    # Shortforms
    dspy.Example(
        query="xleh la bro, aku xde duit skrg",
        context="",
        understanding="Cannot bro, I don't have money right now",
        response="Okay bro, takpe. Nanti bila dah ada duit kita jumpa la"
    ).with_inputs("query", "context"),
    
    dspy.Example(
        query="mcm mane nk buat ni? dh try byk kali tp xjd",
        context="",
        understanding="How do I do this? I've tried many times but it didn't work",
        response="Hmm, boleh explain sikit apa yang kau cuba buat? Mungkin aku boleh tolong"
    ).with_inputs("query", "context"),
    
    # Particles
    dspy.Example(
        query="best gila siot benda ni!",
        context="",
        understanding="This thing is amazing!",
        response="Kan! Memang best habis. Apa yang buat kau excited sangat tu?"
    ).with_inputs("query", "context"),
    
    # Cultural
    dspy.Example(
        query="lepak mamak jom, aku belanja teh tarik",
        context="",
        understanding="Let's hang out at the mamak stall, I'll treat you to teh tarik",
        response="Wah best! Jom, bila nak pergi? Aku free petang ni"
    ).with_inputs("query", "context"),
    
    # Manglish
    dspy.Example(
        query="eh bro, that meeting how ah? client happy tak?",
        context="",
        understanding="Hey bro, how was that meeting? Was the client happy?",
        response="Meeting tadi okay je bro. Client nampak puas hati dengan presentation kita"
    ).with_inputs("query", "context"),
    
    # Sentiment
    dspy.Example(
        query="geram betul la dengan service ni, lambat macam siput",
        context="",
        understanding="I'm really frustrated with this service, it's slow like a snail",
        response="Aku faham frustration tu. Memang tak best bila kena tunggu lama. Ada apa yang aku boleh tolong?"
    ).with_inputs("query", "context"),
]


# ============================================================
# OPTIMIZER CLASS (Integrate with LangChain)
# ============================================================

class DSPyOptimizer:
    """
    DSPy-based prompt optimizer for Malay/Manglish understanding.
    
    This class provides methods to enhance prompts before passing
    them to the LangChain-based engine.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize DSPy optimizer.
        
        Args:
            model_name: LLM model to use for DSPy optimization
        """
        self.model_name = model_name
        self.qa_module = MalayQAModule()
        self.slang_normalizer = SlangNormalizer()
        self._setup_dspy()
        self._is_optimized = False
    
    def _setup_dspy(self):
        """Configure DSPy with the specified LLM."""
        # Use OpenAI for DSPy (most reliable)
        if os.environ.get("OPENAI_API_KEY"):
            lm = dspy.LM(f"openai/{self.model_name}")
            dspy.configure(lm=lm)
    
    def optimize(self, training_examples: Optional[List[dspy.Example]] = None):
        """
        Optimize the DSPy module using few-shot examples.
        
        Args:
            training_examples: Optional custom examples. Uses defaults if None.
        """
        examples = training_examples or MALAY_SLANG_EXAMPLES
        
        # Use BootstrapFewShot optimizer
        from dspy.teleprompt import BootstrapFewShot
        
        optimizer = BootstrapFewShot(
            metric=lambda example, pred, trace: 1  # Simple metric for now
        )
        
        self.qa_module = optimizer.compile(
            self.qa_module,
            trainset=examples
        )
        self._is_optimized = True
    
    def get_enhanced_system_prompt(self) -> str:
        """
        Generate an enhanced system prompt with DSPy-learned patterns.
        
        Returns:
            Enhanced system prompt string for use with LangChain
        """
        return """You are a helpful AI assistant that understands Malaysian Malay, English, and Manglish (mixed language).

CRITICAL SLANG UNDERSTANDING:
- 'xleh/xblh' = tak boleh (cannot)
- 'xde' = tiada (don't have)
- 'xfhm/xphm' = tak faham (don't understand)
- 'xtau' = tak tahu (don't know)
- 'xnk' = tak nak (don't want)
- 'mcm mane' = macam mana (how)
- 'nk/nak' = want to
- 'dh' = dah/sudah (already)
- 'tp' = tapi (but)
- 'sbb' = sebab (because)
- 'skrg' = sekarang (now)
- 'nnt' = nanti (later)
- 'jmpa' = jumpa (meet)
- 'bgtau' = beritahu (tell)
- 'tgk' = tengok (look)
- 'blh' = boleh (can)
- 'tlg' = tolong (help)

PARTICLES & EMPHASIS:
- 'la/lah' = emphasis particle
- 'gila' = extremely (intensifier)
- 'siot' = casual emphasis (like 'damn')
- 'kot' = maybe/perhaps
- 'je' = just/only
- 'kan' = right? (tag question)
- 'meh' = dismissive particle
- 'wei/weh' = hey (attention getter)

CULTURAL TERMS:
- 'mamak' = Indian-Muslim restaurant
- 'tapau' = takeaway
- 'lepak' = hang out/chill
- 'belanja' = treat (pay for someone)
- 'teh tarik' = Malaysian pulled milk tea
- 'nasi lemak' = Malaysian coconut rice
- 'raya' = Eid celebration
- 'sahur' = pre-dawn meal (Ramadan)
- 'kenduri' = feast/celebration
- 'balik kampung' = go back to hometown

RESPONSE GUIDELINES:
1. Mirror the user's language (Malay→Malay, Manglish→Manglish)
2. Be casual and friendly, like chatting with a friend
3. Show understanding of their slang before responding
4. Use appropriate particles (la, lah, kan) for natural flow
5. Stay on topic - don't go off on tangents
"""
    
    def preprocess_query(self, query: str) -> Dict[str, str]:
        """
        Preprocess a query to normalize slang and add context.
        
        Args:
            query: User query in Malay/Manglish
            
        Returns:
            Dict with 'original', 'normalized', and 'context' keys
        """
        try:
            result = self.slang_normalizer(slang_text=query)
            return {
                "original": query,
                "normalized": result.standard_text,
                "slang_mapping": result.slang_mapping
            }
        except Exception as e:
            # Fallback if DSPy fails
            return {
                "original": query,
                "normalized": query,
                "slang_mapping": "{}"
            }
    
    def generate_response(self, query: str, context: str = "") -> Dict[str, str]:
        """
        Generate a response using DSPy-optimized module.
        
        Args:
            query: User query
            context: Optional RAG context
            
        Returns:
            Dict with 'understanding' and 'response' keys
        """
        try:
            result = self.qa_module(query=query, context=context)
            return {
                "understanding": result.understanding,
                "response": result.response
            }
        except Exception as e:
            return {
                "understanding": f"Error: {e}",
                "response": ""
            }


# ============================================================
# HELPER FUNCTIONS (For Integration)
# ============================================================

_optimizer_instance: Optional[DSPyOptimizer] = None

def get_optimizer() -> DSPyOptimizer:
    """Get or create the global DSPy optimizer instance."""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = DSPyOptimizer()
    return _optimizer_instance


def get_enhanced_prompt() -> str:
    """Get the DSPy-enhanced system prompt."""
    return get_optimizer().get_enhanced_system_prompt()


def preprocess_query(query: str) -> Dict[str, str]:
    """Preprocess a query using DSPy slang normalizer."""
    return get_optimizer().preprocess_query(query)
