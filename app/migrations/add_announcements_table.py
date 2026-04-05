#!/usr/bin/env python3
"""
Migration script to add announcements and reactions tables
Run this script to create the new tables in your database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import db, create_app
from app.models import Announcement, Reaction
from sqlalchemy import inspect

def run_migration():
    """Run the migration to create announcements and reactions tables"""
    
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print("📋 Checking existing tables...")
        print(f"Existing tables: {', '.join(existing_tables)}")
        
        # Create tables if they don't exist
        if 'announcements' not in existing_tables:
            print("➕ Creating announcements table...")
            Announcement.__table__.create(db.engine)
            print("✅ announcements table created")
        else:
            print("⚠️  announcements table already exists")
        
        if 'reactions' not in existing_tables:
            print("➕ Creating reactions table...")
            Reaction.__table__.create(db.engine)
            print("✅ reactions table created")
        else:
            print("⚠️  reactions table already exists")
        
        print("\n🎉 Migration completed successfully!")

if __name__ == '__main__':
    run_migration()