from app.extensions import db
from app.models.knowledge_base import KnowledgeArticle
import sqlalchemy as sa

class KBService:
    @staticmethod
    def get_all_articles(page=1, per_page=10, search_query=None):
        """
        List KB articles with pagination and search by title, category, or tags.
        Filters for is_published=True to exclude soft-deleted items.
        """
        query = KnowledgeArticle.query.filter_by(is_published=True)
        
        if search_query:
            # Search across title, category, and tags 
            search_filter = sa.or_(
                KnowledgeArticle.title.ilike(f"%{search_query}%"),
                KnowledgeArticle.category.ilike(f"%{search_query}%"),
                KnowledgeArticle.tags.cast(sa.String).ilike(f"%{search_query}%")
            )
            query = query.filter(search_filter)
            
        return query.order_by(KnowledgeArticle.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def create_article(data, author_id):
        """Create a new KB article."""
        new_article = KnowledgeArticle(
            title=data['title'],
            content=data['content'],
            category=data['category'],
            tags=data.get('tags', []),
            author_id=author_id
        )
        db.session.add(new_article)
        db.session.commit()
        return new_article

    @staticmethod
    def update_article(article_id, data):
        """Update an existing KB article."""
        article = KnowledgeArticle.query.get_or_404(article_id)
        article.title = data.get('title', article.title)
        article.content = data.get('content', article.content)
        article.category = data.get('category', article.category)
        article.tags = data.get('tags', article.tags)
        db.session.commit()
        return article

    @staticmethod
    def soft_delete_article(article_id):
        """
        Performs a soft-delete by setting is_published to False.
        Only Admin users should trigger this via the route.
        """
        article = KnowledgeArticle.query.get_or_404(article_id)
        article.is_published = False
        db.session.commit()
        return True