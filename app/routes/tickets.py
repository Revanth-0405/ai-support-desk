from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.ticket import Ticket
from app.services.ticket_service import TicketService
from app.schemas.ticket import TicketSchema
from app.utils.decorators import role_required
from app.extensions import db
from app.services.ai_service import AIService

# Phase 2 Imports for Chat and Notifications
from app.sockets.notifications import emit_new_ticket_alert, emit_ticket_assigned
from app.services.chat_service import ChatService

tickets_bp = Blueprint('tickets', __name__)
ticket_schema = TicketSchema()
tickets_schema = TicketSchema(many=True)

@tickets_bp.route('', methods=['POST'])
@jwt_required()
def create_ticket():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    if not data.get('subject') or not data.get('description'):
        return jsonify({"error": "Bad Request", "message": "Missing required fields"}), 400
        
    # Transactional Creation 
    ticket = TicketService.create_ticket(data, user_id)
    
    # Try AI Categorisation (Graceful Degradation)
    try:
        ai_result = AIService.categorise_ticket(str(ticket.id), ticket.subject, ticket.description)
        if ai_result:
            ticket.category = ai_result.get('category')
            ticket.priority = ai_result.get('priority', ticket.priority)
            db.session.commit() # Save AI enhancements
    except Exception as e:
        # If AI fails, ticket remains created with default priority/null category
        db.session.rollback() 
    
    ticket_data = ticket_schema.dump(ticket)
    emit_new_ticket_alert(ticket_data)
    
    return jsonify(ticket_data), 201

@tickets_bp.route('', methods=['GET'])
@jwt_required()
def list_tickets():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    category = request.args.get('category')
    
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    query = Ticket.query
    
    # Scope tickets so customers only see their own
    if claims.get('role') == 'customer':
        query = query.filter_by(customer_id=user_id)
        
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if category:
        query = query.filter_by(category=category)
        
    tickets = query.paginate(page=page, per_page=10, error_out=False)
    
    return jsonify({
        "items": tickets_schema.dump(tickets.items),
        "total": tickets.total,
        "page": tickets.page,
        "pages": tickets.pages
    }), 200

@tickets_bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    return jsonify(ticket_schema.dump(ticket)), 200

@tickets_bp.route('/<uuid:id>', methods=['PUT'])
@role_required(['agent', 'admin'])
def update_ticket(id):
    data = request.get_json()
    ticket = Ticket.query.get_or_404(id)
    
    if 'status' in data:
        ticket.status = data['status']
    if 'priority' in data:
        ticket.priority = data['priority']
        
    db.session.commit()
    return jsonify({"msg": "Ticket updated", "ticket": ticket_schema.dump(ticket)}), 200

@tickets_bp.route('/<uuid:id>/assign', methods=['PUT'])
@role_required(['agent', 'admin'])
def assign_ticket(id):
    data = request.get_json() or {}
    ticket = Ticket.query.get_or_404(id)
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    target_agent_id = data.get('agent_id', user_id)

    # RBAC Logic
    if claims.get('role') == 'agent':
        if str(target_agent_id) != str(user_id):
            return jsonify({"error": "Forbidden", "msg": "Agents can only self-assign"}), 403
        if ticket.assigned_agent_id is not None and str(ticket.assigned_agent_id) != str(user_id):
            return jsonify({"error": "Forbidden", "msg": "Ticket already assigned"}), 403

    ticket.assigned_agent_id = target_agent_id
    db.session.commit()
    
    ticket_data = ticket_schema.dump(ticket)
    emit_ticket_assigned(str(ticket.assigned_agent_id), ticket_data)
    return jsonify({"msg": "Ticket assigned", "ticket": ticket_data}), 200

@tickets_bp.route('/<uuid:id>/resolve', methods=['PUT'])
@role_required(['agent', 'admin'])
def resolve_ticket(id):
    data = request.get_json() or {}
    ticket = Ticket.query.get_or_404(id)
    ticket.status = 'resolved'
    
    # If summary is provided manually, use it. Otherwise, use AI.
    if 'summary' in data:
        ticket.ai_summary = data['summary']
    else:
        # Fetch full chat history from DynamoDB and call AI Summarise 
        messages = ChatService.get_messages_by_ticket(id, limit=200)
        summary = AIService.summarise_conversation(str(id), messages)
        if summary:
            ticket.ai_summary = summary
            
    db.session.commit()
    
    # Emit resolution event [cite: 149-150]
    from app.extensions import socketio
    socketio.emit('ticket_resolved', {'ticket_id': str(id)}, room=f"ticket_{id}")
    
    return jsonify({"msg": "Ticket resolved", "ticket": ticket_schema.dump(ticket)}), 200

# PHASE 2: New REST Fallback Endpoint for Chat History
@tickets_bp.route('/<uuid:id>', methods=['GET'])
@jwt_required()
def get_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    claims = get_jwt()
    
    # FIX: Customer scoping
    if claims.get('role') == 'customer' and str(ticket.customer_id) != get_jwt_identity():
        return jsonify({"error": "Forbidden"}), 403
        
    return jsonify(ticket_schema.dump(ticket)), 200

@tickets_bp.route('', methods=['POST'])
@jwt_required()
def create_ticket():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    if not data.get('subject') or not data.get('description'):
        return jsonify({"error": "Bad Request", "message": "Missing required fields"}), 400
        
    ticket = TicketService.create_ticket(data, user_id)
    db.session.commit() # Save ticket first
    
    # FIX: Use nested transaction for partial failure resiliency
    try:
        with db.session.begin_nested():
            ai_result = AIService.categorise_ticket(str(ticket.id), ticket.subject, ticket.description)
            if ai_result:
                ticket.category = ai_result.get('category')
                ticket.priority = ai_result.get('priority', ticket.priority)
        db.session.commit()
    except Exception:
        db.session.rollback() # Roll back only the AI update
    
    ticket_data = ticket_schema.dump(ticket)
    emit_new_ticket_alert(ticket_data)
    
    return jsonify(ticket_data), 201