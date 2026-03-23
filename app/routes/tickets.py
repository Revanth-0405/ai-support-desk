from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.ticket import Ticket
from app.services.ticket_service import TicketService
from app.schemas.ticket import TicketSchema
from app.utils.decorators import role_required
from app.extensions import db

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
    return jsonify(ticket_schema.dump(ticket)), 201

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
    # Agent self-assigns if agent_id is not provided
    ticket.assigned_agent_id = data.get('agent_id', get_jwt_identity())
    db.session.commit()
    return jsonify({"msg": "Ticket assigned", "ticket": ticket_schema.dump(ticket)}), 200

@tickets_bp.route('/<uuid:id>/resolve', methods=['PUT'])
@role_required(['agent', 'admin'])
def resolve_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    ticket.status = 'resolved'
    # ai_summary will be handled here in Phase 3 [cite: 145-148]
    db.session.commit()
    return jsonify({"msg": "Ticket resolved", "ticket": ticket_schema.dump(ticket)}), 200