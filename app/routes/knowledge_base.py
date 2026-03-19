from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.models.knowledge_base import KnowledgeArticle
from app.extensions import db

kb_bp = Blueprint('kb', __name__)

def role_required(roles):
    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"msg": "Admins/Agents only"}), 403
            return fn(*args, **kwargs)
        decorator.__name__ = fn.__name__
        return decorator
    return wrapper

@kb_bp.route('', methods=['GET'])
def list_kb():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = KnowledgeArticle.query.filter_by(is_published=True)
    if search:
        query = query.filter(
            sa.or_(
                KnowledgeArticle.title.ilike(f"%{search}%"),
                KnowledgeArticle.category.ilike(f"%{search}%")
            )
        )
    
    articles = query.paginate(page=page, per_page=10)
    return jsonify({
        "items": [{"id": str(a.id), "title": a.title} for a in articles.items],
        "total": articles.total
    }), 200

@kb_bp.route('/<uuid:id>', methods=['DELETE'])
@role_required(['admin'])
def delete_article(id):
    article = KnowledgeArticle.query.get_or_404(id)
    article.is_published = False  # Soft-delete 
    db.session.commit()
    return jsonify({"msg": "Article soft-deleted"}), 200