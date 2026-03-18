import uuid
from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models.ticket import Ticket
from app.utils.errors import ValidationError

class TicketService:
    @staticmethod
    def generate_ticket_number():
        """Generates format: TKT-YYYYMMDD-XXXX [cite: 70]"""
        today_str = datetime.utcnow().strftime('%Y%m%d')
        prefix = f"TKT-{today_str}-"
        
        # Count tickets created today to determine the suffix
        count = db.session.query(func.count(Ticket.id)).filter(
            Ticket.ticket_number.like(f"{prefix}%")
        ).scalar()
        
        return f"{prefix}{(count + 1):04d}"

    @staticmethod
    def create_ticket(data, customer_id):
        """Atomic transaction for ticket creation [cite: 225]"""
        new_ticket = Ticket(
            id=uuid.uuid4(),
            ticket_number=TicketService.generate_ticket_number(),
            subject=data['subject'],
            description=data['description'],
            customer_id=customer_id,
            status='open',
            priority=data.get('priority', 'medium')
        )
        
        db.session.add(new_ticket)
        db.session.commit()
        return new_ticket

    @staticmethod
    def assign_ticket(ticket_id, agent_id, user_role):
        """Logic for agent self-assignment or admin assignment [cite: 78, 79]"""
        ticket = Ticket.query.get_or_404(ticket_id)
        
        if user_role not in ['agent', 'admin']:
            raise ValidationError("Unauthorized to assign tickets")
            
        ticket.assigned_agent_id = agent_id
        ticket.status = 'in_progress'
        db.session.commit()
        return ticket