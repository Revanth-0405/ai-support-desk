from app.extensions import ma
from app.models.knowledge_base import KnowledgeArticle

class KnowledgeArticleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = KnowledgeArticle
        include_fk = True