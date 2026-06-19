from flask import Flask
from flask_cors import CORS
from config import DevelopmentConfig
from app.db import init_db


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)
    init_db(app)

    from app.routes.trips import trips_bp
    from app.routes.zones import zones_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(trips_bp, url_prefix="/api/v1")
    app.register_blueprint(zones_bp, url_prefix="/api/v1")
    app.register_blueprint(analytics_bp, url_prefix="/api/v1")

    return app
