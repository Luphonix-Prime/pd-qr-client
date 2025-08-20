"""
Full Authentication Module with Login/Signup
Provides complete authentication functionality using Flask-Login
"""
import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    try:
        # Handle both old string IDs and new integer IDs
        if user_id and user_id.isdigit():
            return User.query.get(int(user_id))
        else:
            # Clear invalid session data from old system
            return None
    except (ValueError, TypeError):
        return None

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    admin = User.query.filter_by(email='admin@gmail.com').first()
    if not admin:
        admin = User(
            email='admin@gmail.com',
            first_name='System',
            last_name='Administrator',
            role='admin'
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: admin@gmail.com / admin")

def make_replit_blueprint():
    """Create authentication blueprint with login/signup functionality"""
    auth_bp = Blueprint('auth', __name__)
    
    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember = bool(request.form.get('remember'))
            
            if not email or not password:
                flash('Please enter both email and password', 'error')
                return render_template('auth/login.html')
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                if user.is_active:
                    login_user(user, remember=remember)
                    flash(f'Welcome back, {user.full_name}!', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('dashboard'))
                else:
                    flash('Your account has been deactivated. Please contact support.', 'error')
            else:
                flash('Invalid email or password', 'error')
        
        return render_template('auth/login.html')
    
    @auth_bp.route('/signup', methods=['GET', 'POST'])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            
            # Validation
            if not all([email, password, first_name]):
                flash('Please fill in all required fields', 'error')
                return render_template('auth/signup.html')
            
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('auth/signup.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('auth/signup.html')
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                flash('An account with this email already exists', 'error')
                return render_template('auth/signup.html')
            
            # Create new user
            try:
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='user'  # Regular users get 'user' role by default
                )
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()
                
                login_user(user)
                flash(f'Account created successfully! Welcome, {user.full_name}!', 'success')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                db.session.rollback()
                flash('Error creating account. Please try again.', 'error')
                print(f"Signup error: {e}")
        
        return render_template('auth/signup.html')
    
    @auth_bp.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out', 'info')
        return redirect(url_for('index'))
    
    return auth_bp

def require_login(f):
    """Custom login decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Alternative to login_required for consistency
def login_required_replit(f):
    """Alias for require_login for backward compatibility"""
    return require_login(f)