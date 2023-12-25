from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)
    is_admin = db.Column(db.Integer, default=0)
    def is_administrator(self):
        return self.is_admin

    def is_authenticated(self):
        # Logika untuk menentukan apakah pengguna diautentikasi
        return True if self.id is not None else False

    def is_active(self):
        # Logika untuk menentukan apakah pengguna aktif
        return True  # Anda dapat menambahkan logika tambahan jika diperlukan

    def is_anonymous(self):
        # Logika untuk menentukan apakah pengguna anonim
        return False  # Karena kita menggunakan otentikasi, pengguna tidak anonim

    def get_id(self):
        return str(self.id)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime, default=datetime.utcnow)
    priority = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_completed = db.Column(db.Integer, default=0)
