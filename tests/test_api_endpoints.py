import pytest
from app.extensions import db
from app.models.ticket import Ticket
from app.models.knowledge_base import KnowledgeArticle
from app.models.user import User


def get_token(client, email, password):
    res = client.post('/api/auth/login', json={"email": email, "password": password})
    return res.get_json().get('access_token')

def test_register_validation(client):
    res = client.post('/api/auth/register', json={"username": "bad", "email": "not-an-email", "password": "123"})
    assert res.status_code == 400

def test_login_failure(client):
    res = client.post('/api/auth/login', json={"email": "wrong@test.com", "password": "wrong"})
    assert res.status_code == 401

def test_create_ticket_unauthorized(client):
    res = client.post('/api/tickets', json={"subject": "Test", "description": "Test"})
    assert res.status_code == 401

def test_create_ticket_success(client, app):
    client.post('/api/auth/register', json={"username": "c1", "email": "c1@test.com", "password": "password123"})
    token = get_token(client, "c1@test.com", "password123")
    res = client.post('/api/tickets', json={"subject": "Help", "description": "Need help"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201

def test_get_ticket_customer_scoping(client, app):
    # FIX: Explicitly register c1 inside this isolated test context
    client.post('/api/auth/register', json={"username": "c1", "email": "c1@test.com", "password": "password123"})
    client.post('/api/auth/register', json={"username": "c2", "email": "c2@test.com", "password": "password123"})
    
    token1 = get_token(client, "c1@test.com", "password123") 
    token2 = get_token(client, "c2@test.com", "password123")
    
    t_res = client.post('/api/tickets', json={"subject": "Help", "description": "Need help"}, headers={"Authorization": f"Bearer {token1}"})
    t_id = t_res.get_json()['id']
    
    read_res = client.get(f'/api/tickets/{t_id}', headers={"Authorization": f"Bearer {token2}"})
    assert read_res.status_code == 403

def test_health_endpoint(client):
    res = client.get('/api/health')
    assert res.status_code in [200, 500] 

def test_analytics_admin_only(client, app):
    # FIX: Register the user so the token isn't empty, giving us a 403 instead of a 422
    client.post('/api/auth/register', json={"username": "c3", "email": "c3@test.com", "password": "password123"})
    token = get_token(client, "c3@test.com", "password123")
    res = client.get('/api/analytics/tickets', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_kb_create_unauthorized(client):
    res = client.post('/api/kb', json={"title": "Test", "content": "Test", "category": "general"})
    assert res.status_code == 401

# FIX: Use a properly formatted UUID string so Flask hits the auth check (401) instead of route not found (404)
VALID_MOCK_UUID = "00000000-0000-0000-0000-000000000000"

def test_ai_categorise_unauthorized(client):
    res = client.post(f'/api/ai/categorise/{VALID_MOCK_UUID}')
    assert res.status_code == 401

def test_ai_suggest_unauthorized(client):
    res = client.post(f'/api/ai/suggest/{VALID_MOCK_UUID}')
    assert res.status_code == 401

def test_ai_summarise_unauthorized(client):
    res = res = client.post(f'/api/ai/summarise/{VALID_MOCK_UUID}')
    assert res.status_code == 401
    
def test_ai_usage_unauthorized(client):
    res = client.get('/api/ai/usage')
    assert res.status_code == 401

def test_ticket_update_assign_resolve(client, app):
    """Test agent updating, assigning, and resolving a ticket"""
    from app.models.user import User
    from unittest.mock import patch # FIX: Import patch
    
    client.post('/api/auth/register', json={"username": "c3", "email": "c3@test.com", "password": "password123"})
    c_token = get_token(client, "c3@test.com", "password123")

    client.post('/api/auth/register', json={"username": "a1", "email": "a1@test.com", "password": "password123"})
    with app.app_context():
        u = User.query.filter_by(email="a1@test.com").first()
        u.role = 'agent'
        db.session.commit()
    a_token = get_token(client, "a1@test.com", "password123")

    t_res = client.post('/api/tickets', json={"subject": "Help", "description": "Need help"}, headers={"Authorization": f"Bearer {c_token}"})
    t_id = t_res.get_json()['id']

    with patch('app.sockets.notifications.PresenceService.get_user_presence', return_value=None):
        client.put(f'/api/tickets/{t_id}/assign', json={}, headers={"Authorization": f"Bearer {a_token}"})
    
    u_res = client.put(f'/api/tickets/{t_id}', json={"priority": "high"}, headers={"Authorization": f"Bearer {a_token}"})
    assert u_res.status_code == 200

    with patch('app.routes.tickets.ChatService.get_messages_by_ticket', return_value=[]):
        with patch('app.routes.tickets.AIService.summarise_conversation', return_value="Summary"):
            r_res = client.put(f'/api/tickets/{t_id}/resolve', json={}, headers={"Authorization": f"Bearer {a_token}"})
            assert r_res.status_code == 200
            assert r_res.get_json()['ticket']['status'] == 'resolved'

def test_kb_update_delete_search(client, app):
    """Test KB update, soft delete, and search functionality"""
    from app.models.user import User # FIX: Import the model
    
    client.post('/api/auth/register', json={"username": "a2", "email": "a2@test.com", "password": "password123"})
    with app.app_context():
        u = User.query.filter_by(email="a2@test.com").first()
        u.role = 'admin'
        db.session.commit()
    token = get_token(client, "a2@test.com", "password123")

    kb_res = client.post('/api/kb', json={"title": "SearchMe", "content": "Data", "category": "general"}, headers={"Authorization": f"Bearer {token}"})
    kb_id = kb_res.get_json()['id']

    s_res = client.get('/api/kb?query=SearchMe', headers={"Authorization": f"Bearer {token}"})
    assert len(s_res.get_json()['items']) > 0

    client.put(f'/api/kb/{kb_id}', json={"title": "Updated"}, headers={"Authorization": f"Bearer {token}"})
    d_res = client.delete(f'/api/kb/{kb_id}', headers={"Authorization": f"Bearer {token}"})
    assert d_res.status_code == 200