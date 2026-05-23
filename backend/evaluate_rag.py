import os
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevance,
    context_precision,
    context_recall,
)
from app.rag import get_retrieval_chain, init_rag
from app.config import settings
from langchain.memory import ConversationBufferMemory
from langchain_ollama import ChatOllama

# Prepare Evaluation Data
# In a real scenario, you'd have a ground_truth answer for each question.
test_questions = [
    "What is the main topic of the uploaded document?",
    "Can you summarize the second chapter?",
    "What are the key findings mentioned in the text?",
    # Add more relevant questions here
]

# Ground truth is required for some metrics like context_recall
# For this demonstration, we'll use placeholder ground truths if not available
ground_truths = [
    "The document discusses DBMS concepts and relational algebra.",
    "The second chapter covers ER modeling and database design.",
    "The key findings include the importance of normalization and indexing.",
]

def run_evaluation():
    print("Initializing RAG system...")
    init_rag()
    
    # Setup for Ragas evaluation using local Ollama
    # Note: Llama 3.2 1b might be weak for evaluation scoring. 
    # A larger model like llama3.1 (8B) is recommended for more accurate scores.
    evaluator_llm = ChatOllama(model=settings.MODEL_NAME, base_url=settings.OLLAMA_BASE_URL)
    
    data = []
    
    print(f"Generating responses for {len(test_questions)} questions...")
    for i, question in enumerate(test_questions):
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        chain = get_retrieval_chain(memory)
        
        response = chain.invoke({"question": question})
        
        # Prepare data for RAGAS
        data.append({
            "question": question,
            "answer": response["answer"],
            "contexts": [doc.page_content for doc in response["source_documents"]],
            "ground_truth": ground_truths[i] if i < len(ground_truths) else ""
        })
        print(f"Question {i+1} processed.")

    # Convert to Dataset
    dataset = Dataset.from_pandas(pd.DataFrame(data))
    
    print("Running Ragas evaluation...")
    # Wrap faithfulness and other metrics with the evaluator LLM
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevance,
            context_precision,
            context_recall,
        ],
        llm=evaluator_llm,
        embeddings=None # It will use default or we could specify OllamaEmbeddings
    )
    
    print("\nEvaluation Results:")
    print(result)
    
    # Export to CSV
    df = result.to_pandas()
    df.to_csv("rag_evaluation_results.csv", index=False)
    print("\nDetailed results saved to 'rag_evaluation_results.csv'")

if __name__ == "__main__":
    run_evaluation()
