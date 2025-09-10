from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """Return a salted hash for the given password (werkzeug)."""
    return generate_password_hash(password)

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a provided password against a stored hash."""
    return check_password_hash(stored_password, provided_password)

# Note: JWT handling and request decorators are provided by flask_jwt_extended in routes.
# Keep this module focused on password helpers and small utilities.

def validate_game_state(state) -> bool:
    # Minimal validation hook: ensure dict has expected keys; expand as needed.
    if not isinstance(state, dict):
        return False
    return "systems" in state and "year" in state and "fleets" in state