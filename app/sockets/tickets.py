from app.sockets.notifications import emit_new_ticket_alert, emit_ticket_assigned
from app.services.chat_service import ChatService

# Modify your existing create_ticket to emit the alert:
@tickets_bp.route('', methods=['POST'])
@jwt_required()
def create_ticket():
    # ... (existing logic) ...
    ticket = TicketService.create_ticket(data, user_id)
    ticket_data = ticket_schema.dump(ticket)
    
    # Trigger Phase 2 Notification
    emit_new_ticket_alert(ticket_data)
    
    return jsonify(ticket_data), 201

# Modify your existing assign_ticket to emit the assignment:
@tickets_bp.route('/<uuid:id>/assign', methods=['PUT'])
@role_required(['agent', 'admin'])
def assign_ticket(id):
    # ... (existing logic) ...
    ticket.assigned_agent_id = data.get('agent_id', get_jwt_identity())
    db.session.commit()
    ticket_data = ticket_schema.dump(ticket)
    
    # Trigger Phase 2 Notification
    emit_ticket_assigned(str(ticket.assigned_agent_id), ticket_data)
    
    return jsonify({"msg": "Ticket assigned", "ticket": ticket_data}), 200

# Add the New REST Fallback Endpoint 
@tickets_bp.route('/<uuid:id>/messages', methods=['GET'])
@jwt_required()
def get_ticket_messages(id):
    ticket = Ticket.query.get_or_404(id)
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Auth check
    if claims.get('role') == 'customer' and str(ticket.customer_id) != user_id:
        return jsonify({"error": "Forbidden"}), 403
        
    messages = ChatService.get_messages_by_ticket(id)
    return jsonify(messages), 200