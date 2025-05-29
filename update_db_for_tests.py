"""
Database schema update script for Test-Driven Development
This script adds new columns required for our tests to the database schema
"""
import os
import sqlite3
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import models
import hashlib

def main():
    """Update the database schema and provide initial test data"""
    print("Updating database schema for testing...")
    
    db_path = 'budget.db'
    
    # Create a direct sqlite3 connection to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Try to add the new columns required for our tests
    try:
        # Check if username column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'username' not in columns:
            # Add username column
            cursor.execute("ALTER TABLE users ADD COLUMN username VARCHAR(50)")
            cursor.execute("UPDATE users SET username = name WHERE username IS NULL")
            print("Added username column to users table.")
        else:
            print("Username column already exists.")
        
        if 'password' not in columns:
            # Add password column with default hash
            default_hash = hashlib.sha256("default_password".encode()).hexdigest()
            cursor.execute(f"ALTER TABLE users ADD COLUMN password VARCHAR(256) DEFAULT '{default_hash}'")
            print("Added password column to users table.")
        else:
            print("Password column already exists.")
        
        # Check expense table columns
        cursor.execute("PRAGMA table_info(expenses)")
        expense_columns = [column[1] for column in cursor.fetchall()]
        
        if 'has_apr' not in expense_columns:
            # Add has_apr column with default value
            cursor.execute("ALTER TABLE expenses ADD COLUMN has_apr INTEGER DEFAULT 0")
            print("Added has_apr column to expenses table.")
        else:
            print("has_apr column already exists.")
            
        if 'apr' not in expense_columns:
            # Add apr column with default value
            cursor.execute("ALTER TABLE expenses ADD COLUMN apr FLOAT DEFAULT 0.0")
            print("Added apr column to expenses table.")
        else:
            print("apr column already exists.")
        
        # Make email and name columns nullable for testing
        try:
            cursor.execute("PRAGMA foreign_keys=off")
            cursor.execute("BEGIN TRANSACTION")
            
            # Create backup of users table
            cursor.execute("""
            CREATE TABLE users_backup (
                id INTEGER PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                password VARCHAR(256) NOT NULL,
                name VARCHAR(50),
                email VARCHAR(100) UNIQUE
            )
            """)
            
            # Copy data to backup table
            cursor.execute("""
            INSERT INTO users_backup (id, username, password, name, email)
            SELECT id, username, password, name, email FROM users
            """)
            
            # Drop original table
            cursor.execute("DROP TABLE users")
            
            # Create new users table with modified constraints
            cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                password VARCHAR(256) NOT NULL,
                name VARCHAR(50),
                email VARCHAR(100) UNIQUE
            )
            """)
            
            # Copy data back from backup
            cursor.execute("""
            INSERT INTO users (id, username, password, name, email)
            SELECT id, username, password, name, email FROM users_backup
            """)
            
            # Drop backup table
            cursor.execute("DROP TABLE users_backup")
            
            conn.commit()
            cursor.execute("PRAGMA foreign_keys=on")
            print("Updated nullability constraints for users table.")
        except Exception as e:
            conn.rollback()
            cursor.execute("PRAGMA foreign_keys=on")
            print(f"Error updating constraints: {str(e)}")
        
        print("Database schema updated successfully.")
    except Exception as e:
        print(f"Error updating database schema: {str(e)}")
    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    main()
