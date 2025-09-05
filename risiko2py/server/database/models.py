import os
from . import db
# Path to your SQLite database (adjust if needed)
DB_PATH = os.path.join(os.path.dirname(__file__), '../../game.db')
DB_PATH = os.path.abspath(DB_PATH)

if not os.path.exists(DB_PATH):
    # Create the file so SQLAlchemy can use it
    open(DB_PATH, 'a').close()



class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)

class GameState(db.Model):
    __tablename__ = 'game_states'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    players = db.Column(db.Text)  # JSON string: list of players with color/ready
    state = db.Column(db.Text)    # JSON string: dict with systems, fleets, year, etc.
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref=db.backref('game_states', lazy=True))