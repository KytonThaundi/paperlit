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

    user_id = session['user_id']
    documents = Document.query.filter_by(user_id=user_id).all()

    return render_template('home.html', username=session['user'], documents=documents)


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

@app.route('/download_document/<int:document_id>')
def download_document(document_id):
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login_register'))

    document = Document.query.get_or_404(document_id)
    if document.user_id != session['user_id']:
        flash('Document not found or access denied.', 'danger')
        return redirect(url_for('home'))


    stored_path = document.file_path


    filename_only = os.path.basename(stored_path)


    print(f"Document ID: {document_id}, Stored path: {stored_path}, Filename: {filename_only}")


    possible_paths = [
        os.path.join(project_root, 'uploads', filename_only),
        os.path.join(project_root, 'src', 'uploads', filename_only),
    ]


    if os.path.isabs(stored_path):
        possible_paths.insert(0, stored_path)
        if 'src/src' in stored_path:
            possible_paths.insert(0, stored_path.replace('src/src', 'src'))


    print(f"Trying paths: {possible_paths}")


    for path in possible_paths:
        print(f"Checking path: {path}")
        if os.path.exists(path):
            print(f"File found at: {path}")
            return send_file(path, as_attachment=True)
        else:
            print(f"File not found at: {path}")

    for root, dirs, files in os.walk(project_root):
        if filename_only in files:
            file_path = os.path.join(root, filename_only)
            print(f"Found file via walk at: {file_path}")
            return send_file(file_path, as_attachment=True)


    flash("File not found on server.", "danger")

    current_app.logger.error(f"File not found at any expected path. Original stored path was: {stored_path}")
    current_app.logger.error(f"Tried paths: {possible_paths}")
    return redirect(url_for('home'))

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
