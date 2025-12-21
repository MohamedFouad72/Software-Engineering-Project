"""
Complete Database Rebuild Script - Phase 5
This script will recreate the entire database with all models and sample data.
"""

import os
import sys
import shutil
from datetime import datetime, time

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("=" * 60)
print("🔨 COMPLETE DATABASE REBUILD - PHASE 5")
print("=" * 60)

# 1. Delete old database and migrations
db_path = "instance/app.db"
migrations_path = "migrations"

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ Deleted old database: {db_path}")

if os.path.exists(migrations_path):
    shutil.rmtree(migrations_path)
    print(f"✅ Deleted migrations folder: {migrations_path}")

# 2. Import app and models AFTER deleting old files
from src import create_app, db
from src.models import User, Room, Schedule, Issue, ScheduleImport, IssueComment

app = create_app()

with app.app_context():
    # 3. Create all tables
    print("\n📊 Creating all database tables...")
    db.create_all()
    
    # 4. Add users
    print("👥 Adding users...")
    
    # Admin user
    admin = User(
        name="Admin User",
        email="admin@campus.edu",
        role="admin"
    )
    admin.set_password("admin123")
    db.session.add(admin)
    
    # Staff user
    staff = User(
        name="Staff User", 
        email="staff@campus.edu",
        role="staff"
    )
    staff.set_password("staff123")
    db.session.add(staff)
    
    # 5. Add rooms with capacity
    print("🏢 Adding rooms...")
    
    rooms_data = [
        {"building": "AB", "number": "G006-B", "status": "Available", "capacity": 30},
        {"building": "AB", "number": "G038-B", "status": "Occupied", "capacity": 25},
        {"building": "AB", "number": "G011-B", "status": "Available", "capacity": 40},
        {"building": "ENG", "number": "101", "status": "Available", "capacity": 50},
        {"building": "SCI", "number": "201", "status": "Occupied", "capacity": 35},
        {"building": "LIB", "number": "301", "status": "Available", "capacity": 20},
    ]
    
    for room_data in rooms_data:
        room = Room(**room_data)
        db.session.add(room)
    
    # 6. Add sample schedules
    print("⏰ Adding sample schedules...")
    
    # Get first two rooms
    room1 = Room.query.filter_by(building="AB", number="G006-B").first()
    room2 = Room.query.filter_by(building="ENG", number="101").first()
    
    if room1:
        schedule1 = Schedule(
            room_id=room1.id,
            date=datetime.now().date(),
            open_time=time(8, 0),
            close_time=time(18, 0)
        )
        db.session.add(schedule1)
    
    if room2:
        schedule2 = Schedule(
            room_id=room2.id,
            date=datetime.now().date(),
            open_time=time(9, 0),
            close_time=time(17, 0)
        )
        db.session.add(schedule2)
    
    # 7. Save everything
    db.session.commit()
    
    # 8. Final verification
    print("\n" + "=" * 60)
    print("✅ DATABASE REBUILD COMPLETE!")
    print("=" * 60)
    
    print(f"👤 Users count: {User.query.count()}")
    print(f"🏢 Rooms count: {Room.query.count()}")
    print(f"⏰ Schedules count: {Schedule.query.count()}")
    
    print("\n🔑 Login Credentials:")
    print("   Admin: admin@campus.edu / admin123")
    print("   Staff: staff@campus.edu / staff123")
    
    print("\n🚀 You can now run the app with: python run.py")
    print("=" * 60)