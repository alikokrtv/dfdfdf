#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from sqlalchemy import create_engine, text

def test_database_connection():
    """Test database connection with password fallback logic"""
    
    # Database configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')  # Use localhost or set DB_HOST env var
    DB_NAME = os.environ.get('DB_NAME', 'dof_db')
    DB_USER = 'root'
    
    # Password priority: try 255223Rtv first, then 255223
    passwords_to_try = ['255223Rtv', '255223']
    
    print(f"Testing database connection to {DB_HOST}...")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    
    for password in passwords_to_try:
        try:
            connection_string = f"mysql+pymysql://{DB_USER}:{password}@{DB_HOST}/{DB_NAME}"
            print(f"\nTrying password: {password}")
            print(f"Connection string: mysql+pymysql://{DB_USER}:***@{DB_HOST}/{DB_NAME}")
            
            engine = create_engine(connection_string, connect_args={"connect_timeout": 10})
            
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                
                if test_value == 1:
                    print(f"✅ SUCCESS: Database connection successful with password: {password}")
                    print(f"✅ Working connection string: {connection_string}")
                    return connection_string
                    
        except Exception as e:
            print(f"❌ FAILED with password {password}: {str(e)}")
            continue
    
    print("\n❌ All database connection attempts failed!")
    return None

if __name__ == "__main__":
    working_connection = test_database_connection()
    if working_connection:
        print(f"\n🎯 Use this connection string in your config:")
        print(f"SQLALCHEMY_DATABASE_URI = '{working_connection}'")
    else:
        print("\n💡 Suggestions:")
        print("1. Check if MySQL server is running")
        print("2. Verify database name exists")
        print("3. Check if passwords are correct")
        print("4. Set DB_HOST environment variable if database is on remote server")
