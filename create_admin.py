from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@campusmarket.com',
            is_admin=True
        )
        admin.set_password('admin123')  # Change this password!
        
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin user created successfully!')
        print('Username: admin')
        print('Password: admin123')
    else:
        print('⚠️ Admin user already exists')