from app.models.user import User
from app.models.ticket import Ticket
from app.models.knowledge_base import KnowledgeArticle

# Expose models for SQLAlchemy/Alembic discovery
__all__ = ['User', 'Ticket', 'KnowledgeArticle']