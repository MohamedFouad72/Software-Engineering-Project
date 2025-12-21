"""
Enhanced Issue Management Routes - Phase 5
File: src/routes/issues.py
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from .. import db
from ..models import Issue, IssueComment, Room, User

issues_bp = Blueprint("issues", __name__)


@issues_bp.route("/issues/report", methods=["GET", "POST"])
@login_required
def report_issue():
    """Report a new issue"""
    rooms = Room.query.order_by(Room.building.asc(), Room.number.asc()).all()

    if request.method == "POST":
        room_id = request.form.get("room_id")
        reporter_id = request.form.get("reporter_id") or current_user.name
        description = (request.form.get("description") or "").strip()
        priority = request.form.get("priority", "Medium")

        if not room_id or not description:
            flash("Please choose a room and describe the issue.", "error")
            return redirect(url_for("issues.report_issue"))

        new_issue = Issue(
            room_id=int(room_id),
            reporter_id=reporter_id,
            description=description,
            priority=priority,
            status="New"
        )
        db.session.add(new_issue)
        db.session.commit()

        flash(f"Issue #{new_issue.id} reported successfully.", "success")
        return redirect(url_for("issues.issue_detail", issue_id=new_issue.id))

    return render_template("issue_report.html", rooms=rooms)


@issues_bp.route("/issues")
@login_required
def list_issues():
    """
    List all issues with filtering and sorting
    
    Query params:
    - status: Filter by status (New, In Progress, Resolved)
    - room_id: Filter by specific room
    - assigned_to: Filter by assigned user
    - sort: Sort by (date, priority, status)
    """
    query = Issue.query

    # Filters
    status_filter = request.args.get("status")
    room_filter = request.args.get("room_id")
    assigned_filter = request.args.get("assigned_to")

    if status_filter and status_filter != "all":
        query = query.filter_by(status=status_filter)
    
    if room_filter:
        query = query.filter_by(room_id=int(room_filter))
    
    if assigned_filter:
        if assigned_filter == "unassigned":
            query = query.filter_by(assigned_to=None)
        else:
            query = query.filter_by(assigned_to=int(assigned_filter))

    # Sorting
    sort_by = request.args.get("sort", "date")
    if sort_by == "priority":
        # Custom sort: High > Medium > Low
        priority_order = {"High": 1, "Medium": 2, "Low": 3}
        issues = sorted(query.all(), key=lambda x: priority_order.get(x.priority, 2))
    elif sort_by == "status":
        query = query.order_by(Issue.status.asc())
        issues = query.all()
    else:  # Default: date (newest first)
        query = query.order_by(Issue.created_at.desc())
        issues = query.all()

    # Get rooms and users for filter dropdowns
    rooms = Room.query.order_by(Room.building, Room.number).all()
    users = User.query.filter(User.role.in_(["admin", "staff", "maintenance"])).all()

    return render_template("issues_list.html", 
                          issues=issues,
                          rooms=rooms,
                          users=users,
                          current_status=status_filter,
                          current_room=room_filter,
                          current_assigned=assigned_filter,
                          current_sort=sort_by)


@issues_bp.route("/issues/<int:issue_id>")
@login_required
def issue_detail(issue_id):
    """View detailed issue page with timeline"""
    issue = Issue.query.get_or_404(issue_id)
    
    # Get all comments/timeline entries
    comments = IssueComment.query.filter_by(issue_id=issue_id)\
                                  .order_by(IssueComment.created_at.asc())\
                                  .all()
    
    # Get staff members for assignment dropdown
    staff_users = User.query.filter(
        User.role.in_(["admin", "staff", "maintenance"])
    ).all()

    return render_template("issue_detail.html", 
                          issue=issue,
                          comments=comments,
                          staff_users=staff_users)


@issues_bp.route("/issues/<int:issue_id>/assign", methods=["POST"])
@login_required
def assign_issue(issue_id):
    """Assign issue to a staff member (Admin/Staff only)"""
    
    # Check permission
    if current_user.role not in ["admin", "staff"]:
        flash("You don't have permission to assign issues.", "error")
        return redirect(url_for("issues.issue_detail", issue_id=issue_id))

    issue = Issue.query.get_or_404(issue_id)
    assigned_user_id = request.form.get("assigned_to")

    if not assigned_user_id:
        flash("Please select a user to assign.", "error")
        return redirect(url_for("issues.issue_detail", issue_id=issue_id))

    assigned_user = User.query.get(int(assigned_user_id))
    if not assigned_user:
        flash("Invalid user selected.", "error")
        return redirect(url_for("issues.issue_detail", issue_id=issue_id))

    # Assign issue
    issue.assign_to(int(assigned_user_id))

    # Add timeline comment
    comment = IssueComment(
        issue_id=issue.id,
        user_id=current_user.id,
        comment_text=f"Assigned to {assigned_user.name}",
        comment_type="assignment"
    )
    db.session.add(comment)
    db.session.commit()

    flash(f"Issue assigned to {assigned_user.name}.", "success")
    return redirect(url_for("issues.issue_detail", issue_id=issue_id))


@issues_bp.route("/issues/<int:issue_id>/update-status", methods=["POST"])
@login_required
def update_status(issue_id):
    """Update issue status"""
    
    issue = Issue.query.get_or_404(issue_id)
    new_status = request.form.get("status")

    if new_status not in ["New", "In Progress", "Resolved"]:
        flash("Invalid status.", "error")
        return redirect(url_for("issues.issue_detail", issue_id=issue_id))

    old_status = issue.status

    # Update status
    if new_status == "Resolved":
        issue.resolve()
    elif new_status == "In Progress" and old_status == "Resolved":
        issue.reopen()
    else:
        issue.status = new_status

    # Add timeline comment
    comment = IssueComment(
        issue_id=issue.id,
        user_id=current_user.id,
        comment_text=f"Status changed from {old_status} to {new_status}",
        comment_type="status_change"
    )
    db.session.add(comment)
    db.session.commit()

    flash(f"Issue status updated to {new_status}.", "success")
    return redirect(url_for("issues.issue_detail", issue_id=issue_id))


@issues_bp.route("/issues/<int:issue_id>/comment", methods=["POST"])
@login_required
def add_comment(issue_id):
    """Add a comment to an issue"""
    
    issue = Issue.query.get_or_404(issue_id)
    comment_text = (request.form.get("comment_text") or "").strip()

    if not comment_text:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("issues.issue_detail", issue_id=issue_id))

    comment = IssueComment(
        issue_id=issue.id,
        user_id=current_user.id,
        comment_text=comment_text,
        comment_type="comment"
    )
    db.session.add(comment)
    db.session.commit()

    flash("Comment added successfully.", "success")
    return redirect(url_for("issues.issue_detail", issue_id=issue_id))


@issues_bp.route("/issues/<int:issue_id>/resolve", methods=["POST"])
@login_required
def resolve_issue(issue_id):
    """Quick resolve button (backward compatibility)"""
    issue = Issue.query.get_or_404(issue_id)
    
    if issue.status == "Resolved":
        flash("Issue is already resolved.", "info")
    else:
        issue.resolve()
        
        # Add timeline comment
        comment = IssueComment(
            issue_id=issue.id,
            user_id=current_user.id,
            comment_text="Issue marked as resolved",
            comment_type="resolution"
        )
        db.session.add(comment)
        db.session.commit()
        
        flash("Issue marked as resolved.", "success")
    
    return redirect(url_for("issues.list_issues"))