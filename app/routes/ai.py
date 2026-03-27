from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.models.ticket import Ticket
from app.models.knowledge_base import KnowledgeArticle
from app.services.ai_service import AIService
from app.services.chat_service import ChatService
from app.utils.decorators import role_required
from app.extensions import db
import sqlalchemy as sa

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/categorise/<uuid:ticket_id>', methods=['POST'])
@role_required(['agent', 'admin'])
def categorise_endpoint(ticket_id):
    """Re-run AI categorisation on a ticket """
    ticket = Ticket.query.get_or_404(ticket_id)
    
    result = AIService.categorise_ticket(str(ticket.id), ticket.subject, ticket.description)
    if result:
        ticket.category = result.get('category', ticket.category)
        ticket.priority = result.get('priority', ticket.priority)
        db.session.commit()
        return jsonify({"msg": "Categorisation updated", "result": result}), 200
        
    return jsonify({"error": "AI classification failed"}), 500

@ai_bp.route('/suggest/<uuid:ticket_id>', methods=['POST'])
@role_required(['agent', 'admin'])
def suggest_endpoint(ticket_id):
    ticket_id_str = str(ticket_id) # FIX: Standardize to string immediately
    ticket = Ticket.query.get_or_404(ticket_id_str)
    agent_id = get_jwt_identity()
    
    messages = ChatService.get_messages_by_ticket(ticket_id_str, limit=20)
    
    search_terms = ticket.subject.split() if ticket.subject else []
    if ticket.category:
        search_terms.append(ticket.category)
        
    kb_articles = []
    if search_terms:
        filters = [
            sa.or_(
                KnowledgeArticle.title.ilike(f"%{term}%"),
                KnowledgeArticle.category.ilike(f"%{term}%")
            ) for term in search_terms
        ]
        # FIX: Added filter_by(is_published=True) to prevent feeding deleted articles to AI
        kb_articles = KnowledgeArticle.query.filter_by(is_published=True).filter(sa.or_(*filters)).limit(3).all()
    
    suggestion = AIService.generate_suggestion(ticket_id_str, messages, kb_articles)
    if not suggestion:
        return jsonify({"error": "Failed to generate suggestion"}), 500
        
    stored_message = ChatService.put_message(
        ticket_id=ticket_id_str, sender_id=agent_id,
        sender_role='agent', content=suggestion, message_type='ai_suggestion'
    )
    
    from app.extensions import socketio
    socketio.emit('new_message', stored_message, room=f"ticket_{ticket_id_str}")
    
    return jsonify({"msg": "Suggestion generated", "message": stored_message}), 200

@ai_bp.route('/summarise/<uuid:ticket_id>', methods=['POST'])
@role_required(['agent', 'admin'])
def summarise_endpoint(ticket_id):
    ticket_id_str = str(ticket_id) # FIX: Standardize to string
    ticket = Ticket.query.get_or_404(ticket_id_str)
    
    messages = ChatService.get_messages_by_ticket(ticket_id_str, limit=100) 
    summary = AIService.summarise_conversation(ticket_id_str, messages)
    
    if summary:
        ticket.ai_summary = summary
        db.session.commit()
        return jsonify({"msg": "Summary generated", "summary": summary}), 200
        
    return jsonify({"error": "AI summarisation failed"}), 500

@ai_bp.route('/usage', methods=['GET'])
@role_required(['admin'])
def usage_stats():
    """Get AI API usage stats from DynamoDB [cite: 153-155]"""
    dynamodb = ChatService.get_db()
    table = dynamodb.Table('AIUsageLogs')
    
    # Scan is acceptable here as it's an admin analytics route without a GSI
    response = table.scan()
    items = response.get('Items', [])
    
    total_calls = len(items)
    success_calls = sum(1 for i in items if i.get('success'))
    total_latency = sum(int(i.get('latency_ms', 0)) for i in items)
    
    stats = {
        "total_calls": total_calls,
        "success_rate": f"{(success_calls / total_calls * 100):.1f}%" if total_calls > 0 else "0%",
        "avg_latency_ms": (total_latency // total_calls) if total_calls > 0 else 0,
        "calls_by_feature": {
            "categorise": sum(1 for i in items if i.get('feature') == 'categorise'),
            "suggest": sum(1 for i in items if i.get('feature') == 'suggest'),
            "summarise": sum(1 for i in items if i.get('feature') == 'summarise')
        }
    }
    return jsonify(stats), 200