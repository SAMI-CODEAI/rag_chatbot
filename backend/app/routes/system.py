from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChatMessage, ChatSession
from app.config import settings
import os
import shutil

router = APIRouter()

@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "model": settings.MODEL_NAME,
        "embedding_model": settings.EMBEDDING_MODEL
    }

@router.delete("/reset")
async def reset_system(db: Session = Depends(get_db)):
    # Clear SQLite Chat History
    db.query(ChatMessage).delete()
    db.query(ChatSession).delete()
    db.commit()

    # Clear uploads
    if os.path.exists(settings.UPLOAD_DIRECTORY):
        for filename in os.listdir(settings.UPLOAD_DIRECTORY):
            file_path = os.path.join(settings.UPLOAD_DIRECTORY, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                pass
                
    # Clear Chroma DB natively from memory
    import app.rag as rag
    if rag.vectorstore:
        try:
            rag.vectorstore.delete_collection()
            rag.vectorstore = None
        except Exception as e:
            pass
            
    # Clear physically from disk
    if os.path.exists(settings.CHROMA_PERSIST_DIRECTORY):
        try:
            shutil.rmtree(settings.CHROMA_PERSIST_DIRECTORY, ignore_errors=True)
            os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        except Exception as e:
            pass
            
    # Resetting memory happens at the chain instantiation
    return {"message": "System reset successfully"}
