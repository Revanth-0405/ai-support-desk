from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.ticket import Ticket
from app.services.ticket_service import TicketService
from app.schemas.ticket import TicketSchema
from app.utils.decorators import role_required
from app.extensions import db

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
        
    ticket = TicketService.create_ticket(data, user_id)
    ticket_data = ticket_schema.dump(ticket)
    
    # PHASE 2: Trigger real-time alert to all agents when a ticket is created
    emit_new_ticket_alert(ticket_data)
    
    return jsonify(ticket_data), 201

@tickets_bp.route('', methods=['GET'])
@jwt_required()
def list_tickets():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    category = request.args.get('category')
    
    query = Ticket.query
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
    
    # Accept optional summary
    if 'summary' in data:
        ticket.ai_summary = data['summary']
        
    db.session.commit()
    
    # Emit ticket_resolved event
    from app.extensions import socketio
    socketio.emit('ticket_resolved', {'ticket_id': str(id)}, room=f"ticket_{id}")
    
    return jsonify({"msg": "Ticket resolved", "ticket": ticket_schema.dump(ticket)}), 200
# PHASE 2: New REST Fallback Endpoint for Chat History
@tickets_bp.route('/<uuid:id>/messages', methods=['GET'])
@jwt_required()
def get_ticket_messages(id):
    ticket = Ticket.query.get_or_404(id)
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Security: Customers can only fetch messages for their own tickets
    if claims.get('role') == 'customer' and str(ticket.customer_id) != user_id:
        return jsonify({"error": "Forbidden", "msg": "You cannot view messages for this ticket"}), 403
        
    messages = ChatService.get_messages_by_ticket(id)
    return jsonify(messages), 200