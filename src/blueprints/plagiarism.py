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

    filename = secure_filename(document_file.filename)
    user_id = session['user_id']
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)
    document_file.save(save_path)

    # Extract text and calculate originality
    new_text = extract_text_from_file(save_path)
    previous_docs = Document.query.filter(Document.user_id==user_id, Document.id != None).all()
    previous_texts = [extract_text_from_file(doc.file_path) for doc in previous_docs if doc.file_path and os.path.exists(doc.file_path)]
    originality_score = calculate_originality(new_text, previous_texts)

    # Save to DB
    new_document = Document(
        user_id=user_id,
        document_name=document_name,
        file_path=filename,
        originality_score=originality_score
    )
    db.session.add(new_document)
    db.session.commit()

    flash(f'Document uploaded successfully! Originality score: {originality_score:.2%}', 'success')
    return redirect(url_for('home'))
