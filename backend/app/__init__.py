from flask import Flask
from flask_cors import CORS
from config import Config
from app.db import initialize_database


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)
    initialize_database()

    from app.routes.trips import trips_bp
    from app.routes.zones import zones_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(trips_bp, url_prefix="/api")
    app.register_blueprint(zones_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")

    return app
