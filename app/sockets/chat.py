from flask import request
from flask_socketio import emit, join_room, leave_room
from app.extensions import socketio, db
from app.services.chat_service import ChatService
from app.models.ticket import Ticket
from app.sockets.presence import connected_users

@socketio.on('join_room')
def on_join(data):
    """Validates auth, joins room, emits history [cite: 98-99]"""
    ticket_id = data.get('ticket_id')
    user_data = connected_users.get(request.sid)
    
    if not ticket_id or not user_data:
        return
        
    user_id = user_data['user_id']
    role = user_data['role']

    # Security: Validate user is the ticket's customer or assigned agent
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return
        
    if role == 'customer' and str(ticket.customer_id) != user_id:
        return  # Unauthorized
    if role == 'agent' and ticket.assigned_agent_id and str(ticket.assigned_agent_id) != user_id:
        return  # Unauthorized
        
    room = f"ticket_{ticket_id}"
    join_room(room)
    
    # Load history from DynamoDB
    messages = ChatService.get_messages_by_ticket(ticket_id, limit=50)
    emit('message_history', messages)

@socketio.on('send_message')
def on_send_message(data):
    """Stores in DynamoDB and broadcasts [cite: 100]"""
    ticket_id = data.get('ticket_id')
    content = data.get('content')
    user_data = connected_users.get(request.sid)
    
    if not ticket_id or not content or not user_data:
        return
        
    message = ChatService.put_message(
        ticket_id=ticket_id,
        sender_id=user_data['user_id'],
        sender_role=user_data['role'],
        content=content
    )
    
    room = f"ticket_{ticket_id}"
    emit('new_message', message, room=room)

@socketio.on('leave_room')
def on_leave(data):
    """Removes user from room and broadcasts [cite: 101]"""
    ticket_id = data.get('ticket_id')
    user_data = connected_users.get(request.sid)
    
    if ticket_id and user_data:
        room = f"ticket_{ticket_id}"
        leave_room(room)
        emit('user_left', {'user_id': user_data['user_id'], 'ticket_id': ticket_id}, room=room)