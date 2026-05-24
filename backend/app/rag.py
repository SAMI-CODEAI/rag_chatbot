from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
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
    
    # Chat LLM with generation limit for speed (1B model)
    llm = ChatOllama(
        model=settings.MODEL_NAME,
        temperature=0.0,
        base_url=settings.OLLAMA_BASE_URL,
        num_predict=512
    )

def get_retrieval_chain(memory: ConversationBufferMemory):
    if not vectorstore or not llm:
        init_rag()
        if not vectorstore or not llm:
            raise ValueError("RAG system not initialized.")
            
    # MMR retrieval — balances relevance with diversity across document sections
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 8, "fetch_k": 20, "lambda_mult": 0.7}
    )
    
    # Grounding prompt — handles both specific and broad/overview questions
    system_template = """You are a helpful and accurate AI assistant. Answer the user's question using ONLY the context provided below.

Rules:
1. If the context contains the answer, provide it clearly and concisely.
2. If the question is broad or asks for an overview (e.g., "what topics are covered"), summarize the key topics and themes present in the context.
3. If the context truly contains no relevant information, say: "I'm sorry, but the provided documentation does not contain information to answer this question."
4. DO NOT use your internal knowledge to fill in gaps. Stay strictly to the provided context.

Context:
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
