import os
import pandas as pd
from datetime import datetime
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from app.rag import get_retrieval_chain, init_rag
from app.config import settings
from langchain.memory import ConversationBufferWindowMemory
from langchain_ollama import ChatOllama
from ragas.run_config import RunConfig

# Prepare Evaluation Data
test_questions = [
    "What is the main topic of the uploaded document?",
    "Can you summarize the second chapter?",
    "What are the key findings mentioned in the text?",
]

ground_truths = [
    "The document discusses DBMS concepts and relational algebra.",
    "The second chapter covers ER modeling and database design.",
    "The key findings include the importance of normalization and indexing.",
]

def run_evaluation():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing RAG system...", flush=True)
    init_rag()
    
    # Recommendation: Use a larger model for evaluation for better accuracy.
    # Run 'ollama pull llama3.1:8b' before starting this script.
    EVALUATOR_MODEL = "llama3.1:8b" 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Setting up evaluator with model: {EVALUATOR_MODEL}", flush=True)
    evaluator_llm = ChatOllama(
        model=EVALUATOR_MODEL, 
        base_url=settings.OLLAMA_BASE_URL,
        timeout=1800,
        num_predict=1024, # Limit evaluator response length
    )
    
    data = []
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating responses for {len(test_questions)} questions...", flush=True)
    for i, question in enumerate(test_questions):
        print(f"  > [{datetime.now().strftime('%H:%M:%S')}] Processing Question {i+1}/{len(test_questions)}: '{question}'", flush=True)
        
        # Fresh memory for each question; k=0 for one-shot evaluation
        memory = ConversationBufferWindowMemory(k=0, memory_key="chat_history", return_messages=True, output_key="answer")
        chain = get_retrieval_chain(memory)
        
        start_time = datetime.now()
        response = chain.invoke({"question": question})
        duration = (datetime.now() - start_time).total_seconds()
        
        data.append({
            "question": question,
            "answer": response["answer"],
            "contexts": [doc.page_content for doc in response["source_documents"]],
            "ground_truth": ground_truths[i] if i < len(ground_truths) else ""
        })
        print(f"    - Done in {duration:.2f}s", flush=True)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating responses finished.", flush=True)

    dataset = Dataset.from_pandas(pd.DataFrame(data))
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running Ragas evaluation...", flush=True)
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=evaluator_llm,
        embeddings=None,
        run_config=RunConfig(timeout=1800, max_workers=2, max_retries=3) # Increased max_workers to 2
    )
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Evaluation Results:", flush=True)
    print(result, flush=True)
    
    df = result.to_pandas()
    df.to_csv("rag_evaluation_results.csv", index=False)
    print(f"\nDetailed results saved to 'rag_evaluation_results.csv'", flush=True)

if __name__ == "__main__":
    run_evaluation()
