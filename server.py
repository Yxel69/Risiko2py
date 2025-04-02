import socket
import threading
import json

HOST = ''          # Listen on all interfaces.
PORT = 9999

# Global game state – you can integrate your ButtonGrid/MultiGrid logic into a headless GameState class.
game_state = {
    "year": 1,
    "players": [],
    "systems": {},  # e.g., system_id: { "current_ships": ... , ... }
    "fleets": []
}

clients = []
lock = threading.Lock()

def broadcast(message):
    """Send a JSON message to all clients."""
    data = (json.dumps(message) + "\n").encode()
    with lock:
        for c in clients:
            try:
                c.sendall(data)
            except Exception:
                pass

def process_message(message):
    """Process messages from clients. For example, update game state based on actions."""
    global game_state
    action = message.get("action")
    # Here you would integrate your game logic. For example:
    if action == "next_turn":
        game_state["year"] += 1
        # This is where you would update systems and fleets.
    elif action == "join":
        player = message.get("player")
        if player and player not in game_state["players"]:
            game_state["players"].append(player)
    # ... add other message types as needed ...

def handle_client(conn, addr):
    print(f"Client connected: {addr}")
    buffer = ""
    with conn:
        with lock:
            clients.append(conn)
        # Send the initial game state.
        conn.sendall((json.dumps({"type": "init", "game_state": game_state})+"\n").encode())
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        msg = json.loads(line)
                        with lock:
                            process_message(msg)
                        broadcast({"type": "update", "game_state": game_state})
        except Exception as e:
            print("Error while receiving:", e)
    with lock:
        clients.remove(conn)
    print(f"Client disconnected: {addr}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print("Server listening on port", PORT)
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()