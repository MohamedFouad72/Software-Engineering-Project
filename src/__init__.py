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
    from .models import Room
    
    from .routes.dashboard import dashboard_bp
    from .routes.rooms import rooms_bp
    from .routes.admin import admin_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(admin_bp)

    return app
