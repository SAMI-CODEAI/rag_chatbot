from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
import os
import uuid
import shutil
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from app.loaders import extract_text_from_file
from app.config import settings
import app.rag as rag

router = APIRouter()

@router.post("/")
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    # Ensure initialized
    rag.init_rag()
    if not rag.vectorstore:
        raise HTTPException(status_code=500, detail="Vector DB not initialized (Check your OPENAI_API_KEY in .env)")
        
    processed_files = []
    
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".pdf", ".docx", ".txt"]:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
            
        # Save temp file
        temp_id = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIRECTORY, f"{temp_id}_{file.filename}")
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            # Extract Text
            text = extract_text_from_file(file_path, file.filename)
            
            # Chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNKING_SIZE,
                chunk_overlap=settings.CHUNKING_OVERLAP,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = text_splitter.split_text(text)
            
            # Create Langchain Documents
            docs = [
                LangchainDocument(
                    page_content=chunk,
                    metadata={"source": file.filename, "chunk_id": i}
                ) for i, chunk in enumerate(chunks)
            ]
            
            # Add to vector store
            rag.vectorstore.add_documents(docs)
            processed_files.append(file.filename)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")
            
    return {
        "message": "Files successfully uploaded and processed",
        "processed_files": processed_files
    }
