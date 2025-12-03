#!/usr/bin/env python3
"""
VulnerableShop Database Initialization Script
Initializes PostgreSQL database with schema and seed data
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from config import Config

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (default database)
        conn = psycopg2.connect(
            host=Config.DATABASE_HOST,
            port=Config.DATABASE_PORT,
            user=Config.DATABASE_USER,
            password=Config.DATABASE_PASSWORD,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{Config.DATABASE_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {Config.DATABASE_NAME}')
            print(f"✓ Database '{Config.DATABASE_NAME}' created successfully")
        else:
            print(f"✓ Database '{Config.DATABASE_NAME}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error creating database: {e}")
        return False

def initialize_schema():
    """Initialize database schema from schema.sql"""
    try:
        # Connect to the application database
        conn = psycopg2.connect(Config.DATABASE_URI)
        cursor = conn.cursor()
        
        # Read and execute schema.sql
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✓ Database schema initialized successfully")
        
        # Display some statistics
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM flags")
        flag_count = cursor.fetchone()[0]
        
        print(f"✓ Created {user_count} users")
        print(f"✓ Created {product_count} products")
        print(f"✓ Hidden {flag_count} CTF flags")
        
        cursor.close()
        conn.close()
        return True
        
    except FileNotFoundError:
        print("✗ Error: schema.sql file not found")
        return False
    except psycopg2.Error as e:
        print(f"✗ Error initializing schema: {e}")
        return False

def verify_setup():
    """Verify database setup"""
    try:
        conn = psycopg2.connect(Config.DATABASE_URI)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT username, email, is_admin FROM users WHERE is_admin = TRUE")
        admin_user = cursor.fetchone()
        
        if admin_user:
            print(f"\n✓ Setup verified! Admin user: {admin_user[0]} ({admin_user[1]})")
            print("\nDefault Credentials:")
            print("  Admin:    admin / admin")
            print("  User 1:   alice / password")
            print("  User 2:   bob / password")
            print("  User 3:   charlie / password")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error verifying setup: {e}")
        return False

def main():
    """Main initialization function"""
    print("=" * 60)
    print("VulnerableShop - Database Initialization")
    print("=" * 60)
    print()
    
    print(f"Database Configuration:")
    print(f"  Host: {Config.DATABASE_HOST}")
    print(f"  Port: {Config.DATABASE_PORT}")
    print(f"  Database: {Config.DATABASE_NAME}")
    print(f"  User: {Config.DATABASE_USER}")
    print()
    
    # Step 1: Create database
    print("[Step 1/3] Creating database...")
    if not create_database():
        print("\n✗ Failed to create database. Please check your PostgreSQL configuration.")
        sys.exit(1)
    
    # Step 2: Initialize schema
    print("\n[Step 2/3] Initializing schema and seed data...")
    if not initialize_schema():
        print("\n✗ Failed to initialize schema.")
        sys.exit(1)
    
    # Step 3: Verify setup
    print("\n[Step 3/3] Verifying setup...")
    if not verify_setup():
        print("\n✗ Failed to verify setup.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Database initialization complete!")
    print("=" * 60)
    print("\nYou can now start the application with:")
    print("  python app.py")
    print()
    print("⚠️  WARNING: This is a DELIBERATELY VULNERABLE application")
    print("    for educational purposes only. DO NOT expose to the internet!")
    print()

if __name__ == '__main__':
    main()
