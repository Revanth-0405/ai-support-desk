from app.extensions import socketio
from app.services.presence_service import PresenceService

def emit_new_ticket_alert(ticket_data):
    """Broadcasts [cite: 114] to the agents_room created in presence.py"""
    socketio.emit('new_ticket_alert', ticket_data, room='agents_room')

def emit_ticket_assigned(agent_id, ticket_data):
    """Emits [cite: 115] specifically to the assigned agent's socket"""
    presence = PresenceService.get_user_presence(agent_id)
    if presence and presence.get('socket_id'):
        socketio.emit('ticket_assigned', ticket_data, to=presence['socket_id'])