import socket
import threading
from shared.utils import serialize, deserialize

class GameServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.clients = []
        self.game_state = {}

    def start(self):
        print("Server started, waiting for connections...")
        while True:
            client_socket, addr = self.server.accept()
            print(f"Connection from {addr} has been established.")
            self.clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                self.process_message(data, client_socket)
            except Exception as e:
                print(f"Error: {e}")
                break
        client_socket.close()
        self.clients.remove(client_socket)

    def process_message(self, data, client_socket):
        message = deserialize(data)
        # Handle game logic based on the message received
        # For example, updating game state or broadcasting to other clients
        print(f"Received message: {message}")

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(serialize(message))
            except Exception as e:
                print(f"Error sending message: {e}")

if __name__ == "__main__":
    server = GameServer()
    server.start()