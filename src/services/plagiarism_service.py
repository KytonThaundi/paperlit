"""
Plagiarism/originality checking logic for Paperlit.
"""
import difflib
from typing import List

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
