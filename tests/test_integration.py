import pytest
from app.extensions import db
from app.models.user import User

def test_full_ticket_lifecycle(client, app):
    """E2E Test: Register -> Login -> Create Ticket -> Get Ticket"""
    # 1. Register
    client.post('/api/auth/register', json={
        "username": "e2ecustomer", "email": "e2e@test.com", "password": "password123"
    })
    
    # 2. Login
    login_res = client.post('/api/auth/login', json={
        "email": "e2e@test.com", "password": "password123"
    })
    token = login_res.get_json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create Ticket
    create_res = client.post('/api/tickets', json={
        "subject": "System crash", "description": "It is broken"
    }, headers=headers)
    assert create_res.status_code == 201
    ticket_id = create_res.get_json()['id']
    
    # 4. Fetch Ticket
    get_res = client.get(f'/api/tickets/{ticket_id}', headers=headers)
    assert get_res.status_code == 200
    assert get_res.get_json()['subject'] == "System crash"

def test_websocket_connection(app):
    """Test WebSocket Auth Rejection"""
    from app.extensions import socketio
    client = socketio.test_client(app)
    # Should disconnect immediately because no JWT token was provided in handshake
    assert client.is_connected() is False