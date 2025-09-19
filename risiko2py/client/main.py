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

dark_stylesheet = """
    QWidget { background-color: #111; color: #fff; }
    QMainWindow { background-color: #111; }
    QLineEdit, QTextEdit { background-color: #222; color: #fff; border: 1px solid #444; }
    QPushButton { background-color: #222; color: #fff; border: 1px solid #444; }
    QPushButton:disabled { background-color: #333; color: #888; }
    QLabel { color: #fff; }
    QListWidget, QComboBox, QSpinBox { background-color: #222; color: #fff; border: 1px solid #444; }
    QMenu { background-color: #222; color: #fff; }
    QDialog { background-color: #111; color: #fff; }
    QTableWidget, QHeaderView::section { background-color: #222; color: #fff; }
"""

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_stylesheet)

    # Update: Include /api in the default URL
    default_url = "http://risiko2.shroomy.ac/api"
    api_url, ok = QInputDialog.getText(None, "Server Address", 
        "Enter server API URL (include /api):", 
        text=default_url)
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


