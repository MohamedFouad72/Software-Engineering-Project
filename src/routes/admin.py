from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..auth import admin_required
from .. import db
from ..models import Room

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/rooms")
@admin_required
def manage_rooms():
    """Display all rooms for management"""
    rooms = Room.query.all()
    return render_template("admin/manage_rooms.html", rooms=rooms)

@admin_bp.route("/rooms/add", methods=["GET", "POST"])
@admin_required
def add_room():
    """Add a new room"""
    if request.method == "POST":
        building = request.form.get("building")
        number = request.form.get("number")
        status = request.form.get("status", "Available")
        
        if not building or not number:
            flash("Building and number are required!", "error")
            return redirect(url_for("admin.add_room"))
        
        new_room = Room(building=building, number=number, status=status)
        db.session.add(new_room)
        db.session.commit()
        
        flash(f"Room {building} {number} added successfully!", "success")
        return redirect(url_for("admin.manage_rooms"))
    
    return render_template("admin/add_room.html")

@admin_bp.route("/rooms/<int:room_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_room(room_id):
    """Edit an existing room"""
    room = Room.query.get_or_404(room_id)
    
    if request.method == "POST":
        room.building = request.form.get("building", room.building)
        room.number = request.form.get("number", room.number)
        room.status = request.form.get("status", room.status)
        
        db.session.commit()
        flash(f"Room {room.building} {room.number} updated successfully!", "success")
        return redirect(url_for("admin.manage_rooms"))
    
    return render_template("admin/edit_room.html", room=room)

@admin_bp.route("/rooms/<int:room_id>/delete", methods=["POST"])
@admin_required
def delete_room(room_id):
    """Delete a room"""
    room = Room.query.get_or_404(room_id)
    room_name = f"{room.building} {room.number}"
    
    db.session.delete(room)
    db.session.commit()
    
    flash(f"Room {room_name} deleted successfully!", "success")
    return redirect(url_for("admin.manage_rooms"))
