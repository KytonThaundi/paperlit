
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    full_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_path = db.Column(db.String(255), nullable=True, default='images/avatar-placeholder.png')
    institution = db.Column(db.String(100), nullable=True)

    documents = db.relationship('Document', backref='user', lazy=True)

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    originality_score = db.Column(db.Float, nullable=True)
    similarity_details = db.Column(db.Text, nullable=True)

    def set_similarity_details(self, details):
        if details:
            self.similarity_details = json.dumps(details)
        else:
            self.similarity_details = None

    def get_similarity_details(self):
        if self.similarity_details:
            try:
                return json.loads(self.similarity_details)
            except json.JSONDecodeError:
                return {}
        return {}
