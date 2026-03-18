from datetime import datetime
from app.extensions import db
from app.models.ticket import Ticket
import random

class TicketService:
    @staticmethod
    def generate_ticket_number():
        """Generates format: TKT-YYYYMMDD-XXXX"""
        date_str = datetime.utcnow().strftime('%Y%m%d')
        random_suffix = ''.join(random.choices('0123456789', k=4))
        return f"TKT-{date_str}-{random_suffix}"

    @staticmethod
    def create_ticket(data, customer_id):
        ticket_number = TicketService.generate_ticket_number()
        new_ticket = Ticket(
            ticket_number=ticket_number,
            subject=data['subject'],
            description=data['description'],
            customer_id=customer_id
        )
        db.session.add(new_ticket)
        db.session.commit()
        return new_ticket