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
    """Get AI-suggested response using context + KB [cite: 136-142]"""
    ticket = Ticket.query.get_or_404(ticket_id)
    agent_id = get_jwt_identity()
    
    # 1. Retrieve last 20 messages
    messages = ChatService.get_messages_by_ticket(ticket_id, limit=20)
    
    # 2. Search knowledge base (keyword match on subject/category)
    search_terms = ticket.subject.split()
    if ticket.category:
        search_terms.append(ticket.category)
        
    filters = [KnowledgeArticle.title.ilike(f"%{term}%") for term in search_terms]
    kb_articles = KnowledgeArticle.query.filter(sa.or_(*filters)).limit(3).all()
    
    # 3. Call AI
    suggestion = AIService.generate_suggestion(str(ticket_id), messages, kb_articles)
    if not suggestion:
        return jsonify({"error": "Failed to generate suggestion"}), 500
        
    # 4. Store in DynamoDB as ai_suggestion
    stored_message = ChatService.put_message(
        ticket_id=ticket_id,
        sender_id=agent_id,
        sender_role='agent',
        content=suggestion,
        message_type='ai_suggestion' # Visual indicator in chat history
    )
    
    # Optional: Broadcast it to the room so the agent sees it immediately
    from app.extensions import socketio
    socketio.emit('new_message', stored_message, room=f"ticket_{ticket_id}")
    
    return jsonify({"msg": "Suggestion generated", "message": stored_message}), 200

@ai_bp.route('/summarise/<uuid:ticket_id>', methods=['POST'])
@role_required(['agent', 'admin'])
def summarise_endpoint(ticket_id):
    """Generate conversation summary on demand """
    ticket = Ticket.query.get_or_404(ticket_id)
    messages = ChatService.get_messages_by_ticket(ticket_id, limit=100) # Fetch full chat
    
    summary = AIService.summarise_conversation(str(ticket_id), messages)
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