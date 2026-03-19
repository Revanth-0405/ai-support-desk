from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.ticket import Ticket
from app.services.ticket_service import TicketService
from app.extensions import db

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('', methods=['POST'])
@jwt_required()
def create_ticket():
    data = request.get_json()
    user_id = get_jwt_identity()
    # Basic validation for subject/description
    if not data.get('subject') or not data.get('description'):
        return jsonify({"msg": "Missing required fields"}), 400
    
    ticket = TicketService.create_ticket(data, user_id)
    return jsonify({"ticket_number": ticket.ticket_number, "id": str(ticket.id)}), 201

@tickets_bp.route('', methods=['GET'])
@jwt_required()
def list_tickets():
    # Pagination and filtering logic
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    
    query = Ticket.query
    if status:
        query = query.filter_by(status=status)
        
    tickets = query.paginate(page=page, per_page=10)
    return jsonify([{"id": str(t.id), "number": t.ticket_number} for t in tickets.items]), 200

@tickets_bp.route('/<uuid:id>/resolve', methods=['PUT'])
@jwt_required()
def resolve_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    # Check if user is agent/admin (Phase 1 logic)
    ticket.status = 'resolved'
    db.session.commit()
    return jsonify({"msg": "Ticket resolved"}), 200