from flask import Blueprint, render_template, make_response
from ..models import Room, Schedule  # <--- Added Schedule
import csv
import io
from flask import make_response

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def dashboard():
    rooms = Room.query.order_by(Room.building.asc(), Room.number.asc()).all()
    return render_template("dashboard.html", rooms=rooms)

# --- PASTE AT THE BOTTOM OF src/routes/dashboard.py ---

@dashboard_bp.route('/export/schedules')
def export_schedules():
    # 1. Setup CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    
    # 2. Write Header Row
    cw.writerow(['Building', 'Room', 'Date', 'Open Time', 'Close Time'])

    # 3. Query Real Data from Database
    # We join with Room to ensure we only get valid schedules and order by date
    schedules = Schedule.query.join(Room).order_by(Schedule.date.desc()).all()

    # 4. Loop through and write rows
    for s in schedules:
        cw.writerow([
            s.room.building,       # From Room model
            s.room.number,         # From Room model
            s.date,                # From Schedule model
            s.open_time,           # From Schedule model
            s.close_time           # From Schedule model
        ])

    # 5. Create Response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=schedule_export.csv"
    output.headers["Content-type"] = "text/csv"
    return output