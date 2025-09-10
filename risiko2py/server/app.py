import os
import subprocess
import sys
from database import db

from flask import Flask, render_template
from flask_jwt_extended import JWTManager
import json
from datetime import timedelta
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from flask_talisman import Talisman

# Read configuration from environment with sane defaults
JWT_SECRET = os.environ.get("RISIKO_JWT_SECRET", os.environ.get("JWT_SECRET_KEY", "please_change_me_in_prod"))
ALLOWED_ORIGINS = os.environ.get("RISIKO_ALLOWED_ORIGINS")  # comma separated or empty => not restrictive
PREFERRED_SCHEME = os.environ.get("RISIKO_PREFERRED_SCHEME", "https")
JWT_EXPIRES_MINUTES = int(os.environ.get("RISIKO_JWT_EXPIRES_MINUTES", "180"))

app = Flask(__name__)

# Configuration for the database and JWT
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///game.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=JWT_EXPIRES_MINUTES)
app.config['PREFERRED_URL_SCHEME'] = PREFERRED_SCHEME

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Trusted proxy headers (nginx) so url_for, request.scheme etc are correct
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# Security headers / HTTPS enforcement. Talisman will set HSTS and basic CSP.
Talisman(app, content_security_policy={"default-src": "'self'"},
         force_https=True, strict_transport_security=True)

# CORS: if ALLOWED_ORIGINS set, restrict access; otherwise leave off (or enable as needed)
if ALLOWED_ORIGINS:
    allowed = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": allowed}})
else:
    # Optional: enable CORS for api endpoints in development
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

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
    run_check = input("Check Dependencies (y/n): ").strip().lower()
    if run_check == 'y':
        dependency_check_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "../check_dependencies.py"))
        subprocess.check_call([sys.executable, dependency_check_script])
    with app.app_context():
        db.create_all()
    # Development run; for production use a real WSGI server (gunicorn/uwsgi) behind nginx.
    app.run(host='127.0.0.1', port=int(os.environ.get("RISIKO_DEV_PORT", "5000")), debug=False)


