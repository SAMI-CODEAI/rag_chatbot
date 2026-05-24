from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
from app.config import settings

# Global instances (init lazily as they require API keys)
embeddings = None
vectorstore = None
llm = None

def init_rag():
    global embeddings, vectorstore, llm
    
    # Ollama text embedding model
    embeddings = OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL
    )
    
    # Persistent Chroma DB
    vectorstore = Chroma(
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        embedding_function=embeddings
    )
    
    # Chat LLM with generation limit for speed
    llm = ChatOllama(
        model=settings.MODEL_NAME,
        temperature=0.0,
        base_url=settings.OLLAMA_BASE_URL,
        num_predict=512  # Prevent infinite loops/long responses
    )

def get_retrieval_chain(memory: ConversationBufferMemory):
    if not vectorstore or not llm:
        init_rag()
        if not vectorstore or not llm:
            raise ValueError("RAG system not initialized. Check API keys.")
            
    # Base retriever with initial fetch_k
    base_retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": settings.FETCH_K,
            "score_threshold": 0.2, # Slightly lowered to ensure we don't miss relevant but low-scoring chunks
        }
    )
    
    # Reranker compressor
    compressor = FlashrankRerank(top_n=settings.TOP_K_RETRIEVAL)
    
    # Combined compression retriever
    retriever = ContextualCompressionRetriever(
        base_compressor=compressor, 
        base_retriever=base_retriever
    )
    
    # Grounding prompt
    system_template = """You are a specialized AI assistant that answers questions based ONLY on the provided context.
    
    CRITICAL INSTRUCTIONS:
    1. If the 'Additional Context' below contains information that can answer the user's question, you MUST use it.
    2. Even if the information is brief or partial, provide the best answer possible based ONLY on that context.
    3. If the context is empty or completely irrelevant, only then use your general knowledge, but prioritize the context.
    4. Do NOT say "I cannot read files" or "I don't have access to documents". You HAVE access to the excerpts below.
    
    Additional Context:
    {context}
    """
    
    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
    prompt = ChatPromptTemplate.from_messages(messages)

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": prompt}
    )
    return chain

def get_general_chain(memory: ConversationBufferMemory):
    if not llm:
        init_rag()
        if not llm:
            raise ValueError("RAG system not initialized. Check API keys.")
            
    prompt_template = """You are a helpful AI assistant.
    
Current conversation:
{chat_history}
Human: {question}
AI:"""
    prompt = PromptTemplate(input_variables=["chat_history", "question"], template=prompt_template)
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        output_key="answer"
    )
    return chain
