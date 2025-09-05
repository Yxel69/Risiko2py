from requests import Session

class GameRequests:
    def __init__(self, base_url):
        self.session = Session()
        self.base_url = base_url

    def start_game(self, player_owner):
        response = self.session.post(f"{self.base_url}/game/start", json={"owner": player_owner})
        return response.json()

    def save_game(self, game_state):
        response = self.session.post(f"{self.base_url}/game/save", json=game_state)
        return response.json()

    def load_game(self, game_id):
        response = self.session.get(f"{self.base_url}/game/load/{game_id}")
        return response.json()

    def get_game_info(self, game_id):
        response = self.session.get(f"{self.base_url}/game/info/{game_id}")
        return response.json()

    def register_user(self, username, password):
        response = self.session.post(f"{self.base_url}/user/register", json={"username": username, "password": password})
        return response.json()

    def authenticate_user(self, username, password):
        response = self.session.post(f"{self.base_url}/user/authenticate", json={"username": username, "password": password})
        return response.json()