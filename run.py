from app import create_app, socketio

app = create_app()

with app.app_context():
    from app.services.chat_service import ChatService
    ChatService.initialize_tables()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)