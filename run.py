# run.py
from app import create_app, db
import os

app = create_app()
print("=" * 60)
print("DEBUG: Checking Google OAuth Configuration")
print("=" * 60)
print(f"GOOGLE_CLIENT_ID: {app.config.get('GOOGLE_CLIENT_ID')}")
print(f"GOOGLE_CLIENT_SECRET: {app.config.get('GOOGLE_CLIENT_SECRET')[:10]}..." if app.config.get('GOOGLE_CLIENT_SECRET') else "GOOGLE_CLIENT_SECRET: None")
print(f"GOOGLE_REDIRECT_URI: {app.config.get('GOOGLE_REDIRECT_URI')}")
print("=" * 60)

if not app.config.get('GOOGLE_CLIENT_ID'):
    print("❌ ERROR: GOOGLE_CLIENT_ID is not set!")
    print("Check your .env file and config.py")
    print("Current working directory:", os.getcwd())
    print("Is .env file present?", os.path.exists('.env'))

if __name__ == '__main__':
    with app.app_context():
        try:
            # Development warning
            print("=" * 60)
            print("CAMPUSMARKET DEVELOPMENT SERVER")
            print("=" * 60)
            
            # Check Google OAuth configuration
            if not app.config.get('GOOGLE_CLIENT_ID'):
                print("⚠️  WARNING: Google OAuth not configured!")
                print("   Make sure to set GOOGLE_CLIENT_ID in .env file")
            else:
                print("✅ Google OAuth configured")
            
            # Database setup
            #db.drop_all()  # Uncomment to reset database
            #db.create_all()  # Uncomment to create fresh tables
            
            # Add sample categories (only if they don't exist)
            from app.models import Category
            
            existing_categories = Category.query.all()
            if not existing_categories:
                categories = [
                    Category(name='Electronics', description='Phones, laptops, gadgets'),
                    Category(name='Furniture', description='Chairs, beds, tables'),
                    Category(name='Books', description='Textbooks, novels'),
                    Category(name='Other', description='Other items')
                ]
                
                for category in categories:
                    db.session.add(category)
                
                db.session.commit()
                print("✅ Sample categories added")
            else:
                print(f"✅ Found {len(existing_categories)} existing categories")
            
            print(f"\n🚀 Server running at: http://localhost:5000")
            print(f"📧 Auth login: http://localhost:5000/auth/login")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error during startup: {e}")
            db.session.rollback()
    
    # Run the app WITHOUT SSL
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000
        # REMOVED: ssl_context='adhoc'
    )