import os
import sys

# Ensure project root is in sys.path → reliable import paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import create_app, db
from src.models import Room, User

app = create_app()

with app.app_context():
    db.create_all()  # Ensure tables exist

    # Seed Rooms (only if empty)
    if Room.query.count() == 0:
        sample_rooms = [
            Room(building="AB", number="G006-B", status="Available"),
            Room(building="AB", number="G038-B", status="Occupied"),
            Room(building="AB", number="G011-B", status="Available"),
        ]

        db.session.add_all(sample_rooms)
        print(f"Inserted rooms: {len(sample_rooms)}")
    else:
        print("Rooms already exist — skipping rooms seeding.")

    # Seed Users (Admin + Staff demo accounts)
    if User.query.count() == 0:
        admin = User(name="Admin User", email="admin@campus.edu", role="admin")
        admin.set_password("admin123")

        staff = User(name="Staff User", email="staff@campus.edu", role="staff")
        staff.set_password("staff123")

        db.session.add_all([admin, staff])
        print("Inserted demo users: admin & staff")
    else:
        print("Users already exist — skipping user seeding.")

    db.session.commit()
    print("Database seeded successfully!")
