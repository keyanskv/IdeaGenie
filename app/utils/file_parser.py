import os
from pypdf import PdfReader
from docx import Document
from app.utils.logger import logger

def parse_file(file_path: str) -> str:
    """Extracts text from various file formats."""
    ext = os.path.splitext(file_path)[1].lower()
    content = ""
    
    try:
        if ext == ".txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                content += page.extract_text() + "\n"
        elif ext == ".docx":
            doc = Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        else:
            logger.warning(f"Unsupported file extension: {ext}")
            return f"Error: Unsupported file type {ext}"
            
        return content.strip()
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}")
        return f"Error parsing file: {str(e)}"
