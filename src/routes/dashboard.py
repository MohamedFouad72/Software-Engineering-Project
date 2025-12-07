from flask import Blueprint, render_template
from ..models import Room

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def dashboard():
    rooms = Room.query.order_by(Room.building.asc(), Room.number.asc()).all()
    return render_template("dashboard.html", rooms=rooms)
