import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # IMPORT INSIDE create_app AFTER db.init_app()
    from .models import Room, Schedule, ScheduleImport, Issue
    
    from .routes.dashboard import dashboard_bp
    from .routes.rooms import rooms_bp
    from .routes.admin import admin_bp
    from .routes.imports import imports_bp
    from .routes.issues import issues_bp

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(imports_bp)
    app.register_blueprint(issues_bp)

    return app
