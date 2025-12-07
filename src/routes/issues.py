from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import db
from ..models import Issue, Room

issues_bp = Blueprint("issues", __name__)


@issues_bp.route("/issues/report", methods=["GET", "POST"])
def report_issue():
    rooms = Room.query.order_by(Room.building.asc(), Room.number.asc()).all()

    if request.method == "POST":
        room_id = request.form.get("room_id")
        reporter_id = request.form.get("reporter_id")
        description = (request.form.get("description") or "").strip()

        if not room_id or not description:
            flash("Please choose a room and describe the issue.", "error")
            return redirect(url_for("issues.report_issue"))

        new_issue = Issue(
            room_id=int(room_id),
            reporter_id=reporter_id,
            description=description,
        )
        db.session.add(new_issue)
        db.session.commit()

        flash("Issue reported. We set the status to New for follow-up.", "success")
        return redirect(url_for("issues.list_issues"))

    return render_template("issue_report.html", rooms=rooms)


@issues_bp.route("/issues")
def list_issues():
    issues = Issue.query.order_by(Issue.created_at.desc()).all()
    return render_template("issues_list.html", issues=issues)


@issues_bp.route("/issues/<int:issue_id>/resolve", methods=["POST"])
def resolve_issue(issue_id: int):
    issue = Issue.query.get_or_404(issue_id)
    issue.status = "Resolved"
    db.session.commit()
    flash("Issue marked as resolved.", "success")
    return redirect(url_for("issues.list_issues"))
