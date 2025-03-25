from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import os

# Create a minimal Flask app
app = Flask(__name__)
# Ensure the instance folder exists
os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bus_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

# Create admin user
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
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        # Verify creation
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
            print("Role: admin")
        else:
            print("Failed to create admin user!")
