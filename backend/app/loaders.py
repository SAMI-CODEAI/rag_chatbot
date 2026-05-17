import os
from pypdf import PdfReader
from docx import Document

def extract_text_from_file(file_path: str, filename: str) -> str:
    """Extracts text from a given file based on its extension."""
    ext = os.path.splitext(filename)[1].lower()
    text = ""
    
    try:
        if ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
        elif ext == ".docx":
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
                
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                
        else:
            raise ValueError(f"Unsupported file format: {ext}")
            
    except Exception as e:
        raise Exception(f"Error extracting text from {filename}: {str(e)}")
        
    return text
