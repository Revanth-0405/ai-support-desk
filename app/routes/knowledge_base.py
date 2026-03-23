from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.services.kb_service import KBService
from app.models.knowledge_base import KnowledgeArticle
from app.schemas.knowledge_base import KnowledgeArticleSchema
from app.utils.decorators import role_required
import sqlalchemy as sa

kb_bp = Blueprint('kb', __name__)
kb_schema = KnowledgeArticleSchema()
kbs_schema = KnowledgeArticleSchema(many=True)

@kb_bp.route('', methods=['GET'])
def list_kb():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    articles = KBService.get_all_articles(page=page, search_query=search)
    
    return jsonify({
        "items": kbs_schema.dump(articles.items),
        "total": articles.total,
        "page": articles.page,
        "pages": articles.pages
    }), 200

@kb_bp.route('/<uuid:id>', methods=['GET'])
def get_article(id):
    article = KnowledgeArticle.query.get_or_404(id)
    # Ensure soft-deleted articles are not directly accessible
    if not article.is_published:
        return jsonify({"error": "Not Found"}), 404
    return jsonify(kb_schema.dump(article)), 200

@kb_bp.route('', methods=['POST'])
@role_required(['agent', 'admin'])
def create_article():
    data = request.get_json()
    if not all(k in data for k in ("title", "content", "category")):
        return jsonify({"error": "Bad Request", "message": "Missing required fields"}), 400
        
    author_id = get_jwt_identity()
    article = KBService.create_article(data, author_id)
    return jsonify({"msg": "Article created", "article": kb_schema.dump(article)}), 201

@kb_bp.route('/<uuid:id>', methods=['PUT'])
@role_required(['agent', 'admin'])
def update_article(id):
    data = request.get_json()
    article = KBService.update_article(id, data)
    return jsonify({"msg": "Article updated", "article": kb_schema.dump(article)}), 200

@kb_bp.route('/<uuid:id>', methods=['DELETE'])
@role_required(['admin']) # Strictly Admin as per PDF Page 7 table 
def delete_article(id):
    KBService.soft_delete_article(id)
    return jsonify({"msg": "Article soft-deleted"}), 200