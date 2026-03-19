from flask import Blueprint, jsonify
from app.extensions import db
import sqlalchemy

health_bp = Blueprint('health', __name__)

@health_bp.route('', methods=['GET'])
def health_check():
    health_status = {
        "flask_app": "healthy",
        "postgresql": "unhealthy",
    }
    try:
        db.session.execute(sqlalchemy.text('SELECT 1'))
        health_status["postgresql"] = "healthy"
    except Exception as e:
        health_status["postgresql"] = f"unhealthy: {str(e)}"
        
    return jsonify(health_status), 200 if health_status["postgresql"] == "healthy" else 500