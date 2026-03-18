from flask import Flask
from app.extensions import db, migrate, jwt, ma, socketio
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    # Initialize socketio with the app
    socketio.init_app(app, cors_allowed_origins="*")

    # Register Blueprints (Ensure these files exist)
    from app.routes.auth import auth_bp
    from app.routes.tickets import tickets_bp
    from app.routes.knowledge_base import kb_bp
    from app.routes.health import health_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
    app.register_blueprint(kb_bp, url_prefix='/api/kb')
    app.register_blueprint(health_bp, url_prefix='/api/health')

    return app