from flask import Blueprint, jsonify
from app.extensions import db
import sqlalchemy

health_bp = Blueprint('health', __name__)

@health_bp.route('', methods=['GET'])
def health_check():
    # Includes all 5 checks required by the spec
    health_status = {
        "flask_app": "healthy", 
        "postgresql": "unhealthy", 
        "dynamodb": "unhealthy", 
        "gemini": "unhealthy",
        "websocket": "unhealthy"
    }
    
    # 1. PostgreSQL Check
    try:
        db.session.execute(sqlalchemy.text('SELECT 1'))
        health_status["postgresql"] = "healthy"
    except Exception as e:
        health_status["postgresql"] = f"error: {str(e)}"
        
    # 2. DynamoDB Check
    try:
        from app.services.chat_service import ChatService
        dynamo = ChatService.get_db()
        dynamo.meta.client.list_tables(Limit=1)
        health_status["dynamodb"] = "healthy"
    except Exception as e:
        health_status["dynamodb"] = f"error: {str(e)}"
        
    # 3. Gemini Check
    try:
        from app.services.ai_service import AIService
        model = AIService._get_model()
        model.count_tokens("ping")
        health_status["gemini"] = "healthy"
    except Exception as e:
        health_status["gemini"] = f"error: {str(e)}"
        
    # 4. WebSocket Check
    try:
        from app.extensions import socketio
        if socketio.server is not None:
            health_status["websocket"] = "healthy"
        else:
            health_status["websocket"] = "uninitialized"
    except Exception as e:
        health_status["websocket"] = f"error: {str(e)}"
        
    status_code = 200 if all(v == "healthy" for v in health_status.values()) else 500
    return jsonify(health_status), status_code