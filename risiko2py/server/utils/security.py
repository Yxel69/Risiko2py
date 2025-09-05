from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from database.models import GameState

# Secret key for JWT encoding and decoding
SECRET_KEY = "your_secret_key_here"

def hash_password(password):
    return generate_password_hash(password)

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)

def generate_token(user_id):
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, SECRET_KEY, algorithm='HS256')
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = data['user_id']
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def create_game_state(players):
    # TODO: Implement actual game state creation logic
    # For now, just return a dummy object or raise NotImplementedError
    # Example: create a new GameState instance
    state_data = {"players": players, "state": {}}  # Adjust as needed
    game_state = GameState(user_id=1, state_data=state_data)  # user_id should be set properly
    return game_state

def validate_game_state(state):
    # TODO: Implement actual validation logic
    return True