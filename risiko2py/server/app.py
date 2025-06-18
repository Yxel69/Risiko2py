import os
import subprocess
import sys
from database import db

# Check dependencies before starting the server
dependency_check_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "../check_dependencies.py"))
subprocess.check_call([sys.executable, dependency_check_script])

from flask import Flask, render_template
from flask_jwt_extended import JWTManager
import json
from datetime import timedelta

app = Flask(__name__)

# Configuration for the database and JWT
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'  # Use SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Change this to a secure key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=180)  # default

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Import blueprints *after* app and db are set up
from routes.game import game_bp
from routes.user import user_bp

# Register blueprints for routes with /api prefix
app.register_blueprint(game_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')

@app.route('/')
def home():
    return "Welcome to the Risiko2Py Game Server!"

@app.route('/games')
def games_list():
    from database.models import GameState
    games = GameState.query.all()
    games_data = []
    for game in games:
        players = json.loads(game.players)
        state = json.loads(game.state)
        year = state.get("year", 1)
        games_data.append({
            "game_id": game.id,
            "players": players,
            "year": year
        })
    return render_template('games.html', games=games_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000, debug=True)  # Run the server on all interfaces


