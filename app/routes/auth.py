from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.user import User
from app.extensions import db
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Input validation
    if not all(k in data for k in ("username", "email", "password")):
        return jsonify({"msg": "Missing required fields"}), 400
        
    if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
        return jsonify({"msg": "Invalid email format"}), 400

    # Uniqueness checks
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already registered"}), 400
    
    user = User(username=data['username'], email=data['email'], role=data.get('role', 'customer'))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201