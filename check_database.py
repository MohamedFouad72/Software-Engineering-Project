"""
Database Verification Script
Checks if all tables and columns are properly created.
"""

import os
import sys
import sqlite3

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("🔍 COMPLETE DATABASE VERIFICATION")
print("=" * 60)

# 1. Check database file
db_path = "instance/app.db"
print(f"📁 Database path: {os.path.abspath(db_path)}")
print(f"📁 File exists: {os.path.exists(db_path)}")

if not os.path.exists(db_path):
    print("❌ Database not found!")
    exit(1)

# 2. Connect and check all tables
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

print(f"\n📊 Total tables: {len(tables)}")

# Check each table
for table in tables:
    table_name = table[0]
    print(f"\n📋 Table: {table_name}")
    
    # Get columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"   Columns ({len(columns)}):")
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        not_null = "NOT NULL" if col[3] else ""
        default = f"DEFAULT {col[4]}" if col[4] else ""
        pk = "PRIMARY KEY" if col[5] else ""
        
        print(f"     - {col_name}: {col_type} {not_null} {default} {pk}".strip())
    
    # Count rows
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   Records: {count}")
    except Exception as e:
        print(f"   ❌ Error reading data: {e}")

conn.close()

print("\n" + "=" * 60)
print("✅ DATABASE VERIFICATION COMPLETE")
print("=" * 60)

# 3. Test model imports
print("\n🧪 Testing model imports...")
try:
    from src import create_app, db
    from src.models import User, Room, Schedule, Issue, ScheduleImport, IssueComment
    
    app = create_app()
    with app.app_context():
        print("✅ All models imported successfully")
        print(f"✅ Users in DB: {User.query.count()}")
        print(f"✅ Rooms in DB: {Room.query.count()}")
        
except Exception as e:
    print(f"❌ Import error: {e}")