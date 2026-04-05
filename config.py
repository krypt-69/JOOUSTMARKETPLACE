# config.py (in project root)
import os
from pathlib import Path

# Load .env file manually to ensure it's loaded
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    print(f"✅ Loading .env from: {env_path}")
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
else:
    print(f"⚠️  .env file not found at: {env_path}")

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///marketplace.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads', 'product_images')
    CHAT_UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads', 'chat_images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # M-Pesa Configuration
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '4wG4bdDlPrrhXJD6LO2x7BnnAgJy5ITHgFdo3i9XDtorCFoq')
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', 'Z0B4Urr3fC6iZXBsNkQN6vIrmWDV6OfnvGJrS6V2xC2n9V3117PZZFn47XdYPWGK')
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '174379')
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
    MPESA_BASE_URL = os.environ.get('MPESA_BASE_URL', 'https://sandbox.safaricom.co.ke')
    # Change from M-Pesa Daraja config:
    # To Megapay config:
    MEGAPAY_API_KEY = "MGPY1EvRts3I"
    MEGAPAY_BUSINESS_CODE = "your_business_code"
    MEGAPAY_BASE_URL = "https://api.sandbox.megapay.com"  # or production URL
        
    # App Configuration
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    LISTING_FEE = int(os.environ.get('LISTING_FEE', '1'))
    UNLOCK_FEE = int(os.environ.get('UNLOCK_FEE', '1'))  # Default unlock fee
    
    # Chat Configuration
    CHAT_POLLING_INTERVAL = 3000  # 3 seconds for AJAX polling
    MAX_MESSAGE_LENGTH = 1000  # Maximum characters per message