from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
from langchain.memory import ConversationBufferMemory
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChatMessage
from app.rag import get_retrieval_chain, init_rag

router = APIRouter()

# Simple dict to hold session memory (In production, use Redis or Postgres)
# In-memory backup
sessions_memory: Dict[str, ConversationBufferMemory] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

class MessageBase(BaseModel):
    role: str
    content: str
    
class SourceDoc(BaseModel):
    content: str
    metadata: dict

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDoc]

@router.get("/history")
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp).all()
    return [{"role": m.role, "content": m.content, "sources": m.sources} for m in messages]

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        # Rehydrate memory from SQLite if this is a new server lifecycle
        if req.session_id not in sessions_memory:
            memory = ConversationBufferMemory(
                memory_key="chat_history", 
                return_messages=True,
                output_key="answer"
            )
            past_messages = db.query(ChatMessage).filter(ChatMessage.session_id == req.session_id).order_by(ChatMessage.timestamp).all()
            for msg in past_messages:
                if msg.role == "human":
                    memory.chat_memory.add_user_message(msg.content)
                elif msg.role == "ai":
                    memory.chat_memory.add_ai_message(msg.content)
            sessions_memory[req.session_id] = memory
            
        memory = sessions_memory[req.session_id]
        
        # Check if vectorstore has data
        import app.rag as rag
        rag.init_rag() # Initialize so vectorstore is no longer None
        
        has_docs = False
        if rag.vectorstore:
            try:
                if rag.vectorstore._collection.count() > 0:
                    has_docs = True
            except:
                pass
                
        if has_docs:
            chain = rag.get_retrieval_chain(memory)
            response = chain.invoke({"question": req.message})
            
            sources = []
            if "source_documents" in response:
                for doc in response["source_documents"]:
                    sources.append(
                        SourceDoc(
                            content=doc.page_content,
                            metadata=doc.metadata
                        )
                    )
                    
            final_answer = response["answer"]
        else:
            chain = rag.get_general_chain(memory)
            response = chain.invoke({"question": req.message})
            final_answer = response["answer"]
            sources = []
            
        # Save to SQLite Database
        sources_json = json.dumps([s.model_dump() for s in sources]) if sources else None
        
        human_msg = ChatMessage(session_id=req.session_id, role="human", content=req.message)
        ai_msg = ChatMessage(session_id=req.session_id, role="ai", content=final_answer, sources=sources_json)
        
        db.add(human_msg)
        db.add(ai_msg)
        db.commit()
            
        return ChatResponse(
            answer=final_answer,
            sources=sources
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
