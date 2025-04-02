class GameServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.game_state = {}
        self.running = False

    def start(self):
        import socket
        from threading import Thread

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Server started on {self.host}:{self.port}")

        while self.running:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr} has been established.")
            self.clients.append(client_socket)
            Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while self.running:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    self.process_message(client_socket, message)
                else:
                    break
            except Exception as e:
                print(f"Error: {e}")
                break
        self.clients.remove(client_socket)
        client_socket.close()

    def process_message(self, client_socket, message):
        print(f"Received message: {message}")
        # Handle game logic and update game state here
        self.broadcast(message)

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending message: {e}")

    def stop(self):
        self.running = False
        self.server_socket.close()
        print("Server stopped.")