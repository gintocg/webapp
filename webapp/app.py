from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Ensure the instance folder exists
os.makedirs(os.path.join(app.instance_path), exist_ok=True)

# Use PostgreSQL from environment or fallback to SQLite locally
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bus_tracker.db")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'parent', 'volunteer', 'admin'
    
class BusLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'))
    
class Bus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    route = db.Column(db.String(100), nullable=False)
    locations = db.relationship('BusLocation', backref='bus', lazy=True)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role=role)
        
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    buses = Bus.query.all()
    
    return render_template('dashboard.html', user=user, buses=buses)

@app.route('/update_location', methods=['POST'])
def update_location():
    if 'user_id' not in session or session['role'] != 'volunteer':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    bus_id = data.get('bus_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    new_location = BusLocation(
        latitude=latitude,
        longitude=longitude,
        bus_id=bus_id
    )
    
    db.session.add(new_location)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    buses = Bus.query.all()
    
    # Get statistics for admin dashboard
    stats = {
        'total_buses': Bus.query.count(),
        'total_users': User.query.count(),
        'students': User.query.filter_by(role='student').count(),
        'parents': User.query.filter_by(role='parent').count(),
        'volunteers': User.query.filter_by(role='volunteer').count(),
        'total_locations': BusLocation.query.count()
    }
    
    return render_template('admin_dashboard.html', buses=buses, stats=stats)

# Removed admin_users route as it's not needed and causing BuildError

@app.route('/admin/add_bus', methods=['GET', 'POST'])
def add_bus():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        route = request.form.get('route')
        
        if name and route:
            new_bus = Bus(name=name, route=route)
            db.session.add(new_bus)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        
    return render_template('add_bus.html')

@app.route('/admin/delete_bus/<int:bus_id>', methods=['POST'])
def delete_bus(bus_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    bus = Bus.query.get_or_404(bus_id)
    
    # Delete associated locations first
    BusLocation.query.filter_by(bus_id=bus_id).delete()
    
    # Then delete the bus
    db.session.delete(bus)
    db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_bus/<int:bus_id>', methods=['GET', 'POST'])
def edit_bus(bus_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    bus = Bus.query.get_or_404(bus_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        route = request.form.get('route')
        
        if name and route:
            bus.name = name
            bus.route = route
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_bus.html', bus=bus)

@app.route('/admin/bus_locations/<int:bus_id>')
def bus_locations(bus_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    bus = Bus.query.get_or_404(bus_id)
    locations = BusLocation.query.filter_by(bus_id=bus_id).order_by(BusLocation.timestamp.desc()).all()
    
    # Get statistics for admin dashboard
    stats = {
        'total_buses': Bus.query.count(),
        'total_users': User.query.count(),
        'students': User.query.filter_by(role='student').count(),
        'parents': User.query.filter_by(role='parent').count(),
        'volunteers': User.query.filter_by(role='volunteer').count(),
        'total_locations': BusLocation.query.count()
    }
    
    # Create a simple bus locations view instead of reusing admin_dashboard
    return render_template('admin_dashboard.html', buses=Bus.query.all(), stats=stats, 
                          selected_bus=bus, locations=locations)

@app.route('/get_location/<int:bus_id>')
def get_location(bus_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    location = BusLocation.query.filter_by(bus_id=bus_id).order_by(BusLocation.timestamp.desc()).first()
    
    if location:
        return jsonify({
            'latitude': location.latitude,
            'longitude': location.longitude,
            'timestamp': location.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({'error': 'No location data available'}), 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    from waitress import serve
    with app.app_context():
        db.create_all()
    serve(app, host="0.0.0.0", port=5000)
