"""
Quick Fix Script - Add Missing Capacity Column
Run this ONCE to fix the database without losing data
File: quick_fix.py (save in project root)
"""

import sqlite3
import os

# Path to database
DB_PATH = "instance/app.db"

def fix_database():
    """Add missing capacity column to rooms table"""
    
    if not os.path.exists(DB_PATH):
        print("❌ Database not found at:", DB_PATH)
        return
    
    print("🔧 Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if capacity column exists
        cursor.execute("PRAGMA table_info(rooms)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "capacity" in columns:
            print("✅ Capacity column already exists!")
        else:
            print("📝 Adding capacity column to rooms table...")
            cursor.execute("ALTER TABLE rooms ADD COLUMN capacity INTEGER")
            conn.commit()
            print("✅ Capacity column added successfully!")
        
        # Verify IssueComment table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='issue_comments'
        """)
        
        if cursor.fetchone():
            print("✅ issue_comments table exists!")
        else:
            print("❌ issue_comments table missing!")
            print("   Run: flask db upgrade")
        
        print("\n🎉 Database fix complete!")
        print("📌 Next step: Run 'python run.py' to start the app")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()