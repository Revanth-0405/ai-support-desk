import uuid
from datetime import datetime
from app.extensions import db

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Format: TKT-YYYYMMDD-XXXX 
    ticket_number = db.Column(db.String(25), unique=True, nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Enums per spec 
    status = db.Column(db.Enum('open', 'in_progress', 'waiting_on_customer', 'resolved', 'closed', name='ticket_status'), default='open')
    priority = db.Column(db.Enum('low', 'medium', 'high', 'urgent', name='ticket_priority'), default='medium')
    category = db.Column(db.String(50), nullable=True) # Populated by AI later 
    
    customer_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    assigned_agent_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    
    ai_summary = db.Column(db.Text, nullable=True) # Populated by AI on resolution 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)