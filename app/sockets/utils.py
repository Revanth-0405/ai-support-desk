from flask import request
from flask_socketio import ConnectionRefusedError
from flask_jwt_extended import decode_token

# Store active socket sessions mapping request.sid to user_id and role
active_sessions = {}

def authenticate_socket(auth_payload):
    """
    Validates the JWT token passed during the SocketIO handshake.
    Rejects unauthenticated connections per spec .
    """
    token = None
    if auth_payload and 'token' in auth_payload:
        token = auth_payload['token']
    elif request.args.get('token'):
        token = request.args.get('token')

    if not token:
        raise ConnectionRefusedError('Unauthorized: Token missing')

    try:
        decoded = decode_token(token)
        return decoded['sub'], decoded.get('role', 'customer')
    except Exception as e:
        raise ConnectionRefusedError(f'Unauthorized: Invalid token ({str(e)})')