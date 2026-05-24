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
from langchain_ollama import ChatOllama, OllamaEmbeddings
from ragas.run_config import RunConfig

# Prepare Evaluation Data
test_questions = [
    "What is a Database Management System (DBMS)?",
    "What are the different types of keys in a database?",
    "Explain the basic operators in Relational Algebra.",
    "What are the different states of a transaction?",
    "What is an ER diagram and what are its components?",
]

ground_truths = [
    "A DBMS is a software for storing and retrieving users' data while considering appropriate security measures. It consists of a group of programs which manipulate the database.",
    "Types of keys include Super Key (set of attributes that can identify each tuple uniquely), Candidate Key (minimal set of attributes for unique identification), and Primary Key (a candidate key selected by the database designer, which is unique and NOT NULL).",
    "Basic operators in Relational Algebra include Selection (σ) to select rows based on conditions, Projection (∏) to project columns, Cross Product (X) returning m*n rows, and Union (U) returning tuples in either R1 or R2.",
    "Transaction states include Active State (instructions being executed, changes stored in buffer), Partially Committed State (after last instruction executed), and the transaction must follow ACID properties.",
    "An ER diagram is a conceptual model that gives the graphical representation of the logical structure of the database. It is composed of Entity Sets, Attributes, and Relationship Sets.",
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
    
    # Use the same embeddings as the RAG system for evaluation
    evaluator_embeddings = OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL
    )
    
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
        embeddings=evaluator_embeddings,
        run_config=RunConfig(timeout=1800, max_workers=2, max_retries=3) # Increased max_workers to 2
    )
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Evaluation Results:", flush=True)
    print(result, flush=True)
    
    df = result.to_pandas()
    df.to_csv("rag_evaluation_results.csv", index=False)
    print(f"\nDetailed results saved to 'rag_evaluation_results.csv'", flush=True)

if __name__ == "__main__":
    run_evaluation()
