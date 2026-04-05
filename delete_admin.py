#!/usr/bin/env python
"""
Script to delete admin user
Usage: python delete_admin.py
"""

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Find admin user
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        # Also check by email if username not found
        if not admin:
            admin = User.query.filter_by(email='admin@campusmarket.com').first()
    
    if admin:
        print(f"⚠️ Found admin user:")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   ID: {admin.id}")
        print(f"   Is Admin: {admin.is_admin}")
        
        # Confirm before deleting
        confirm = input("\n⚠️ Are you sure you want to delete this admin user? (yes/no): ")
        
        if confirm.lower() == 'yes':
            db.session.delete(admin)
            db.session.commit()
            print(f"\n✅ Admin user '{admin.username}' has been deleted successfully!")
        else:
            print("\n❌ Deletion cancelled.")
    else:
        print("❌ No admin user found with username 'admin' or email 'admin@campusmarket.com'")