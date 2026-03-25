from flask import request
from flask_socketio import emit, join_room, leave_room, rooms
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
        emit('error', {'msg': 'Missing ticket_id or unauthenticated'}) # ACTION ITEM 11
        return
        
    user_id = user_data['user_id']
    role = user_data['role']
    ticket = db.session.get(Ticket, ticket_id)
    
    if not ticket:
        emit('error', {'msg': 'Ticket not found'})
        return
        
    if role == 'customer' and str(ticket.customer_id) != user_id:
        emit('error', {'msg': 'Unauthorized'})
        return  
        
    # Block agents from joining unassigned tickets they aren't assigned to
    if role == 'agent' and str(ticket.assigned_agent_id) != user_id:
        emit('error', {'msg': 'Unauthorized: Not the assigned agent'})
        return  
        
    room = f"ticket_{ticket_id}"
    join_room(room)
    PresenceService.update_presence(user_id, status='online', active_ticket_id=str(ticket_id))
    messages = ChatService.get_messages_by_ticket(ticket_id, limit=50)
    emit('message_history', messages)

@socketio.on('send_message')
def on_send_message(data):
    ticket_id = data.get('ticket_id')
    content = data.get('content')
    user_data = connected_users.get(request.sid)
    
    room = f"ticket_{ticket_id}"
    
    # Verify sender is actually in the room
    if room not in rooms(request.sid):
        emit('error', {'msg': 'Unauthorized: You have not joined this room'})
        return
        
    message = ChatService.put_message(
        ticket_id=ticket_id, sender_id=user_data['user_id'],
        sender_role=user_data['role'], content=content
    )
    emit('new_message', message, room=room)

@socketio.on('leave_room')
def on_leave(data):
    ticket_id = data.get('ticket_id')
    user_data = connected_users.get(request.sid)
    
    if ticket_id and user_data:
        room = f"ticket_{ticket_id}"
        leave_room(room)
        
        # Clear the active_ticket_id when they leave
        PresenceService.update_presence(user_data['user_id'], status='online', active_ticket_id=None)
        
        emit('user_left', {'user_id': user_data['user_id'], 'ticket_id': ticket_id}, room=room)