import socket
import json
import ssl

class GameClient:
    def __init__(self, host='localhost', port=5000, token=None, api_url=None):
        self.host = host
        self.port = port
        self.socket = None
        self.token = token
        self.api_url = api_url

    def connect(self):
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_default_certs()

        self.socket = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=self.host)
        self.socket.connect((self.host, self.port))
        print("Connected to the server.")

    def send_request(self, request_type, data):
        request = {
            'type': request_type,
            'data': data
        }
        self.socket.sendall(json.dumps(request).encode('utf-8'))

    def receive_response(self):
        response = self.socket.recv(4096)
        return json.loads(response.decode('utf-8'))

    def close(self):
        if self.socket:
            self.socket.close()
            print("Connection closed.")

    def some_method(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        # ... use headers ...

