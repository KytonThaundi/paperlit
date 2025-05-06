from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file, current_app
from src.models import db, User, Document
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv


load_dotenv()


from src.blueprints.plagiarism import plagiarism_bp


app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'changeme')


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', os.path.join(project_root, 'uploads'))


db.init_app(app)

logging.basicConfig(level=logging.DEBUG)

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login_register'))

    # Check if we're in edit mode
    edit_mode = request.args.get('edit', None)
    editing_document_id = session.get('editing_document_id', None)
    editing_document_name = session.get('editing_document_name', None)

    user_id = session['user_id']
    documents = Document.query.filter_by(user_id=user_id).order_by(Document.uploaded_at.desc()).all()

    return render_template('home.html',
                          username=session['user'],
                          documents=documents,
                          edit_mode=edit_mode,
                          editing_document_id=editing_document_id,
                          editing_document_name=editing_document_name)


@app.route('/', methods=['GET', 'POST'])
def login_register():
    try:
        if request.method == 'POST':
            if 'login' in request.form:

                username = request.form['username']
                password = request.form['password']
                user = User.query.filter_by(username=username).first()

                if user and check_password_hash(user.password, password):
                    session['user'] = username
                    session['user_id'] = user.id
                    flash('Login successful!', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('Invalid credentials. Please try again.', 'danger')

            elif 'register' in request.form:
                username = request.form['username']
                email = request.form['email']
                password = request.form['password']
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

                if User.query.filter_by(username=username).first():
                    flash('Username already exists. Please log in.', 'warning')
                    return redirect(url_for('login_register'))

                if User.query.filter_by(email=email).first():
                    flash('Email already exists. Please log in.', 'warning')
                    return redirect(url_for('login_register'))

                new_user = User(username=username, email=email, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login_register'))

        return render_template('login.html')
    except Exception as e:
        logging.error(f"Error during login or registration: {e}")
        return render_template('500.html'), 500

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login_register'))

# Helper function to find document file path
def get_document_file_path(document):
    """Find the actual file path for a document."""
    stored_path = document.file_path

    # Fix the duplicate src/src path issue by replacing it with src
    if 'src/src' in stored_path:
        stored_path = stored_path.replace('src/src', 'src')

    # Extract *only* the filename part, regardless of whether stored_path is absolute or relative
    filename_only = os.path.basename(stored_path)

    # Try multiple possible locations
    possible_paths = [
        stored_path,  # The path as stored in the database
        os.path.join(project_root, 'uploads', filename_only),  # Root uploads folder
        os.path.join(project_root, 'src', 'uploads', filename_only),  # src/uploads folder
    ]

    # Try each path
    for path in possible_paths:
        if os.path.exists(path):
            return path

    # If not found, try a more exhaustive search
    for root, dirs, files in os.walk(project_root):
        if filename_only in files:
            return os.path.join(root, filename_only)

    return None

@app.route('/download_document/<int:document_id>')
def download_document(document_id):
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    document = Document.query.get_or_404(document_id)
    if document.user_id != session['user_id']:
        flash('Document not found or access denied.', 'danger')
        return redirect(url_for('home'))

    file_path = get_document_file_path(document)

    if file_path:
        return send_file(file_path, as_attachment=True)

    flash("File not found on server.", "danger")
    current_app.logger.error(f"File not found for document ID: {document_id}, path: {document.file_path}")
    return redirect(url_for('home'))

@app.route('/view_document/<int:document_id>')
def view_document(document_id):
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    document = Document.query.get_or_404(document_id)
    if document.user_id != session['user_id']:
        flash('Document not found or access denied.', 'danger')
        return redirect(url_for('home'))

    # Get the document file path
    file_path = get_document_file_path(document)

    if not file_path:
        flash("File not found on server.", "danger")
        return redirect(url_for('home'))

    # Get document text
    from src.utils.file_extract import extract_text_from_file
    document_text = extract_text_from_file(file_path)

    # Get similarity details
    similarity_details = document.get_similarity_details()

    # Determine file type for appropriate viewer
    ext = os.path.splitext(file_path)[1].lower()

    return render_template(
        'view_document.html',
        document=document,
        document_text=document_text,
        similarity_details=similarity_details,
        file_extension=ext,
        file_path=file_path
    )

@app.route('/serve_document/<int:document_id>')
def serve_document(document_id):
    """Serve the document file for viewing (not downloading)."""
    if 'user' not in session:
        return "Unauthorized", 401

    document = Document.query.get_or_404(document_id)
    if document.user_id != session['user_id']:
        return "Access denied", 403

    # Get the document file path
    file_path = get_document_file_path(document)

    if not file_path:
        return "File not found", 404

    # Determine the MIME type based on file extension
    ext = os.path.splitext(file_path)[1].lower()
    mime_type = 'application/pdf' if ext == '.pdf' else 'text/plain'

    # Serve the file with the appropriate MIME type
    return send_file(file_path, mimetype=mime_type)

@app.route('/delete_document/<int:document_id>', methods=['POST'])
def delete_document(document_id):
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    document = Document.query.get_or_404(document_id)
    if document.user_id != session['user_id']:
        flash('Document not found or access denied.', 'danger')
        return redirect(url_for('home'))

    try:
        # Get the file path
        file_path = get_document_file_path(document)

        # Try to delete the file from the filesystem
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

        # Delete from database
        db.session.delete(document)
        db.session.commit()

        flash('Document deleted successfully.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error deleting document: {e}")
        flash('An error occurred while deleting the document.', 'danger')

    return redirect(url_for('home'))

@app.route('/edit_document/<int:document_id>', methods=['GET'])
def edit_document(document_id):
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    document = Document.query.get_or_404(document_id)
    if document.user_id != session['user_id']:
        flash('Document not found or access denied.', 'danger')
        return redirect(url_for('home'))

    # Store document ID in session for the upload form to use
    session['editing_document_id'] = document_id
    session['editing_document_name'] = document.document_name

    return redirect(url_for('home', edit=document_id))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    if request.method == 'POST':
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('edit_profile.html')

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Server Error: {error}")
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    logging.error(f"Page Not Found: {error}")
    return render_template('404.html'), 404

app.register_blueprint(plagiarism_bp)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
