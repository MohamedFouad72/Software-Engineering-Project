"""
Enhanced Database Models for Phase 5
Add this to src/models.py (replace existing Issue class)
"""

from datetime import datetime
from flask_login import UserMixin
from . import db, bcrypt


# ============= User Model (No changes) =============
class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# ============= Room Model (No changes) =============
class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    building = db.Column(db.String(20), nullable=False, index=True)
    number = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default="Available")
    capacity = db.Column(db.Integer)  # NEW: Optional capacity field

    def toggle_status(self):
        self.status = "Occupied" if self.status == "Available" else "Available"

    def __repr__(self):
        return f"<Room {self.building} {self.number}>"


# ============= ENHANCED Issue Model =============
class Issue(db.Model):
    """
    Enhanced Issue model with assignment and lifecycle tracking
    """
    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False, index=True)
    reporter_id = db.Column(db.String(120))
    description = db.Column(db.Text, nullable=False)
    
    # Status: New, In Progress, Resolved
    status = db.Column(db.String(20), default="New", index=True)
    
    # NEW: Assignment tracking
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    # NEW: Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # NEW: Priority (optional)
    priority = db.Column(db.String(20), default="Medium")  # Low, Medium, High

    # Relationships
    room = db.relationship("Room", backref=db.backref("issues", lazy=True))
    assigned_user = db.relationship("User", foreign_keys=[assigned_to], 
                                    backref="assigned_issues")
    comments = db.relationship("IssueComment", backref="issue", 
                               lazy="dynamic", cascade="all, delete-orphan")

    def assign_to(self, user_id):
        """Assign issue to a user"""
        self.assigned_to = user_id
        if self.status == "New":
            self.status = "In Progress"

    def resolve(self):
        """Mark issue as resolved"""
        self.status = "Resolved"
        self.resolved_at = datetime.utcnow()

    def reopen(self):
        """Reopen a resolved issue"""
        self.status = "In Progress"
        self.resolved_at = None

    def get_status_badge_class(self):
        """Get CSS class for status badge"""
        status_map = {
            "New": "status-new",
            "In Progress": "status-progress",
            "Resolved": "status-resolved"
        }
        return status_map.get(self.status, "status-new")

    def __repr__(self):
        return f"<Issue #{self.id} - {self.status}>"


# ============= NEW: IssueComment Model =============
class IssueComment(db.Model):
    """
    Comments/timeline for issues
    """
    __tablename__ = "issue_comments"

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    comment_text = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(20), default="comment")  
    # Types: comment, status_change, assignment, resolution
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", backref="comments")

    def __repr__(self):
        return f"<Comment on Issue #{self.issue_id}>"


# ============= ScheduleImport Model (No changes) =============
class ScheduleImport(db.Model):
    __tablename__ = "schedule_imports"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.String(120))
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

    schedules = db.relationship("Schedule", back_populates="import_record", 
                                cascade="all, delete-orphan")


# ============= Schedule Model (No changes) =============
class Schedule(db.Model):
    __tablename__ = "schedules"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    import_id = db.Column(db.Integer, db.ForeignKey("schedule_imports.id"))

    room = db.relationship("Room", backref=db.backref("schedules", lazy=True))
    import_record = db.relationship("ScheduleImport", back_populates="schedules")