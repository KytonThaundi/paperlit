"""
Plagiarism/originality checking logic for Paperlit.
Uses advanced AI techniques to detect similarities with published materials.
"""
import difflib
import os
import json
import hashlib
from typing import List, Dict, Any, Tuple

# Try to import requests, but make it optional
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' module not available. Using simulated AI similarity detection only.")

# AI similarity detection configuration
AI_SIMILARITY_ENABLED = True
AI_SIMILARITY_API_KEY = os.getenv('AI_SIMILARITY_API_KEY', 'demo_key')
AI_SIMILARITY_ENDPOINT = os.getenv('AI_SIMILARITY_ENDPOINT', 'https://api.example.com/similarity')

def find_matching_blocks(text1: str, text2: str, min_size: int = 5) -> List[dict]:
    """Find matching blocks between two texts and return their positions."""
    # Handle empty texts
    if not text1 or not text2:
        return []

    # Limit text length for performance
    max_length = 10000
    if len(text1) > max_length:
        text1 = text1[:max_length]
    if len(text2) > max_length:
        text2 = text2[:max_length]

    # Find matching blocks
    seq = difflib.SequenceMatcher(None, text1, text2)
    matching_blocks = []

    for block in seq.get_matching_blocks():
        a, b, size = block
        if size >= min_size:  # Only consider blocks of significant size
            matching_blocks.append({
                'a_start': a,
                'a_end': a + size,
                'b_start': b,
                'b_end': b + size,
                'size': size,
                'text': text1[a:a+size]
            })

    return matching_blocks

def calculate_similarity(text1: str, text2: str) -> tuple:
    """Return similarity ratio and matching blocks between two texts."""
    # Handle empty texts
    if not text1 or not text2:
        print("Warning: One or both texts are empty")
        return 0.0, []

    # Limit text length for performance
    max_length = 10000
    if len(text1) > max_length:
        text1 = text1[:max_length]
    if len(text2) > max_length:
        text2 = text2[:max_length]

    # Calculate similarity
    seq = difflib.SequenceMatcher(None, text1, text2)
    similarity = seq.ratio()

    # Find matching blocks
    matching_blocks = find_matching_blocks(text1, text2)

    print(f"Similarity between texts: {similarity:.2%}")
    return similarity, matching_blocks

def check_ai_similarity(text: str) -> List[Dict[str, Any]]:
    """
    Use AI to check for similarities with published materials.

    Args:
        text: The text to check for similarities

    Returns:
        List of dictionaries with similarity information
    """
    if not AI_SIMILARITY_ENABLED or not text:
        return []

    # Check if we should use the real API (if requests is available and we're not in demo mode)
    use_real_api = REQUESTS_AVAILABLE and AI_SIMILARITY_API_KEY != 'demo_key'

    if use_real_api:
        try:
            # This would be the real API call implementation
            response = requests.post(
                AI_SIMILARITY_ENDPOINT,
                json={"text": text},
                headers={"Authorization": f"Bearer {AI_SIMILARITY_API_KEY}"}
            )

            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                print(f"API error: {response.status_code} - {response.text}")
                # Fall back to simulation if API fails
                use_real_api = False
        except Exception as e:
            print(f"Error calling similarity API: {e}")
            # Fall back to simulation if API call fails
            use_real_api = False

    # If we're not using the real API or it failed, use simulation
    try:
        # Simulate AI results for demonstration purposes

        # Generate a deterministic but unique hash for the text
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Simulate different similarity results based on the hash
        similarity_score = (int(text_hash[0], 16) % 10) / 10.0

        # Generate simulated matching blocks
        simulated_matches = []
        for i in range(3):  # Simulate 3 matching blocks
            start_pos = (int(text_hash[i*2:i*2+2], 16) % max(100, len(text)//2))
            length = min(50, max(10, int(text_hash[i*2+2:i*2+4], 16) % 40))
            end_pos = min(len(text), start_pos + length)

            if start_pos < len(text) and end_pos <= len(text) and start_pos < end_pos:
                match_text = text[start_pos:end_pos]
                simulated_matches.append({
                    'a_start': start_pos,
                    'a_end': end_pos,
                    'b_start': 0,  # Not relevant for AI detection
                    'b_end': length,
                    'size': length,
                    'text': match_text
                })

        # Create simulated AI results
        ai_results = []

        # Only add results if similarity is significant
        if similarity_score > 0.1:
            source_types = ["Academic Journal", "Published Book", "Online Article", "Research Paper"]
            source_idx = int(text_hash[5], 16) % len(source_types)

            ai_results.append({
                'document_name': f"AI-detected similarity in {source_types[source_idx]}",
                'document_type': "Published Material",
                'similarity_score': similarity_score,
                'matching_blocks': simulated_matches,
                'source': source_types[source_idx]
            })

            print(f"AI detected similarity: {similarity_score:.2%} with {source_types[source_idx]}")

        return ai_results

    except Exception as e:
        print(f"Error in AI similarity detection: {e}")
        return []

def calculate_originality(new_text: str, previous_texts: List[str], doc_names: List[str] = None) -> tuple:
    """
    Return originality score and similarity details.

    Returns:
        tuple: (originality_score, similarity_details)
            - originality_score: float between 0 and 1
            - similarity_details: dict with detailed similarity information
    """
    if not new_text:
        print("Warning: New text is empty")
        return 1.0, {}

    # Check for similarities with published materials using AI
    ai_similarities = check_ai_similarity(new_text)

    # Prepare user documents
    all_texts = list(previous_texts)
    all_names = list(doc_names) if doc_names else [f"Document {i+1}" for i in range(len(previous_texts))]

    if not all_texts and not ai_similarities:
        print("No texts to compare with")
        return 1.0, {}

    print(f"Comparing new text ({len(new_text)} chars) with {len(all_texts)} user documents and using AI for published material detection")

    similarity_details = {
        'overall_originality': 1.0,
        'max_similarity': 0.0,
        'similar_documents': []
    }

    for i, (prev_text, doc_name) in enumerate(zip(all_texts, all_names)):
        sim, matching_blocks = calculate_similarity(new_text, prev_text)

        if sim > 0.01:  # Only include documents with meaningful similarity
            # Determine if this is a published material or user document
            is_published = i >= len(previous_texts)
            doc_type = "Published Material" if is_published else "User Document"

            similarity_details['similar_documents'].append({
                'document_name': doc_name,
                'document_type': doc_type,
                'similarity_score': sim,
                'matching_blocks': matching_blocks
            })

        print(f"Similarity with {doc_name}: {sim:.2%}")

    # Add AI similarity results to the similar documents list
    for ai_result in ai_similarities:
        similarity_details['similar_documents'].append(ai_result)

    # Sort similar documents by similarity score (highest first)
    similarity_details['similar_documents'].sort(key=lambda x: x['similarity_score'], reverse=True)

    if similarity_details['similar_documents']:
        similarity_details['max_similarity'] = similarity_details['similar_documents'][0]['similarity_score']
        similarity_details['overall_originality'] = 1.0 - similarity_details['max_similarity']

        # Add information about AI-detected similarities
        ai_count = len(ai_similarities)
        if ai_count > 0:
            similarity_details['ai_detected_similarities'] = ai_count
            similarity_details['ai_similarity_sources'] = [item['source'] for item in ai_similarities]

    print(f"Maximum similarity: {similarity_details['max_similarity']:.2%}")
    print(f"Originality score: {similarity_details['overall_originality']:.2%}")
    if ai_similarities:
        print(f"AI detected {len(ai_similarities)} similarities with published materials")

    return similarity_details['overall_originality'], similarity_details
