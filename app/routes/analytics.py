from flask import Blueprint, jsonify
from app.models.ticket import Ticket
from app.models.user import User
from app.services.chat_service import ChatService
from app.utils.decorators import role_required
from app.extensions import db
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/tickets', methods=['GET'])
@role_required(['admin'])
def ticket_analytics():
    """Aggregate ticket stats by status and priority"""
    status_counts = db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    priority_counts = db.session.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
    
    return jsonify({
        "by_status": dict(status_counts),
        "by_priority": dict(priority_counts)
    }), 200

@analytics_bp.route('/agents', methods=['GET'])
@role_required(['admin'])
def agent_analytics():
    """Agent workload distribution"""
    agent_loads = db.session.query(
        User.username, func.count(Ticket.id)
    ).join(Ticket, User.id == Ticket.assigned_agent_id).group_by(User.username).all()
    
    return jsonify({
        "agent_ticket_load": dict(agent_loads)
    }), 200

@analytics_bp.route('/ai', methods=['GET'])
@role_required(['admin'])
def ai_analytics():
    """AI Usage overview from DynamoDB"""
    dynamodb = ChatService.get_db()
    table = dynamodb.Table('AIUsageLogs')
    response = table.scan()
    items = response.get('Items', [])
    
    total_calls = len(items)
    success_calls = sum(1 for i in items if i.get('success'))
    total_latency = sum(int(i.get('latency_ms', 0)) for i in items)
    
    return jsonify({
        "total_calls": total_calls,
        "success_rate": f"{(success_calls / total_calls * 100):.1f}%" if total_calls > 0 else "0%",
        "avg_latency_ms": (total_latency // total_calls) if total_calls > 0 else 0
    }), 200