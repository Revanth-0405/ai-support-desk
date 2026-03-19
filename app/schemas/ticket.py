from app.extensions import ma
from app.models.ticket import Ticket

class TicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ticket
        include_fk = True