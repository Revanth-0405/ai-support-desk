from flask import request, Blueprint, jsonify
from flask_socketio import emit, join_room, disconnect
from flask_jwt_extended import decode_token
from app.extensions import socketio
from app.services.presence_service import PresenceService
from app.utils.decorators import role_required

# Store connection state in memory for chat.py to access
connected_users = {}

# REST Endpoint (Housed here to respect the strict file structure)
presence_bp = Blueprint('presence', __name__)

@presence_bp.route('/agents', methods=['GET'])
@role_required(['agent', 'admin'])
def list_agents_presence():
    from app.models.user import User
    agents = User.query.filter(User.role.in_(['agent', 'admin'])).all()
    agent_ids = [str(a.id) for a in agents]
    presence_data = PresenceService.get_agents_presence(agent_ids)
    return jsonify(presence_data), 200

@socketio.on('connect')
def handle_connect(auth):
    """Requires JWT token in handshake [cite: 221]"""
    token = auth.get('token') if auth else request.args.get('token')
    if not token:
        return False  # Rejects unauthenticated connection [cite: 222]
        
    try:
        decoded = decode_token(token)
        user_id = decoded['sub']
        role = decoded.get('role', 'customer')
        
        # Track user session
        connected_users[request.sid] = {'user_id': user_id, 'role': role}
        
        # If agent/admin, add to broadcast room for new ticket alerts [cite: 114]
        if role in ['agent', 'admin']:
            join_room('agents_room')
            
        PresenceService.update_presence(user_id, 'online', socket_id=request.sid)
        emit('presence_update', {'user_id': user_id, 'status': 'online'}, broadcast=True)
    except Exception as e:
        return False

@socketio.on('disconnect')
def handle_disconnect():
    user_data = connected_users.pop(request.sid, None)
    if user_data:
        PresenceService.update_presence(user_data['user_id'], 'offline', active_ticket_id=None)
        emit('presence_update', {'user_id': user_data['user_id'], 'status': 'offline'}, broadcast=True)
@socketio.on('typing')
def handle_typing(data):
    """Broadcasts typing indicator [cite: 110]"""
    ticket_id = data.get('ticket_id')
    user_data = connected_users.get(request.sid)
    if ticket_id and user_data:
        room = f"ticket_{ticket_id}"
        emit('user_typing', {'user_id': user_data['user_id'], 'ticket_id': ticket_id}, room=room, include_self=False)