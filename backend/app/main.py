from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, upload, system
from app.config import settings
from app.database import engine, Base
import uvicorn
import os

# Create DB Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Conversational RAG Chatbot API",
    description="API for uploading documents and questioning them via RAG",
    version="1.0.0"
)

# Configure CORS
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allowing all for dev, ideally restrict to origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(system.router, prefix="/api/system", tags=["System"])

@app.on_event("startup")
async def startup_event():
    # Make sure required directories exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("chroma_db", exist_ok=True)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
