from langchain_openai import ChatOpenAI, OpenAIEmbeddings
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
    if not settings.OPENAI_API_KEY:
        return
        
    # Standard text embedding model
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL, 
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    # Persistent Chroma DB
    vectorstore = Chroma(
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        embedding_function=embeddings
    )
    
    # Chat LLM
    llm = ChatOpenAI(
        model=settings.MODEL_NAME,
        temperature=0.0,
        openai_api_key=settings.OPENAI_API_KEY
    )

def get_retrieval_chain(memory: ConversationBufferMemory):
    if not vectorstore or not llm:
        init_rag()
        if not vectorstore or not llm:
            raise ValueError("RAG system not initialized. Check API keys.")
            
    from langchain.retrievers.multi_query import MultiQueryRetriever
    
    # 1. Base Retriever with MMR for diversity
    base_retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": settings.TOP_K_RETRIEVAL,
            "fetch_k": settings.FETCH_K
        }
    )
    
    # 2. Multi-Query Retriever for question expansion (fixes semantic misses)
    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever, 
        llm=llm
    )
    
    # Grounding prompt
    system_template = """You are an intelligent, helpful AI assistant. The user has uploaded documents, and the 'Additional Context' below contains excerpts from those uploaded files.
    When the user asks about the 'uploaded file', 'document', or 'book', they are referring to this context. ALWAYS treat this context as the contents of the uploaded files. Do not say you cannot read files.
    If the context contains information relevant to the user's question, prioritize using it.
    If the context is irrelevant to a general question, use your general knowledge to give a helpful and accurate response.
    
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
