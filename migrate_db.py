#!/usr/bin/env python3
"""
Database Migration Script
Handles schema migration for the User table when switching to proper authentication
"""

import os
import sqlite3
import logging
from app import app, db
from models import User

def migrate_database():
    """Migrate the database schema to support new authentication system"""
    
    # Database file path
    db_file = 'app.db'
    instance_db = os.path.join('instance', 'app.db')
    
    # Remove old database files if they exist
    for db_path in [db_file, instance_db]:
        if os.path.exists(db_path):
            print(f"Removing old database: {db_path}")
            os.remove(db_path)
    
    # Remove instance directory if it exists
    if os.path.exists('instance'):
        import shutil
        shutil.rmtree('instance')
        print("Removed instance directory")
    
    print("Creating fresh database with new schema...")
    
    # Create all tables with new schema
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
        
        # Create default admin user
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
            print("✓ Default admin user created: admin@gmail.com / admin")
        else:
            print("✓ Default admin user already exists")
    
    print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database()