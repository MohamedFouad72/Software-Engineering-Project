from datetime import datetime
from flask_login import UserMixin
from . import db, bcrypt

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")
    # Roles: admin, staff, ta_prof, maintenance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if password matches hash"""
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    building = db.Column(db.String(20), nullable=False)
    number = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default="Available")

    def toggle_status(self):
        self.status = "Occupied" if self.status == "Available" else "Available"


class ScheduleImport(db.Model):
    __tablename__ = "schedule_imports"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.String(120))
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

    schedules = db.relationship("Schedule", back_populates="import_record", cascade="all, delete-orphan")


class Schedule(db.Model):
    __tablename__ = "schedules"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    import_id = db.Column(db.Integer, db.ForeignKey("schedule_imports.id"))

    room = db.relationship("Room", backref=db.backref("schedules", lazy=True))
    import_record = db.relationship("ScheduleImport", back_populates="schedules")


class Issue(db.Model):
    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    reporter_id = db.Column(db.String(120))
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="New")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship("Room", backref=db.backref("issues", lazy=True))