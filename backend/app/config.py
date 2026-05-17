import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    CHUNKING_SIZE: int = 1000
    CHUNKING_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 8
    FETCH_K: int = 25
    CHROMA_PERSIST_DIRECTORY: str = "chroma_db"
    UPLOAD_DIRECTORY: str = "uploads"

settings = Settings()
