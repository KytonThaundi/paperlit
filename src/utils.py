import os
import difflib
from typing import List

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
    except Exception:
        pass
    return ""

def calculate_similarity(text1: str, text2: str) -> float:
    """Return similarity ratio between two texts (0-1)."""
    seq = difflib.SequenceMatcher(None, text1, text2)
    return seq.ratio()

def calculate_originality(new_text: str, previous_texts: List[str]) -> float:
    """Return originality score: 1 - max similarity to any previous text."""
    if not previous_texts:
        return 1.0
    max_sim = max(calculate_similarity(new_text, t) for t in previous_texts)
    return 1.0 - max_sim
