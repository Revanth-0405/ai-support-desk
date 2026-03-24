from app.extensions import socketio
# Import handlers to ensure they are registered with SocketIO
from app.sockets import presence, chat, notifications