import sys
import socket
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog
from game_client import GameClient

def main():
    app = QApplication(sys.argv)
    
    # Prompt for server address and port
    server_address, ok = QInputDialog.getText(None, "Server Address", "Enter server address (IP or hostname):")
    if not ok or not server_address:
        sys.exit(0)

    server_port, ok = QInputDialog.getInt(None, "Server Port", "Enter server port:", 12345, 1024, 65535)
    if not ok:
        sys.exit(0)

    # Initialize the game client
    client = GameClient(server_address, server_port)

    try:
        client.connect_to_server()
        client.run()
    except Exception as e:
        QMessageBox.critical(None, "Connection Error", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()