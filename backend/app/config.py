import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # OPENAI_API_KEY removed for Ollama
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama3.2:1b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    CHUNKING_SIZE: int = 500
    CHUNKING_OVERLAP: int = 100
    TOP_K_RETRIEVAL: int = 20  # Increase to 20 for initial retrieval before re-ranking
    FETCH_K: int = 40
    CHROMA_PERSIST_DIRECTORY: str = "chroma_db"
    UPLOAD_DIRECTORY: str = "uploads"

settings = Settings()
