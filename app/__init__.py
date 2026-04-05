from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from flask_caching import Cache 

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
cache = Cache()

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Load configuration from Config class
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app, config={
        "CACHE_TYPE": "simple",
        "CACHE_DEFAULT_TIMEOUT": 300
    })
    
    # Debug: Print loaded config
    print("\n" + "="*60)
    print("FLASK APP CONFIGURATION LOADED")
    print("="*60)
    print(f"SECRET_KEY: {'Set' if app.config.get('SECRET_KEY') else 'Not Set'}")
    print(f"GOOGLE_CLIENT_ID: {app.config.get('GOOGLE_CLIENT_ID')}")
    print(f"GOOGLE_REDIRECT_URI: {app.config.get('GOOGLE_REDIRECT_URI')}")
    print(f"MPESA_SHORTCODE: {app.config.get('MPESA_SHORTCODE')}")
    print("="*60 + "\n")

    
    # Import and register blueprints
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.products.routes import products_bp
    from app.admin.routes import admin_bp
    from app.admin.auth import admin_auth_bp 
    from app.admin.dashboard import dashboard_bp 
    from app.chat import chat_bp
    from app.rooms.routes import rooms_bp  # Import rooms blueprint
    from app.announcements import announcements_bp
    app.register_blueprint(announcements_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_auth_bp, url_prefix='/adminauth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(chat_bp)
    app.register_blueprint(rooms_bp)  # Register rooms blueprint
    
    # ========== ADD THIS CONTEXT PROCESSOR ==========
    @app.context_processor
    def inject_announcement_data():
        """Make announcement count available to all templates"""
        announcement_count = 0
        try:
            # Import here to avoid circular imports
            from app.models import Announcement
            announcement_count = Announcement.query.count()
        except Exception as e:
            # Table might not exist yet - silently fail
            pass
        
        return dict(
            announcement_count=announcement_count,
            # Add other global variables here if needed
        )
    # ========== END CONTEXT PROCESSOR ==========
    
    return app