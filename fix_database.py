"""
Complete Database Fix Script - Phase 5
Adds ALL missing columns without losing data
File: fix_database.py (save in project root)
"""

import sqlite3
import os

DB_PATH = "instance/app.db"

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    return column in columns

def fix_database():
    """Add all missing columns to database"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        print("   Make sure you're in the project root directory!")
        return False
    
    print("🔧 Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        changes_made = False
        
        # ═══════════════════════════════════════
        # FIX 1: Add missing columns to ROOMS
        # ═══════════════════════════════════════
        print("\n📋 Checking ROOMS table...")
        
        if not check_column_exists(cursor, "rooms", "capacity"):
            print("   ➕ Adding 'capacity' column...")
            cursor.execute("ALTER TABLE rooms ADD COLUMN capacity INTEGER")
            changes_made = True
            print("   ✅ Done!")
        else:
            print("   ✅ 'capacity' column already exists")
        
        # ═══════════════════════════════════════
        # FIX 2: Add missing columns to ISSUES
        # ═══════════════════════════════════════
        print("\n📋 Checking ISSUES table...")
        
        # Check and add assigned_to
        if not check_column_exists(cursor, "issues", "assigned_to"):
            print("   ➕ Adding 'assigned_to' column...")
            cursor.execute("ALTER TABLE issues ADD COLUMN assigned_to INTEGER")
            changes_made = True
            print("   ✅ Done!")
        else:
            print("   ✅ 'assigned_to' column already exists")
        
        # Check and add created_at
        if not check_column_exists(cursor, "issues", "created_at"):
            print("   ➕ Adding 'created_at' column...")
            cursor.execute("ALTER TABLE issues ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            changes_made = True
            print("   ✅ Done!")
        else:
            print("   ✅ 'created_at' column already exists")
        
        # Check and add resolved_at
        if not check_column_exists(cursor, "issues", "resolved_at"):
            print("   ➕ Adding 'resolved_at' column...")
            cursor.execute("ALTER TABLE issues ADD COLUMN resolved_at DATETIME")
            changes_made = True
            print("   ✅ Done!")
        else:
            print("   ✅ 'resolved_at' column already exists")
        
        # Check and add priority
        if not check_column_exists(cursor, "issues", "priority"):
            print("   ➕ Adding 'priority' column...")
            cursor.execute("ALTER TABLE issues ADD COLUMN priority VARCHAR(20) DEFAULT 'Medium'")
            changes_made = True
            print("   ✅ Done!")
        else:
            print("   ✅ 'priority' column already exists")
        
        # ═══════════════════════════════════════
        # FIX 3: Create issue_comments table if missing
        # ═══════════════════════════════════════
        print("\n📋 Checking ISSUE_COMMENTS table...")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='issue_comments'
        """)
        
        if not cursor.fetchone():
            print("   ➕ Creating 'issue_comments' table...")
            cursor.execute("""
                CREATE TABLE issue_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_id INTEGER NOT NULL,
                    user_id INTEGER,
                    comment_text TEXT NOT NULL,
                    comment_type VARCHAR(20) DEFAULT 'comment',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(issue_id) REFERENCES issues (id),
                    FOREIGN KEY(user_id) REFERENCES users (id)
                )
            """)
            changes_made = True
            print("   ✅ Done!")
        else:
            print("   ✅ 'issue_comments' table already exists")
        
        # ═══════════════════════════════════════
        # COMMIT CHANGES
        # ═══════════════════════════════════════
        if changes_made:
            conn.commit()
            print("\n" + "="*50)
            print("🎉 DATABASE FIXED SUCCESSFULLY!")
            print("="*50)
            print("\n✅ All columns and tables are now ready!")
            print("📌 Next step: Run 'python run.py' to start the app")
        else:
            print("\n" + "="*50)
            print("✅ Database is already up to date!")
            print("="*50)
            print("📌 You can run 'python run.py' to start the app")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        print("\n💡 If you see 'duplicate column' errors, that's OK!")
        print("   It means the columns were already added.")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*50)
    print("🔧 PHASE 5 DATABASE FIX SCRIPT")
    print("="*50)
    success = fix_database()
    
    if success:
        print("\n💡 TIP: After running the app, you can:")
        print("   1. Login as admin")
        print("   2. Test the Issues feature")
        print("   3. Test the Rooms Search feature")
        print("\n🚀 Ready to go!")
    else:
        print("\n⚠️  Fix failed. Check the error above.")
        print("   You might need to run: flask db upgrade")