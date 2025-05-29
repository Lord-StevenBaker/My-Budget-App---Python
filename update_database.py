from sqlalchemy import create_engine, text
import os

def upgrade_database():
    """Add the new APR columns to the expenses table"""
    
    print("Updating database schema...")
    
    # Check if database exists
    if not os.path.exists('budget.db'):
        print("Database file not found. Please run the main application first to initialize the database.")
        return False
    
    # Connect to the database
    engine = create_engine('sqlite:///budget.db')
    conn = engine.connect()
    
    try:
        # Check if columns already exist to avoid errors
        result = conn.execute(text("PRAGMA table_info(expenses)"))
        columns = [row[1] for row in result]
        
        # Add has_apr column if it doesn't exist
        if 'has_apr' not in columns:
            print("Adding 'has_apr' column...")
            conn.execute(text("ALTER TABLE expenses ADD COLUMN has_apr INTEGER DEFAULT 0"))
        else:
            print("Column 'has_apr' already exists.")
        
        # Add apr column if it doesn't exist
        if 'apr' not in columns:
            print("Adding 'apr' column...")
            conn.execute(text("ALTER TABLE expenses ADD COLUMN apr FLOAT DEFAULT 0.0"))
        else:
            print("Column 'apr' already exists.")
            
        print("Database schema updated successfully!")
        return True
        
    except Exception as e:
        print(f"Error updating database schema: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade_database()
