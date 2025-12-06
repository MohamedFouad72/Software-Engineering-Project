from flask import Blueprint, redirect, url_for
from .. import db
from ..models import Room

rooms_bp = Blueprint("rooms", __name__)

@rooms_bp.route("/rooms/<int:room_id>/toggle")
def toggle(room_id):
    room = Room.query.get_or_404(room_id)
    room.toggle_status()
    db.session.commit()
    return redirect(url_for("dashboard.dashboard"))
