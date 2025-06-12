from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
import requests

class AuthDialog(QDialog):
    def __init__(self, api_url):
        super().__init__()
        self.api_url = api_url
        self.token = None
        self.setWindowTitle("Login/Register")
        self.layout = QVBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.layout.addWidget(self.username_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.password_input)
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        self.layout.addWidget(self.login_button)
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.register)
        self.layout.addWidget(self.register_button)
        self.setLayout(self.layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        response = requests.post(f"{self.api_url}/user/login", json={"username": username, "password": password})
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", response.json().get("msg", "Unknown error"))

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        response = requests.post(f"{self.api_url}/user/register", json={"username": username, "password": password})
        if response.status_code == 201:
            QMessageBox.information(self, "Registration Successful", "You can now log in.")
        else:
            QMessageBox.warning(self, "Registration Failed", response.json().get("msg", "Unknown error"))