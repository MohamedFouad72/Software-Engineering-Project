"""
Enhanced Room Routes with Search & Filter - Phase 5
File: src/routes/rooms.py
"""

from flask import Blueprint, redirect, url_for, render_template, request, jsonify
from flask_login import login_required
from sqlalchemy import or_

from .. import db
from ..models import Room

rooms_bp = Blueprint("rooms", __name__)


@rooms_bp.route("/rooms/<int:room_id>/toggle")
@login_required
def toggle(room_id):
    """Toggle room status between Available and Occupied"""
    room = Room.query.get_or_404(room_id)
    room.toggle_status()
    db.session.commit()
    return redirect(url_for("dashboard.dashboard"))


@rooms_bp.route("/rooms/search")
@login_required
def search():
    """
    Search and filter rooms
    
    Query parameters:
    - q: Search keyword (room number, building)
    - building: Filter by building
    - status: Filter by status (Available, Occupied)
    - capacity_min: Minimum capacity
    - capacity_max: Maximum capacity
    - format: Response format (html or json)
    """
    
    query = Room.query

    # Keyword search
    search_term = request.args.get("q", "").strip()
    if search_term:
        query = query.filter(
            or_(
                Room.building.ilike(f"%{search_term}%"),
                Room.number.ilike(f"%{search_term}%")
            )
        )

    # Building filter
    building_filter = request.args.get("building")
    if building_filter:
        query = query.filter_by(building=building_filter)

    # Status filter
    status_filter = request.args.get("status")
    if status_filter:
        query = query.filter_by(status=status_filter)

    # Capacity filters
    capacity_min = request.args.get("capacity_min")
    capacity_max = request.args.get("capacity_max")
    
    if capacity_min:
        try:
            query = query.filter(Room.capacity >= int(capacity_min))
        except ValueError:
            pass
    
    if capacity_max:
        try:
            query = query.filter(Room.capacity <= int(capacity_max))
        except ValueError:
            pass

    # Execute query
    rooms = query.order_by(Room.building.asc(), Room.number.asc()).all()

    # Response format
    response_format = request.args.get("format", "html")
    
    if response_format == "json":
        # JSON response for AJAX requests
        return jsonify({
            "count": len(rooms),
            "rooms": [{
                "id": r.id,
                "building": r.building,
                "number": r.number,
                "status": r.status,
                "capacity": r.capacity
            } for r in rooms]
        })
    
    # HTML response
    # Get all buildings for filter dropdown
    all_buildings = db.session.query(Room.building)\
                               .distinct()\
                               .order_by(Room.building)\
                               .all()
    buildings = [b[0] for b in all_buildings]
    
    return render_template("rooms_search.html",
                          rooms=rooms,
                          buildings=buildings,
                          search_term=search_term,
                          current_building=building_filter,
                          current_status=status_filter,
                          count=len(rooms))


@rooms_bp.route("/rooms/autocomplete")
@login_required
def autocomplete():
    """
    Autocomplete endpoint for room search
    Returns JSON array of room suggestions
    """
    term = request.args.get("term", "").strip()
    
    if not term or len(term) < 2:
        return jsonify([])
    
    rooms = Room.query.filter(
        or_(
            Room.building.ilike(f"%{term}%"),
            Room.number.ilike(f"%{term}%")
        )
    ).limit(10).all()
    
    suggestions = [
        {
            "value": f"{r.building} {r.number}",
            "label": f"{r.building} {r.number} ({r.status})",
            "id": r.id
        }
        for r in rooms
    ]
    
    return jsonify(suggestions)