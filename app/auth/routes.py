from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app import db
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests
import os
import pathlib

auth_bp = Blueprint('auth', __name__)

# Google OAuth Configuration
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Remove in production!

# Create client configuration from environment variables
def get_google_oauth_flow():
    client_config = {
        "web": {
            "client_id": current_app.config['GOOGLE_CLIENT_ID'],
            "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [current_app.config['GOOGLE_REDIRECT_URI']],
            "issuer": "https://accounts.google.com",
            "userinfo_uri": "https://openidconnect.googleapis.com/v1/userinfo",
            "scope": "openid email profile"
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_uri=current_app.config['GOOGLE_REDIRECT_URI']
    )
    return flow

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        
        # Check if user exists
        user = User.query.filter((User.email == email) | (User.username == username)).first()
        if user:
            flash('Email or username already exists!', 'error')
            return redirect(url_for('auth.register'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone
        )
        print(f'this is the email{email},{username}')
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Change from 'email' to 'login' to accept both email and username
        login_input = request.form.get('login')  # This will accept email OR username
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        if not login_input or not password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if the input contains @ to determine if it's email or username
        if '@' in login_input:
            # It's an email
            user = User.query.filter_by(email=login_input).first()
        else:
            # It's a username
            user = User.query.filter_by(username=login_input).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to admin dashboard if admin, otherwise to main page
            if hasattr(user, 'is_admin') and user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.index'))
        else:
            flash('Invalid login credentials!', 'error')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html')

@auth_bp.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    try:
        flow = get_google_oauth_flow()
        
        # Generate URL for request to Google's OAuth 2.0 server
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account'
        )
        
        # Store the state in the session for validation
        session['state'] = state
        session['oauth_flow'] = flow.authorization_url()
        
        return redirect(authorization_url)
        
    except Exception as e:
        current_app.logger.error(f"Error initiating Google login: {str(e)}")
        flash('Failed to initiate Google login. Please try again.', 'error')
        return redirect(url_for('auth.login'))
@auth_bp.route('/callback', endpoint='google_callback_root')
@auth_bp.route('/auth/callback', endpoint='google_callback_auth')
def google_callback():
    """Google OAuth callback route"""
    try:
        # Verify state for security
        if 'state' not in session or session['state'] != request.args.get('state'):
            flash('Invalid authentication state. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Create flow instance
        flow = get_google_oauth_flow()
        flow.fetch_token(authorization_response=request.url)
        
        # Get credentials
        credentials = flow.credentials
        
        # Get user info from Google
        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v1/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        
        if userinfo_response.status_code != 200:
            flash('Failed to fetch user information from Google.', 'error')
            return redirect(url_for('auth.login'))
        
        user_info = userinfo_response.json()
        
        # Extract user data
        google_id = user_info['id']
        email = user_info['email']
        name = user_info.get('name', '').strip()
        profile_pic = user_info.get('picture', '')
        
        # Generate username from email if name is not available
        if not name:
            name = email.split('@')[0]
        
        # Check if user exists in database
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user from Google account
            # Generate a unique username
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            
            # Ensure username is unique
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create new user with Google data
            user = User(
                username=username,
                email=email,
                # Store Google ID for future reference
                google_id=google_id,
                profile_picture=profile_pic,
                # Generate a random password for Google users (they won't use it)
                password_hash=generate_password_hash(os.urandom(24).hex())
            )
            
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully with Google!', 'success')
        else:
            # Update existing user with Google ID if not already set
            if not user.google_id:
                user.google_id = google_id
                db.session.commit()
            
            flash('Logged in successfully with Google!', 'success')
        
        # Login the user
        login_user(user)
        
        # Clear the session state
        session.pop('state', None)
        
        return redirect(url_for('main.index'))
        
    except Exception as e:
        current_app.logger.error(f"Error in Google callback: {str(e)}")
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))