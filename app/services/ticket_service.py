from datetime import datetime, timezone
from app.extensions import db
from app.models.ticket import Ticket

class TicketService:
    @staticmethod
    def generate_ticket_number():
        now = datetime.now(timezone.utc)
        date_str = now.strftime('%Y%m%d')
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Use SELECT ... FOR UPDATE to lock the rows and prevent race conditions [cite: 56]
        count = db.session.query(Ticket).filter(Ticket.created_at >= today_start).with_for_update().count()
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