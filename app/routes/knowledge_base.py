from flask import Blueprint, request, jsonify
from app.services.kb_service import KBService
from app.utils.decorators import role_required
import sqlalchemy as sa # Fixed crash here

kb_bp = Blueprint('kb', __name__)

@kb_bp.route('', methods=['GET'])
def list_kb():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Delegate logic to service as reviewer requested
    articles = KBService.get_all_articles(page=page, search_query=search)
    
    return jsonify({
        "items": [{"id": str(a.id), "title": a.title, "category": a.category} for a in articles.items],
        "total": articles.total,
        "page": articles.page,
        "pages": articles.pages
    }), 200

@kb_bp.route('/<uuid:id>', methods=['GET'])
def get_article(id):
    from app.models.knowledge_base import KnowledgeArticle
    article = KnowledgeArticle.query.get_or_404(id)
    return jsonify({"id": str(article.id), "title": article.title, "content": article.content}), 200

@kb_bp.route('', methods=['POST'])
@role_required(['agent', 'admin'])
def create_article():
    data = request.get_json()
    from flask_jwt_extended import get_jwt_identity
    author_id = get_jwt_identity()
    article = KBService.create_article(data, author_id)
    return jsonify({"msg": "Article created", "id": str(article.id)}), 201

@kb_bp.route('/<uuid:id>', methods=['PUT'])
@role_required(['agent', 'admin'])
def update_article(id):
    data = request.get_json()
    article = KBService.update_article(id, data)
    return jsonify({"msg": "Article updated", "id": str(article.id)}), 200

@kb_bp.route('/<uuid:id>', methods=['DELETE'])
@role_required(['admin', 'agent']) # Fixed RBAC for delete
def delete_article(id):
    KBService.soft_delete_article(id)
    return jsonify({"msg": "Article soft-deleted"}), 200