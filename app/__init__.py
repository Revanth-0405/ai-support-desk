from flask import Flask, jsonify
from app.extensions import db, migrate, jwt, ma, socketio
from app.config import Config
from app.utils.logging_config import setup_logging


def create_app(config_class=Config):
    # Wire up logging before app creation
    setup_logging()
    
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.tickets import tickets_bp
    from app.routes.knowledge_base import kb_bp
    from app.routes.health import health_bp
    from app.sockets.presence import presence_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
    app.register_blueprint(kb_bp, url_prefix='/api/kb')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    app.register_blueprint(presence_bp, url_prefix='/api/presence')

    # Centralized Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad Request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal Server Error"}), 500

    return app