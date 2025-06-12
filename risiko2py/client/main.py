import sys
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List your client dependencies here
client_dependencies = [
    "requests",
    "PyQt5",
    "cryptography"
]

for dep in client_dependencies:
    try:
        __import__(dep.split('==')[0])
    except ImportError:
        print(f"Installing missing dependency: {dep}")
        install(dep)

# Now import the rest of your application
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog
from ui.game_ui import GameUI
from network.client import GameClient
from ui.auth_dialog import AuthDialog

def main():
    app = QApplication(sys.argv)

    # Prompt for server address
    default_url = "http://localhost:5000/api"
    api_url, ok = QInputDialog.getText(None, "Server Address", "Enter server API URL:", text=default_url)
    if not ok or not api_url.strip():
        QMessageBox.critical(None, "No Server", "You must enter a server address to continue.")
        sys.exit(1)
    api_url = api_url.strip()

    # Show login/register dialog
    auth = AuthDialog(api_url)
    result = auth.exec_()
    if not result or not auth.token:
        QMessageBox.critical(None, "Authentication Required", "You must log in or register to play.")
        sys.exit(1)

    # Pass the token and api_url to your GameClient or GameUI as needed
    client = GameClient(token=auth.token, api_url=api_url)
    game_ui = GameUI(client=client)
    game_ui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()