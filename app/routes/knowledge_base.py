from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.knowledge_base import KnowledgeArticle
from app.extensions import db

kb_bp = Blueprint('kb', __name__)

@kb_bp.route('', methods=['GET'])
def get_kb():
    search = request.args.get('search')
    query = KnowledgeArticle.query.filter_by(is_published=True)
    
    if search:
        query = query.filter(KnowledgeArticle.title.contains(search))
        
    articles = query.all()
    return jsonify([{"id": str(a.id), "title": a.title} for a in articles]), 200

@kb_bp.route('', methods=['POST'])
@jwt_required()
def create_article():
    # Only Agent/Admin logic here [cite: 77]
    data = request.get_json()
    new_article = KnowledgeArticle(
        title=data['title'],
        content=data['content'],
        category=data['category'],
        author_id=request.headers.get('User-ID') # Placeholder for demo
    )
    db.session.add(new_article)
    db.session.commit()
    return jsonify({"msg": "Article created"}), 201