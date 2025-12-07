import os
from datetime import datetime

import pandas as pd
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from .. import db
from ..models import Room, Schedule, ScheduleImport

imports_bp = Blueprint("imports", __name__)


def _allowed_file(filename: str | None) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", set())


def _split_room_label(label: str | None) -> tuple[str | None, str | None]:
    label = (label or "").strip()
    if not label:
        return None, None
    parts = label.split(None, 1)
    building = parts[0]
    number = parts[1] if len(parts) > 1 else "000"
    return building, number


def _read_schedule_dataframe(file_path: str) -> pd.DataFrame:
    if file_path.lower().endswith(".csv"):
        return pd.read_csv(file_path)
    return pd.read_excel(file_path)


def _parse_date(value):
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _parse_time(value):
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value).time()
    except Exception:
        return None


@imports_bp.route("/import", methods=["GET", "POST"])
def import_schedule():
    recent_imports = ScheduleImport.query.order_by(ScheduleImport.upload_time.desc()).limit(5).all()

    if request.method == "POST":
        file = request.files.get("schedule_file")
        uploaded_by = request.form.get("uploaded_by") or "Unknown"

        if not file or file.filename == "":
            flash("Please choose a schedule file before submitting.", "error")
            return redirect(url_for("imports.import_schedule"))

        if not _allowed_file(file.filename):
            flash("Only .csv and .xlsx schedule files are supported right now.", "error")
            return redirect(url_for("imports.import_schedule"))

        safe_name = secure_filename(file.filename or "")
        timestamp_prefix = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        stored_name = f"{timestamp_prefix}_{safe_name}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
        file.save(save_path)

        try:
            df = _read_schedule_dataframe(save_path)
        except Exception as exc:
            current_app.logger.exception("Failed to read schedule file: %s", exc)
            flash("Could not read that file. Please confirm it opens in Excel first.", "error")
            return redirect(url_for("imports.import_schedule"))

        required_cols = {"Room", "Date", "OpenTime", "CloseTime"}
        if not required_cols.issubset(df.columns):
            flash("File must include columns: Room, Date, OpenTime, CloseTime.", "error")
            return redirect(url_for("imports.import_schedule"))

        import_record = ScheduleImport(filename=safe_name, uploaded_by=uploaded_by)
        db.session.add(import_record)
        db.session.flush()

        created_rows = 0
        skipped_rows = 0

        for _, row in df.iterrows():
            building, number = _split_room_label(row.get("Room"))
            date_value = _parse_date(row.get("Date"))
            open_time = _parse_time(row.get("OpenTime"))
            close_time = _parse_time(row.get("CloseTime"))

            if not (building and number and date_value and open_time and close_time):
                skipped_rows += 1
                continue

            room = Room.query.filter_by(building=building, number=number).first()
            if not room:
                room = Room(building=building, number=number)
                db.session.add(room)
                db.session.flush()

            schedule_entry = Schedule(
                room_id=room.id,
                date=date_value,
                open_time=open_time,
                close_time=close_time,
                import_id=import_record.id,
            )
            db.session.add(schedule_entry)
            created_rows += 1

        db.session.commit()

        message = f"Imported {created_rows} schedule rows"
        if skipped_rows:
            message += f" (skipped {skipped_rows} incomplete rows)"
        flash(message + ".", "success")
        return redirect(url_for("imports.import_schedule"))

    return render_template("import.html", recent_imports=recent_imports)
