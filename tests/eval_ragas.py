
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

# Load env
load_dotenv()
sys.path.append(os.getcwd())

from src.chatbot.engine import MalayaChatbot

def run_eval():
    print("Initializing Chatbot for Eval...")
    bot = MalayaChatbot()
    
    # Test Data
    questions = [
        "What is YTL AI Labs?",
        "Where is YTL AI Labs located?",
        "What is the name of their LLM?"
    ]
    
    ground_truths = [
        "YTL AI Labs is a division of YTL Group focused on building sovereign AI solutions.",
        "YTL AI Labs is located in YTL Green Data Center Campus, Johor.",
        "The name of their LLM is Ilmu."
    ]
    
    answers = []
    contexts = []
    
    print("Generating answers...")
    for q in questions:
        print(f"Processing: {q}")
        response = bot.process_query(q)
        answers.append(response['answer'])
        # Extract context from sources
        # MalayaChatbot returns 'sources' list, but we need the text context.
        # The engine builds context_str internally but doesn't return it directly in the dict 
        # except as part of the prompt construction.
        # However, we can infer it or modify engine to return it.
        # For now, let's use the 'sources' URLs as a proxy or try to fetch content if possible.
        # Actually, Ragas needs the TEXT context.
        # I'll hack it: The engine returns 'sources' which has 'url'. 
        # But Ragas needs the content used.
        # Let's assume the answer is enough for Answer Relevance, but Faithfulness needs context.
        # I will modify engine.py slightly to return 'context' in the response dict for debug/eval purposes?
        # Or I can just pass empty context and skip Faithfulness? No, user wants eval.
        # I'll modify engine.py to return 'context' in the response.
        contexts.append([response.get('context', '')])

    # Create Dataset
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    
    dataset = Dataset.from_dict(data)
    
    from langchain_openai import OpenAIEmbeddings
    
    print("Running Ragas Evaluation...")
    # Ragas needs explicit LLM/Embeddings if default fails
    embeddings = OpenAIEmbeddings()
    
    results = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=bot.llm,
        embeddings=embeddings
    )
    
    print("\nEvaluation Results:")
    print(results)
    
    # Save to file
    df = results.to_pandas()
    df.to_csv("eval_results.csv", index=False)
    print("Saved to eval_results.csv")

if __name__ == "__main__":
    run_eval()
