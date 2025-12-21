import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'

    # User loader for Flask-Login
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import models
    from .models import Room, Schedule, ScheduleImport, Issue
    
    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.rooms import rooms_bp
    from .routes.admin import admin_bp
    from .routes.imports import imports_bp
    from .routes.issues import issues_bp

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(imports_bp)
    app.register_blueprint(issues_bp)

    return app