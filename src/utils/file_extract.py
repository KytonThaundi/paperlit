"""
File extraction utilities for Paperlit.
Supports .txt and .pdf (if PyPDF2 is installed).
"""
import os
from typing import Optional

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

def extract_text_from_file(file_path: str) -> str:
    """Extract text from a .txt or .pdf file. Returns empty string if unsupported or error."""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif ext == '.pdf' and PyPDF2:
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text
    except Exception as e:
        # Log or handle extraction error
        pass
    return ""
