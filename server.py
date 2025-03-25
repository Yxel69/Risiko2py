import socket
import threading
import os
import json
from datetime import datetime
import uuid
import random

HOST = '0.0.0.0'
PORT = 9999

# Global dictionary for game sessions.
# Each session holds a game_state dictionary.
game_sessions = {}  # session_id -> game_state

def random_color():
    return "#{:06X}".format(random.randint(0, 0xFFFFFF))

def new_game_state(planet_count, creator, player_name):
    """Return a new game state dictionary. The creator is assigned a unique color."""
    state = {
        "session_id": str(uuid.uuid4()),
        "planet_count": planet_count,
        "year": 1,
        "creator": creator,
        "players": [{ "name": player_name, "color": random_color() }],
        "systems": {},
    }
    for sys_id in range(1, planet_count+1):
        state["systems"][sys_id] = {
            "owner": None,
            "current_ships": 0,
            "ship_production": 0,
            "defense_factor": 0,
            "grid_pos": (0,0),
            "color": None  # Will be set when the system is assigned.
        }
    return state

def assign_starting_planet(state, player_name):
    """
    Randomly choose an unowned system and assign it as the starting planet for player_name.
    The system is given 250 ships, production value 10, 0.5 defense, and gets the player's unique color.
    Returns the system id assigned or None if no unowned system exists.
    """
    available = [sys_id for sys_id, sys in state["systems"].items() if sys["owner"] is None]
    if not available:
        return None
    chosen = random.choice(available)
    # Lookup the player's color from the players list.
    player_color = None
    for p in state["players"]:
        if p["name"] == player_name:
            player_color = p.get("color")
            break
    state["systems"][chosen]["owner"] = player_name
    state["systems"][chosen]["current_ships"] = 250
    state["systems"][chosen]["ship_production"] = 10
    state["systems"][chosen]["defense_factor"] = 0.5
    state["systems"][chosen]["color"] = player_color
    return chosen

def assign_pirate_planets(state, chance=0.35):
    """
    For each unowned system in state, with a given chance, assign it to 'Pirates'
    with predefined values. Pirate systems use a fixed gray color.
    """
    for sys_id, sys in state["systems"].items():
        if sys["owner"] is None and random.random() < chance:
            sys["owner"] = "Pirates"
            sys["current_ships"] = 150
            sys["ship_production"] = 5
            sys["defense_factor"] = 0.5
            sys["color"] = "#808080"

def save_game(session_id):
    """Save the game state for a session to a JSON file and return the filename."""
    if session_id not in game_sessions:
        return None
    state = game_sessions[session_id]
    timestamp = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
    filename = f"{session_id}_{timestamp}.json"
    save_folder = os.path.join(os.getcwd(), "saves")
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    full_path = os.path.join(save_folder, filename)
    with open(full_path, "w") as f:
        json.dump(state, f)
    print(f"Session {session_id} saved as {filename}")
    return filename

def list_sessions():
    """Return a list of active session details."""
    sessions = []
    for sid, state in game_sessions.items():
        sessions.append({
            "session_id": sid,
            "planet_count": state.get("planet_count"),
            "year": state.get("year"),
            "creator": state.get("creator"),
            "player_count": len(state.get("players", []))
        })
    return sessions

def load_game_from_file(filename):
    """Load a game state from a file and register it as an active session."""
    save_folder = os.path.join(os.getcwd(), "saves")
    full_path = os.path.join(save_folder, filename)
    with open(full_path, "r") as f:
        loaded_state = json.load(f)
    game_sessions[loaded_state["session_id"]] = loaded_state
    return loaded_state

clients = []
clients_lock = threading.Lock()

def broadcast(message, session_id, sender_socket=None):
    """Send a message to all connected clients for a given session."""
    with clients_lock:
        for client in clients:
            if client.get("socket") != sender_socket and client.get("session_id") == session_id:
                try:
                    client["socket"].send(message.encode('utf-8'))
                except Exception as e:
                    print(f"Broadcast error: {e}")

def handle_client(client_socket, addr):
    """
    Handle client commands. Expected commands:
      CREATE <planet_count> <player_name>
      JOIN <session_id> <player_name>
      LISTSESSIONS
      REFRESH <session_id>
      SAVE <session_id>
      LOAD <filename>
    Other messages may be broadcast to players in the same session.
    """
    print(f"Connection from {addr}")
    client_info = {"socket": client_socket, "session_id": None, "player": None}
    with clients_lock:
        clients.append(client_info)
    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            message = data.decode('utf-8').strip()
            print(f"Received from {addr}: {message}")
            parts = message.split()
            if not parts:
                continue
            cmd = parts[0].upper()
            if cmd == "CREATE" and len(parts) >= 3:
                try:
                    planet_count = int(parts[1])
                    player_name = parts[2]
                    state = new_game_state(planet_count, creator=player_name, player_name=player_name)
                    sp = assign_starting_planet(state, player_name)
                    assign_pirate_planets(state, chance=0.35)
                    session_id = state["session_id"]
                    game_sessions[session_id] = state
                    client_info["session_id"] = session_id
                    client_info["player"] = player_name
                    client_socket.send(f"CREATED {session_id} START {sp}".encode('utf-8'))
                except Exception as e:
                    client_socket.send(f"ERROR {e}".encode('utf-8'))
            elif cmd == "JOIN" and len(parts) >= 3:
                session_id = parts[1]
                player_name = parts[2]
                if session_id in game_sessions:
                    state = game_sessions[session_id]
                    new_color = random_color()
                    state["players"].append({ "name": player_name, "color": new_color })
                    sp = assign_starting_planet(state, player_name)
                    client_info["session_id"] = session_id
                    client_info["player"] = player_name
                    client_socket.send(f"JOINED {session_id} START {sp}".encode('utf-8'))
                    broadcast(f"PLAYER {player_name} joined session; assigned planet {sp}", session_id, client_socket)
                else:
                    client_socket.send("ERROR Session not found".encode('utf-8'))
            elif cmd == "LISTSESSIONS":
                sessions = list_sessions()
                client_socket.send(f"SESSIONS {json.dumps(sessions)}".encode('utf-8'))
            elif cmd == "REFRESH" and len(parts) >= 2:
                session_id = parts[1]
                if session_id in game_sessions:
                    state = game_sessions[session_id]
                    client_socket.send(f"GAMEDATA {json.dumps(state)}".encode('utf-8'))
                else:
                    client_socket.send("ERROR Session not found".encode('utf-8'))
            elif cmd == "SAVE" and len(parts) >= 2:
                session_id = parts[1]
                filename = save_game(session_id)
                if filename:
                    client_socket.send(f"SAVED {filename}".encode('utf-8'))
                else:
                    client_socket.send("ERROR No such session".encode('utf-8'))
            elif cmd == "LOAD" and len(parts) >= 2:
                filename = parts[1]
                try:
                    state = load_game_from_file(filename)
                    client_socket.send(f"GAMEDATA {json.dumps(state)}".encode('utf-8'))
                except Exception as ex:
                    client_socket.send(f"ERROR Could not load save: {ex}".encode('utf-8'))
            else:
                session_id = client_info.get("session_id")
                if session_id:
                    broadcast(message, session_id, client_socket)
                else:
                    client_socket.send("ERROR Not in a session".encode('utf-8'))
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        print(f"Closing connection from {addr}")
        with clients_lock:
            if client_info in clients:
                clients.remove(client_info)
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server listening on {HOST}:{PORT}")
    try:
        while True:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()