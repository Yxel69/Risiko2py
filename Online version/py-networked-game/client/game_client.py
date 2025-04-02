class GameClient:
    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.socket = None

    def connect(self):
        import socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_address, self.server_port))
        print("Connected to server at {}:{}".format(self.server_address, self.server_port))

    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Disconnected from server.")

    def send_action(self, action):
        if self.socket:
            self.socket.sendall(action.encode('utf-8'))

    def receive_updates(self):
        while True:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                self.process_update(data.decode('utf-8'))
            except Exception as e:
                print("Error receiving data:", e)
                break

    def process_update(self, update):
        print("Received update:", update)

    def run(self):
        self.connect()
        try:
            self.receive_updates()
        finally:
            self.disconnect()