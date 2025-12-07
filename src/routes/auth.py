from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from ..models import User
from .. import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    # If user already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Please enter both email and password.", "error")
            return redirect(url_for("auth.login"))
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f"Welcome back, {user.name}!", "success")
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("auth.login"))
    
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    """Logout user"""
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("auth.login"))