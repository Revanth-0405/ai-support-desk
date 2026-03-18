from app.extensions import db
from app.models.knowledge_base import KnowledgeArticle

class KBService:
    @staticmethod
    def get_articles(page=1, per_page=10, search_query=None):
        """Paginated list with search by title or tags [cite: 76]"""
        query = KnowledgeArticle.query.filter_by(is_published=True)
        
        if search_query:
            query = query.filter(
                (KnowledgeArticle.title.ilike(f"%{search_query}%")) |
                (KnowledgeArticle.tags.contains([search_query]))
            )
            
        return query.paginate(page=page, per_page=per_page)

    @staticmethod
    def soft_delete_article(article_id):
        """Admin-only soft delete """
        article = KnowledgeArticle.query.get_or_404(article_id)
        article.is_published = False
        db.session.commit()
        return True