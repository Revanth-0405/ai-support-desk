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
    """Aggregate ticket stats by status, priority, and category + avg resolution time"""
    tickets = Ticket.query.all()
    
    by_status = {}
    by_priority = {}
    by_category = {}
    resolution_times = []
    
    for t in tickets:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
        if t.category:
            by_category[t.category] = by_category.get(t.category, 0) + 1
            
        if t.status == 'resolved' and t.updated_at and t.created_at:
            delta = (t.updated_at - t.created_at).total_seconds()
            resolution_times.append(delta)
            
    avg_res_time = (sum(resolution_times) / len(resolution_times)) if resolution_times else 0
    
    return jsonify({
        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,
        "avg_resolution_time_seconds": avg_res_time
    }), 200

@analytics_bp.route('/agents', methods=['GET'])
@role_required(['admin'])
def agent_analytics():
    """Agent workload and resolution rate"""
    agents = User.query.filter_by(role='agent').all()
    stats = {}
    
    for agent in agents:
        assigned = Ticket.query.filter_by(assigned_agent_id=agent.id).all()
        total = len(assigned)
        resolved = sum(1 for t in assigned if t.status == 'resolved')
        
        stats[agent.username] = {
            "tickets_assigned": total,
            "resolution_rate_percent": (resolved / total * 100) if total > 0 else 0,
            "avg_response_time_placeholder": "Computed via chat logs in production"
        }
        
    return jsonify({"agent_stats": stats}), 200

@analytics_bp.route('/ai', methods=['GET'])
@role_required(['admin'])
def ai_analytics():
    """AI Usage overview including calls by feature"""
    dynamodb = ChatService.get_db()
    table = dynamodb.Table('AIUsageLogs')
    response = table.scan()
    items = response.get('Items', [])
    
    total_calls = len(items)
    success_calls = sum(1 for i in items if i.get('success'))
    total_latency = sum(int(i.get('latency_ms', 0)) for i in items)
    
    calls_by_feature = {}
    for item in items:
        feat = item.get('feature', 'unknown')
        calls_by_feature[feat] = calls_by_feature.get(feat, 0) + 1
    
    return jsonify({
        "total_calls": total_calls,
        "success_rate": f"{(success_calls / total_calls * 100):.1f}%" if total_calls > 0 else "0%",
        "avg_latency_ms": (total_latency // total_calls) if total_calls > 0 else 0,
        "calls_by_feature": calls_by_feature
    }), 200