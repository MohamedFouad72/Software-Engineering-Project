import os, sys

# Ensure project root is in sys.path → reliable import paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import create_app, db

from src.models import Room

app = create_app()

with app.app_context():
    db.create_all()  # Ensure tables exist before inserting data

    if Room.query.count() == 0:
        sample_rooms = [
            Room(building="AB", number="G006-B", status="Available"),
            Room(building="AB", number="G038-B", status="Occupied"),
            Room(building="AB", number="G011-B", status="Available"),
        ]

        db.session.add_all(sample_rooms)
        db.session.commit()

        print("Database seeded successfully! Rooms inserted: ", Room.query.count())
    else:
        print("Existing data detected — seeding skipped to avoid duplicates.")
