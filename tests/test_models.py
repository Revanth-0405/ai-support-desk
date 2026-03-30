import pytest
from app.extensions import db
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
    # 1. Create a dummy customer to satisfy the NOT NULL constraint
    customer = User(username="customer1", email="c1@test.com", role="customer")
    customer.set_password("pass")
    db.session.add(customer)
    db.session.flush()

    # 2. Create the ticket and attach the customer_id
    ticket = Ticket(
        ticket_number="TKT-20260101-0001", 
        subject="Test", 
        description="Test desc",
        customer_id=customer.id
    )
    db.session.add(ticket)
    db.session.flush() # Apply defaults
    
    assert ticket.status == 'open'
    assert ticket.priority == 'medium'

def test_kb_article(app):
    # 1. Create a dummy agent to satisfy the NOT NULL constraint
    agent = User(username="agent1", email="a1@test.com", role="agent")
    agent.set_password("pass")
    db.session.add(agent)
    db.session.flush()

    # 2. Create the article and attach the author_id
    article = KnowledgeArticle(
        title="How to login", 
        content="Step 1...", 
        category="general",
        author_id=agent.id
    )
    db.session.add(article)
    db.session.flush() # Apply defaults
    
    assert article.is_published is True