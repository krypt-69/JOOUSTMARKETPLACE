from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

admin_auth_bp = Blueprint('admin_auth', __name__)

@admin_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.is_admin and user.check_password(password):
            login_user(user)
            flash('Admin login successful!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid credentials or insufficient permissions.', 'error')
    
    return render_template('admin/auth/login.html')

@admin_auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('admin_auth.login'))