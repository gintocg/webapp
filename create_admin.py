from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import os
import time

# Create a minimal Flask app
app = Flask(__name__)
# Ensure the instance folder exists
os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Please configure it in Render.")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

def create_admin_user(username, password):
    # Hash the password for security
    hashed_password = generate_password_hash(password)
    # Create a new admin user
    admin_user = User(username=username, password=hashed_password, role='admin')
    db.session.add(admin_user)
    db.session.commit()
    print(f"Admin user '{username}' created successfully.")

if __name__ == "__main__":
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print(f"Admin user already exists: {admin.username}, role: {admin.role}")
            print("To recreate the admin user, delete the existing one first.")
        else:
            # Create new admin user
            create_admin_user("admin", "admin123")
