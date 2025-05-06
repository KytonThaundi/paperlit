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

    if not os.path.isabs(file_path) and not os.path.exists(file_path):

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        possible_paths = [
            os.path.join(project_root, 'uploads', file_path),
            os.path.join(project_root, 'src', 'uploads', file_path)
        ]

        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break


    if not os.path.exists(file_path):
        print(f"Warning: File not found at {file_path}")
        return ""

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                print(f"Extracted {len(text)} characters from text file: {file_path}")
                return text
        elif ext == '.pdf' and PyPDF2:
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    text += page_text
                print(f"Extracted {len(text)} characters from PDF file: {file_path}")
                return text
        else:
            print(f"Unsupported file extension: {ext}")
    except Exception as e:

        print(f"Error extracting text from {file_path}: {e}")

    return ""
