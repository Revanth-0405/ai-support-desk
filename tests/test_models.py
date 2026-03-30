import pytest
from app.models.user import User
from app.models.ticket import Ticket
from app.models.knowledge_base import KnowledgeArticle

def test_user_creation(app):
    user = User(username="testuser", email="test@test.com", role="customer")
    user.set_password("password123")
    assert user.username == "testuser"
    assert user.role == "customer"
    assert user.check_password("password123") is True
    assert user.check_password("wrong") is False

def test_ticket_model(app):
    ticket = Ticket(ticket_number="TKT-20260101-0001", subject="Test", description="Test desc")
    assert ticket.status == 'open'
    assert ticket.priority == 'medium'

def test_kb_article(app):
    article = KnowledgeArticle(title="How to login", content="Step 1...", category="general")
    assert article.is_published is True