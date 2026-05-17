from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String, primary_key=True, index=True)
    title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"), index=True)
    role = Column(String) # 'human' or 'ai'
    content = Column(Text)
    sources = Column(Text, nullable=True) # JSON stringified
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
