from datetime import datetime
from app.extensions import db
from app.models.ticket import Ticket
import sqlalchemy as sa

class TicketService:
    @staticmethod
    def generate_ticket_number():
        date_str = datetime.utcnow().strftime('%Y%m%d')
        # Count tickets created today to increment XXXX
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        count = db.session.query(Ticket).filter(Ticket.created_at >= today_start).count()
        return f"TKT-{date_str}-{str(count + 1).zfill(4)}"

    @staticmethod
    def create_ticket(data, customer_id):
        new_ticket = Ticket(
            ticket_number=TicketService.generate_ticket_number(),
            subject=data['subject'],
            description=data['description'],
            customer_id=customer_id
        )
        db.session.add(new_ticket)
        db.session.commit()
        return new_ticket