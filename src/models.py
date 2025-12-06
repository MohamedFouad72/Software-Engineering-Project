from . import db

class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    building = db.Column(db.String(20), nullable=False)
    number = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default="Available")

    def toggle_status(self):
        self.status = "Occupied" if self.status == "Available" else "Available"
