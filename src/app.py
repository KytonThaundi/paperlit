from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file, current_app
from src.models import db, User, Document
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- Best Practice: Load secrets from .env ---
load_dotenv()

# --- Best Practice: Register blueprints and keep app.py minimal ---
from src.blueprints.plagiarism import plagiarism_bp

# Initialize Flask app
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'changeme')

# PostgreSQL database configuration
# Ensure the password is URL-encoded if it contains special characters like '#'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload folder configuration
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', os.path.join(project_root, 'uploads'))

# Initialize SQLAlchemy
# (db is now imported from src.models)
db.init_app(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Models are now defined in src/models.py

# Home Route (Requires Login)
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login_register'))

    user_id = session['user_id']
    documents = Document.query.filter_by(user_id=user_id).all()
    # Show originality scores if available, otherwise None
    return render_template('home.html', username=session['user'], documents=documents)

# Combined Login and Registration Route
@app.route('/', methods=['GET', 'POST'])
def login_register():
    try:
        if request.method == 'POST':
            if 'login' in request.form:
                # Handle login
                username = request.form['username']
                password = request.form['password']
                user = User.query.filter_by(username=username).first()

                if user and check_password_hash(user.password, password):
                    session['user'] = username
                    session['user_id'] = user.id  # Store user_id in session
                    flash('Login successful!', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('Invalid credentials. Please try again.', 'danger')

            elif 'register' in request.form:
                # Handle registration
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

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)  # Remove user_id from session
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login_register'))

# --- The /upload_document route is now handled by the plagiarism blueprint. ---
# Legacy upload_document route removed. See src/blueprints/plagiarism.py for new implementation.

# Download Document Route
@app.route('/download_document/<int:document_id>')
def download_document(document_id):
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    document = Document.query.get_or_404(document_id)
    if document.user_id != session['user_id']:
        flash('Document not found or access denied.', 'danger')
        return redirect(url_for('home'))

    # Get the path stored in the database
    stored_path = document.file_path
    # Extract *only* the filename part, regardless of whether stored_path is absolute or relative
    filename_only = os.path.basename(stored_path)

    # Get the correctly configured upload folder
    upload_folder = current_app.config['UPLOAD_FOLDER']
    # Construct the full path using the correct folder and the extracted filename
    full_file_path = os.path.join(upload_folder, filename_only)

    if not os.path.exists(full_file_path):
        flash("File not found on server.", "danger")
        # Log the problematic path and the original stored path for debugging
        current_app.logger.error(f"File not found at expected path: {full_file_path}. Original stored path was: {stored_path}")
        return redirect(url_for('home'))
    
    # Use the reconstructed full path
    return send_file(full_file_path, as_attachment=True)

# Edit Profile Route
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    if request.method == 'POST':
        # Handle profile update logic here
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('edit_profile.html')

# Error handling
@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Server Error: {error}")
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    logging.error(f"Page Not Found: {error}")
    return render_template('404.html'), 404

# Register blueprints
app.register_blueprint(plagiarism_bp)

# --- Create tables if they do not exist (development only) ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
