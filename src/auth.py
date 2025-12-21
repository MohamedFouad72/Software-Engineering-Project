from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def login_required_with_role(*roles):
    """
    Decorator to check if user is logged in and has required role
    Usageeeeeee @login_required_with_role('admin', 'staff')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login'))
            
            if roles and current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator for admin-only routes"""
    return login_required_with_role('admin')(f)

def staff_or_admin_required(f):
    """Decorator for staff or admin routes"""
    return login_required_with_role('admin', 'staff')(f)