"""
Authentication routes and utilities.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from app.models import User, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True
            user.last_login = db.func.now()
            db.session.commit()
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard.index'))
        
        flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Logout route."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    user = User.query.get(session.get('user_id'))
    return render_template('auth/profile.html', user=user)
