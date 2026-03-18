from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.user import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "User exists"}), 400
    
    user = User(username=data['username'], email=data['email'], role=data.get('role', 'customer'))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        # We include the role in the access token for RBAC checks
        access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Bad credentials"}), 401