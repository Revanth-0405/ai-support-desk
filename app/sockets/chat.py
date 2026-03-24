from flask import request
from flask_socketio import emit, join_room, leave_room
from app.extensions import socketio, db
from app.services.chat_service import ChatService
from app.services.presence_service import PresenceService # ADDED THIS IMPORT
from app.models.ticket import Ticket
from app.sockets.presence import connected_users

@socketio.on('join_room')
def on_join(data):
    ticket_id = data.get('ticket_id')
    user_data = connected_users.get(request.sid)
    
    if not ticket_id or not user_data:
        return
        
    user_id = user_data['user_id']
    role = user_data['role']

    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return
        
    if role == 'customer' and str(ticket.customer_id) != user_id:
        return  
    if role == 'agent' and ticket.assigned_agent_id and str(ticket.assigned_agent_id) != user_id:
        return  
        
    room = f"ticket_{ticket_id}"
    join_room(room)
    
    # NEW: Update DynamoDB to show which ticket room the user is actively viewing
    PresenceService.update_presence(user_id, status='online', active_ticket_id=str(ticket_id))
    
    messages = ChatService.get_messages_by_ticket(ticket_id, limit=50)
    emit('message_history', messages)

@socketio.on('send_message')
def on_send_message(data):
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
    ticket_id = data.get('ticket_id')
    user_data = connected_users.get(request.sid)
    
    if ticket_id and user_data:
        room = f"ticket_{ticket_id}"
        leave_room(room)
        
        # NEW: Clear the active_ticket_id when they leave
        PresenceService.update_presence(user_data['user_id'], status='online', active_ticket_id=None)
        
        emit('user_left', {'user_id': user_data['user_id'], 'ticket_id': ticket_id}, room=room)