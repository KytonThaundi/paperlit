"""
Blueprint for plagiarism/originality checking and document upload in Paperlit.
"""
from flask import Blueprint, request, redirect, url_for, flash, session, render_template, current_app as app
from werkzeug.utils import secure_filename
import os
from src.utils.file_extract import extract_text_from_file
from src.services.plagiarism_service import calculate_originality
from src.models import db, Document

plagiarism_bp = Blueprint('plagiarism', __name__)

@plagiarism_bp.route('/upload_document', methods=['POST'])
def upload_document():
    if 'user' not in session or 'user_id' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    document_name = request.form.get('document_name')
    document_file = request.files.get('document_file')

    if not document_name or not document_file:
        flash('Both document name and file are required.', 'warning')
        return redirect(url_for('home'))

    # Check if we're editing an existing document
    editing_document_id = session.pop('editing_document_id', None)
    editing = editing_document_id is not None

    # If editing, get the existing document
    existing_document = None
    if editing:
        existing_document = Document.query.get(editing_document_id)
        if not existing_document or existing_document.user_id != session['user_id']:
            flash('Document not found or access denied.', 'danger')
            return redirect(url_for('home'))

        # Remove the editing document name from session
        session.pop('editing_document_name', None)

        # If editing, delete the old file if it exists
        if existing_document.file_path:
            # Try to find the old file
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            possible_paths = [
                os.path.join(project_root, 'uploads', existing_document.file_path),
                os.path.join(project_root, 'src', 'uploads', existing_document.file_path),
                existing_document.file_path  # In case it's already a full path
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        print(f"Deleted old file: {path}")
                    except Exception as e:
                        print(f"Error deleting old file: {e}")
                    break

    filename = secure_filename(document_file.filename)
    user_id = session['user_id']
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)
    document_file.save(save_path)

    # Extract text and calculate originality
    print(f"Extracting text from new document: {save_path}")
    new_text = extract_text_from_file(save_path)

    # Get previous documents from the same user
    previous_docs = Document.query.filter(Document.user_id==user_id, Document.id != None).all()
    print(f"Found {len(previous_docs)} previous documents for comparison")

    # Extract text from previous documents
    previous_texts = []
    doc_names = []
    for doc in previous_docs:
        if doc.file_path:
            # Try to find the file in the uploads directory
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            possible_paths = [
                os.path.join(project_root, 'uploads', doc.file_path),
                os.path.join(project_root, 'src', 'uploads', doc.file_path),
                doc.file_path  # In case it's already a full path
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    print(f"Found previous document at: {path}")
                    text = extract_text_from_file(path)
                    if text:
                        previous_texts.append(text)
                        doc_names.append(doc.document_name)
                    break

    print(f"Extracted text from {len(previous_texts)} previous documents")

    # Calculate originality score and get similarity details
    originality_score, similarity_details = calculate_originality(new_text, previous_texts, doc_names)

    # Ensure originality score is between 0 and 1
    originality_score = max(0.0, min(1.0, originality_score))

    # If editing, update the existing document
    if editing and existing_document:
        existing_document.document_name = document_name
        existing_document.file_path = filename
        existing_document.originality_score = originality_score
        existing_document.set_similarity_details(similarity_details)
        db.session.commit()
        flash(f'Document updated successfully! New originality score: {originality_score:.2%}', 'success')
    else:
        # Create a new document
        new_document = Document(
            user_id=user_id,
            document_name=document_name,
            file_path=filename,  # Store just the filename for consistency
            originality_score=originality_score
        )
        # Store similarity details
        new_document.set_similarity_details(similarity_details)
        db.session.add(new_document)
        db.session.commit()
        flash(f'Document uploaded successfully! Originality score: {originality_score:.2%}', 'success')

    return redirect(url_for('home'))
