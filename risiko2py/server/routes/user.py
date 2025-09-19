from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database.models import GameState, User
from utils.security import hash_password, verify_password, create_game_state, validate_game_state
from database import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Username and password are required."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists."}), 400

    hashed_password = hash_password(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User registered successfully."}), 201

@user_bp.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(user.password, password):
        return jsonify({"msg": "Invalid credentials."}), 401

    # Return integer identity so get_jwt_identity() yields an int
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

@user_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user:
        return jsonify({"username": user.username}), 200

    return jsonify({"msg": "User not found."}), 404

@user_bp.route('/user/list', methods=['GET'])
@jwt_required()
def list_users():
    """Returns a list of registered users."""
    q = (request.args.get('q') or "").strip()
    query = User.query
    if q:
        query = query.filter(User.username.ilike(f"%{q}%"))
    users = query.limit(200).all()
    return jsonify([{"id": u.id, "username": u.username} for u in users]), 200