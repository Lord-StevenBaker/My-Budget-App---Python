"""
Update Income model schema to match our test requirements
"""
import sqlite3
import os

def main():
    """Update the income schema to make source nullable and description non-nullable"""
    db_path = 'budget.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    print(f"Updating income schema in {db_path}...")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("PRAGMA foreign_keys=off")
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Create backup of incomes table
            cursor.execute("""
            CREATE TABLE incomes_backup (
                id INTEGER PRIMARY KEY,
                amount FLOAT NOT NULL,
                description VARCHAR(200) NOT NULL,
                date DATE,
                source VARCHAR(100),
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """)
            
            # Copy data to backup, using source as description if description is NULL
            cursor.execute("""
            INSERT INTO incomes_backup (id, amount, description, date, source, user_id)
            SELECT id, amount, 
                   CASE WHEN description IS NULL THEN source ELSE description END,
                   date, source, user_id 
            FROM incomes
            """)
            
            # Drop original table
            cursor.execute("DROP TABLE incomes")
            
            # Create new incomes table with modified schema
            cursor.execute("""
            CREATE TABLE incomes (
                id INTEGER PRIMARY KEY,
                amount FLOAT NOT NULL,
                description VARCHAR(200) NOT NULL,
                date DATE,
                source VARCHAR(100),
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """)
            
            # Copy data back from backup
            cursor.execute("""
            INSERT INTO incomes (id, amount, description, date, source, user_id)
            SELECT id, amount, description, date, source, user_id FROM incomes_backup
            """)
            
            # Drop backup table
            cursor.execute("DROP TABLE incomes_backup")
            
            # Commit transaction
            conn.commit()
            cursor.execute("PRAGMA foreign_keys=on")
            print("Income schema updated successfully!")
            
        except Exception as e:
            # Rollback transaction on error
            conn.rollback()
            cursor.execute("PRAGMA foreign_keys=on")
            print(f"Error updating income schema: {str(e)}")
            
    finally:
        # Close connection
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
