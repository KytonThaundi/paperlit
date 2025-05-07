from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file, current_app
from src.models import db, User, Document
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os
import time
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

    edit_mode = request.args.get('edit', None)
    editing_document_id = session.get('editing_document_id', None)
    editing_document_name = session.get('editing_document_name', None)

    user_id = session['user_id']
    user = User.query.get(user_id)
    documents = Document.query.filter_by(user_id=user_id).order_by(Document.uploaded_at.desc()).all()

    return render_template('home.html',
                          username=session['user'],
                          user=user,
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


def get_document_file_path(document):
    stored_path = document.file_path

    if 'src/src' in stored_path:
        stored_path = stored_path.replace('src/src', 'src')

    filename_only = os.path.basename(stored_path)

    possible_paths = [
        stored_path,
        os.path.join(project_root, 'uploads', filename_only),
        os.path.join(project_root, 'src', 'uploads', filename_only),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    for root, _, files in os.walk(project_root):
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

    user_id = session['user_id']
    user = User.query.get(user_id)

    document = Document.query.get_or_404(document_id)
    if document.user_id != user_id:
        flash('Document not found or access denied.', 'danger')
        return redirect(url_for('home'))

    file_path = get_document_file_path(document)

    if not file_path:
        flash("File not found on server.", "danger")
        return redirect(url_for('home'))

    from src.utils.file_extract import extract_text_from_file
    document_text = extract_text_from_file(file_path)

    similarity_details = document.get_similarity_details()

    ext = os.path.splitext(file_path)[1].lower()

    return render_template(
        'view_document.html',
        user=user,
        document=document,
        document_text=document_text,
        similarity_details=similarity_details,
        file_extension=ext,
        file_path=file_path
    )

@app.route('/serve_document/<int:document_id>')
def serve_document(document_id):
    if 'user' not in session:
        return "Unauthorized", 401

    document = Document.query.get_or_404(document_id)
    if document.user_id != session['user_id']:
        return "Access denied", 403

    file_path = get_document_file_path(document)

    if not file_path:
        return "File not found", 404

    ext = os.path.splitext(file_path)[1].lower()
    mime_type = 'application/pdf' if ext == '.pdf' else 'text/plain'

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
        file_path = get_document_file_path(document)

        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")

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

    session['editing_document_id'] = document_id
    session['editing_document_name'] = document.document_name

    return redirect(url_for('home', edit=document_id))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('logout'))

    if request.method == 'POST':
        new_username = request.form.get('username')
        if new_username != user.username:
            if User.query.filter(User.username == new_username, User.id != user.id).first():
                flash('Username already taken.', 'danger')
                return render_template('edit_profile.html', user=user)
            user.username = new_username
            session['user'] = new_username

        new_email = request.form.get('email')
        if new_email != user.email:
            if User.query.filter(User.email == new_email, User.id != user.id).first():
                flash('Email already taken.', 'danger')
                return render_template('edit_profile.html', user=user)
            user.email = new_email

        user.full_name = request.form.get('full_name')
        user.bio = request.form.get('bio')
        user.institution = request.form.get('institution')

        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            file_ext = avatar_file.filename.rsplit('.', 1)[1].lower() if '.' in avatar_file.filename else ''

            if file_ext not in allowed_extensions:
                flash('Invalid file type. Please upload a PNG, JPG, or GIF image.', 'danger')
                return render_template('edit_profile.html', user=user)

            base_filename = f"avatar_{user.id}_{int(time.time())}"
            avatar_filename = secure_filename(f"{base_filename}.{file_ext}")
            avatar_path = os.path.join('uploads/avatars', avatar_filename)
            full_path = os.path.join(app.static_folder, avatar_path)

            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            avatar_file.save(full_path)

            user.avatar_path = avatar_path

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        if current_password and new_password:
            if check_password_hash(user.password, current_password):
                user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                flash('Password updated successfully.', 'success')
            else:
                flash('Current password is incorrect.', 'danger')
                return render_template('edit_profile.html', user=user)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('edit_profile.html', user=user)

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
