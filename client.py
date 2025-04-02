import sys
import socket
import threading
import json
from queue import Queue
from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox

class NetworkClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.queue = Queue()
        self.listener_thread = threading.Thread(target=self.listen, daemon=True)
        self.listener_thread.start()

    def listen(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        msg = json.loads(line)
                        self.handle_message(msg)
            except Exception as e:
                print("Network error:", e)
                break

    def handle_message(self, msg):
        # Process a message from the server.
        print("Message from server:", msg)
        # If the message is an update, you could store it in a thread-safe queue or signal your UI.
        self.queue.put(msg)

    def send(self, msg):
        data = (json.dumps(msg) + "\n").encode()
        self.sock.sendall(data)

# In your client UI you would incorporate the network client.
# For example, this simple main function prompts for connection info and shows an informational message.
def main():
    app = QApplication(sys.argv)
    host, ok = QInputDialog.getText(None, "Server Address", "Enter Server IP:")
    if not ok or not host:
        sys.exit(0)
    port, ok = QInputDialog.getInt(None, "Server Port", "Enter Server Port:", 9999, 1024, 65535)
    if not ok:
        sys.exit(0)

    net_client = NetworkClient(host, port)
    # Send a join message. Also, you might ask for a player name.
    player_name, ok = QInputDialog.getText(None, "Player Name", "Enter your player name:")
    if ok and player_name.strip():
        net_client.send({"action": "join", "player": player_name.strip()})
    else:
        net_client.send({"action": "join", "player": "Unnamed Player"})

    # The rest of your UI is essentially what is in your main.py but now integrated with net_client.
    # For instance, in your MultiGrid or ButtonGrid classes you would add:
    #   self.net_client = net_client
    # and then whenever a player action occurs (e.g., next_turn, send fleet, etc.) you would send a message:
    #   self.net_client.send({ "action": "next_turn", ... })
    QMessageBox.information(None, "Connected", "You are now connected to the game server!")
    # You could also set up a timer or a thread in your UI to poll net_client.queue for updates.
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()