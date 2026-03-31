import pytest
from app.extensions import db
from app.models.user import User

def test_full_ticket_lifecycle(client, app):
    """E2E Test: Register -> Login -> Create Ticket -> Get Ticket"""
    client.post('/api/auth/register', json={"username": "e2euser", "email": "e2e@test.com", "password": "password123"})
    token = client.post('/api/auth/login', json={"email": "e2e@test.com", "password": "password123"}).get_json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    create_res = client.post('/api/tickets', json={"subject": "System crash", "description": "It is broken"}, headers=headers)
    assert create_res.status_code == 201
    ticket_id = create_res.get_json()['id']
    
    get_res = client.get(f'/api/tickets/{ticket_id}', headers=headers)
    assert get_res.status_code == 200

def test_websocket_connection(app):
    """Test WebSocket infrastructure can successfully broadcast events"""
    from app.extensions import socketio
    ws_client = socketio.test_client(app)
    socketio.emit('system_alert', {'msg': 'Server rebooting'})
    received = ws_client.get_received()
    assert len(received) > 0
    assert received[0]['name'] == 'system_alert'

def test_kb_lifecycle_integration(client, app):
    """Integration 2: Admin creates KB -> Fetches KB list"""
    client.post('/api/auth/register', json={"username": "admin1", "email": "admin1@test.com", "password": "password123"})
    
    with app.app_context():
        user = User.query.filter_by(email="admin1@test.com").first()
        if user:
            user.role = 'admin'
            db.session.commit()

    token = client.post('/api/auth/login', json={"email": "admin1@test.com", "password": "password123"}).get_json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    client.post('/api/kb', json={"title": "Reset", "content": "Click reset.", "category": "general"}, headers=headers)
    list_res = client.get('/api/kb', headers=headers)
    assert list_res.status_code == 200

def test_ticket_update_integration(client, app):
    """Integration 3: Agent role verification on ticket update"""
    client.post('/api/auth/register', json={"username": "agent2", "email": "agent2@test.com", "password": "password123"})
    
    with app.app_context():
        user = User.query.filter_by(email="agent2@test.com").first()
        if user:
            user.role = 'agent'
            db.session.commit()

    token = client.post('/api/auth/login', json={"email": "agent2@test.com", "password": "password123"}).get_json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    res = client.put('/api/tickets/00000000-0000-0000-0000-000000000000', json={"status": "resolved"}, headers=headers)
    assert res.status_code == 404 

def test_ws_join_room_validation(client, app):
    """WebSocket 2: Test join_room security validation"""
    client.post('/api/auth/register', json={"username": "wsuser2", "email": "wsuser2@test.com", "password": "password123"})
    token = client.post('/api/auth/login', json={"email": "wsuser2@test.com", "password": "password123"}).get_json()['access_token']
    from app.extensions import socketio
    ws_client = socketio.test_client(app, query_string=f"token={token}")

    ws_client.emit('join_room', {}) 
    received = ws_client.get_received()
    # FIX: Assert the server safely blocked the request and did not broadcast history
    assert len(received) == 0

def test_ws_send_message_validation(client, app):
    """WebSocket 3: Test send_message security validation"""
    client.post('/api/auth/register', json={"username": "wsuser3", "email": "wsuser3@test.com", "password": "password123"})
    token = client.post('/api/auth/login', json={"email": "wsuser3@test.com", "password": "password123"}).get_json()['access_token']
    from app.extensions import socketio
    ws_client = socketio.test_client(app, query_string=f"token={token}")

    ws_client.emit('send_message', {}) 
    received = ws_client.get_received()
    # FIX: Assert the server safely blocked the request and did not broadcast the message
    assert len(received) == 0

def test_ws_leave_room_validation(client, app):
    """WebSocket 4: Test leave_room fails safely"""
    client.post('/api/auth/register', json={"username": "wsuser4", "email": "wsuser4@test.com", "password": "password123"})
    token = client.post('/api/auth/login', json={"email": "wsuser4@test.com", "password": "password123"}).get_json()['access_token']
    from app.extensions import socketio
    ws_client = socketio.test_client(app, query_string=f"token={token}")

    ws_client.emit('leave_room', {'ticket_id': '00000000-0000-0000-0000-000000000000'})
    received = ws_client.get_received()
    assert len(received) == 0

def test_ws_typing_indicator(client, app):
    """WebSocket 5: Test typing indicator fallback"""
    client.post('/api/auth/register', json={"username": "wsuser5", "email": "wsuser5@test.com", "password": "password123"})
    token = client.post('/api/auth/login', json={"email": "wsuser5@test.com", "password": "password123"}).get_json()['access_token']
    from app.extensions import socketio
    ws_client = socketio.test_client(app, query_string=f"token={token}")

    ws_client.emit('typing', {'ticket_id': '00000000-0000-0000-0000-000000000000'})
    received = ws_client.get_received()
    assert len(received) == 0