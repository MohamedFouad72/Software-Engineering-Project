import os, sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import create_app, db
from src.models import User

app = create_app()

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(email='admin@campus.edu').first()
    
    if not admin:
        admin = User(
            name='Admin User',
            email='admin@campus.edu',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("✅ Admin user created: admin@campus.edu / admin123")
    else:
        print("⚠️  Admin already exists")
    
    # Create sample staff user
    staff = User.query.filter_by(email='staff@campus.edu').first()
    if not staff:
        staff = User(
            name='Staff Member',
            email='staff@campus.edu',
            role='staff'
        )
        staff.set_password('staff123')
        db.session.add(staff)
        print("✅ Staff user created: staff@campus.edu / staff123")
    else:
        print("⚠️  Staff user already exists")
    
    db.session.commit()
    print("\n🎉 Setup complete! You can now login.")