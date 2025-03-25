import sys
import os
import random
import math
import socket
import threading
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QGridLayout,
    QVBoxLayout, QLineEdit, QHBoxLayout, QMenu, QMessageBox, QInputDialog, QDialog, QLabel)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, QObject
from functools import partial
from worldgen import load_worldgen_options

class NetworkSignals(QObject):
    gameUpdate = pyqtSignal(str)

class ButtonGrid(QWidget):
    def __init__(self, session_id=None, player_name=None):
        super().__init__()
        self.setWindowIcon(QIcon("designs/icon.png"))
        self.year = 1
        self.session_id = session_id  
        self.player_name = player_name
        self.num_buttons = 80
        self.owners = []  # List of player names in session.
        self.owner_colors = {}
        self.button_coords = {}  
        self.buttons = {}        
        self.fleets = []
        self.ready_set = set()
        self.initUI()
        self.network_signals = NetworkSignals()
        self.network_signals.gameUpdate.connect(self.handleServerMessage)
        self.connectToServer()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.info_label = QLabel("Not in a session yet")
        main_layout.addWidget(self.info_label)
        
        self.grid = QGridLayout()
        rows, cols = 40, 15
        positions = [(row, col) for row in range(rows) for col in range(cols)]
        random.shuffle(positions)
        for i in range(self.num_buttons):
            button = QPushButton(str(i+1))
            pos = positions[i]
            button.grid_pos = pos
            self.button_coords[i+1] = pos
            self.buttons[i+1] = button
            button.current_ships = 0
            button.ship_production = random.randint(1, 10)
            button.defense_factor = round(random.uniform(0.7, 1.0), 2)
            button.owner = None
            button.setStyleSheet("background-color: #FFFFFF;")
            self.grid.addWidget(button, pos[0], pos[1])
            button.installEventFilter(self)
        main_layout.addLayout(self.grid)
        
        # Control buttons.
        hbox = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setMinimumHeight(40)
        next_turn_button = QPushButton("Next Turn")
        change_owner_button = QPushButton("Change Owner")
        refresh_button = QPushButton("Refresh Game List")
        hbox.addWidget(self.input_field)
        hbox.addWidget(next_turn_button)
        hbox.addWidget(change_owner_button)
        hbox.addWidget(refresh_button)
        next_turn_button.clicked.connect(self.readyNextTurn)
        change_owner_button.clicked.connect(self.changeOwner)
        refresh_button.clicked.connect(self.refreshGameList)
        main_layout.addLayout(hbox)
        
        self.setLayout(main_layout)
        self.input_field.clearFocus()

    def connectToServer(self):
        self.server_host = '127.0.0.1'
        self.server_port = 9999
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            threading.Thread(target=self.listenToServer, daemon=True).start()
        except Exception as e:
            QMessageBox.warning(self, "Network Error", f"Could not connect to server: {e}")

    def listenToServer(self):
        while True:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                message = data.decode('utf-8')
                self.network_signals.gameUpdate.emit(message)
            except Exception as e:
                print("Network receive error:", e)
                break

    def handleServerMessage(self, message):
        if message.startswith("CREATED"):
            parts = message.split()
            self.session_id = parts[1]
            assigned = parts[3] if len(parts) >= 4 else "None"
            self.info_label.setText(f"Session {self.session_id}: You are creator; starting planet {assigned}")
            self.owners.append(self.player_name)
        elif message.startswith("JOINED"):
            parts = message.split()
            self.session_id = parts[1]
            assigned = parts[3] if len(parts) >= 4 else "None"
            self.info_label.setText(f"Session {self.session_id}: Joined as {self.player_name}; starting planet {assigned}")
            self.owners.append(self.player_name)
        elif message.startswith("SESSIONS"):
            try:
                sessions = json.loads(message[len("SESSIONS "):])
                s = "\n".join([f"{sess['session_id']}: {sess['planet_count']} planets, Year {sess['year']}, Players {sess['player_count']}" 
                                for sess in sessions])
                QMessageBox.information(self, "Available Games", s if s else "No games available")
            except Exception as e:
                QMessageBox.warning(self, "Parsing Error", str(e))
        elif message.startswith("GAMEDATA"):
            try:
                state = json.loads(message[len("GAMEDATA "):])
                self.year = state.get("year", self.year)
                self.owners = [p["name"] for p in state.get("players", [])]
                self.info_label.setText(f"Session {state.get('session_id')} | Year: {self.year} | Players: {', '.join(self.owners)}")
            except Exception as e:
                QMessageBox.warning(self, "Parsing Error", str(e))
        elif message.startswith("SAVED"):
            QMessageBox.information(self, "Save Confirmed", message)
        elif message.startswith("ERROR"):
            QMessageBox.warning(self, "Server Error", message)
        else:
            QMessageBox.information(self, "Server Message", message)

    def sendCommand(self, cmd):
        try:
            self.client_socket.send(cmd.encode('utf-8'))
        except Exception as e:
            QMessageBox.warning(self, "Network Error", str(e))

    def createGame(self, planet_count, player_name):
        self.player_name = player_name
        cmd = f"CREATE {planet_count} {player_name}"
        self.sendCommand(cmd)

    def joinGame(self, session_id, player_name):
        self.player_name = player_name
        cmd = f"JOIN {session_id} {player_name}"
        self.sendCommand(cmd)

    def refreshGameList(self):
        self.sendCommand("LISTSESSIONS")

    def refreshGameState(self):
        if self.session_id:
            self.sendCommand(f"REFRESH {self.session_id}")

    def changeOwner(self):
        if not self.owners:
            QMessageBox.warning(self, "Error", "No owners available.")
            return
        current, ok = QInputDialog.getItem(self, "Change Owner", "Select your new owner:", self.owners, 0, False)
        if ok and current:
            self.player_name = current
            QMessageBox.information(self, "Owner Changed", f"You are now '{current}'")
            self.updateInfoLabel()

    def readyNextTurn(self):
        self.refreshGameState()

    def updateInfoLabel(self):
        self.info_label.setText(f"Session: {self.session_id} | Year: {self.year} | You: {self.player_name}")

    def eventFilter(self, obj, event):
        if isinstance(obj, QPushButton):
            if event.type() == QEvent.Enter:
                self.openMenu(obj)
                return True
            elif event.type() == QEvent.Leave:
                if hasattr(self, "current_menu") and self.current_menu:
                    self.current_menu.close()
                    self.current_menu = None
        return super().eventFilter(obj, event)

    def openMenu(self, button):
        menu = QMenu(self)
        menu.addAction(f"Current Ships: {button.current_ships}")
        menu.addAction(f"Ship Production: {button.ship_production}")
        menu.addAction(f"Defense Factor: {button.defense_factor}")
        menu.addAction(f"Owner: {button.owner}")
        menu.addSeparator()
        action1 = menu.addAction("Select as first system for distance calculation")
        action1.triggered.connect(lambda: self.selectFirstSystem(button))
        action2 = menu.addAction("Send Fleet from this System")
        action2.triggered.connect(lambda: self.selectSourceForFleetSend(button))
        menu.addAction("Other Action")
        self.current_menu = menu
        menu.popup(button.mapToGlobal(button.rect().bottomLeft()))

    def selectFirstSystem(self, button):
        num = int(button.text())
        self.distance_inputs = [num]
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter second system number")
        try:
            self.input_field.returnPressed.disconnect(self.processDistanceInput)
        except Exception:
            pass
        self.input_field.returnPressed.connect(self.processDistanceInput)
        self.input_field.setFocus()

    def selectSourceForFleetSend(self, button):
        if button.owner != self.player_name:
            QMessageBox.warning(self, "Invalid", "You can only send fleets from systems you own.")
            return
        src = int(button.text())
        self.fleet_inputs = [src]
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter destination system number")
        try:
            self.input_field.returnPressed.disconnect(self.processDistanceInput)
        except Exception:
            pass
        try:
            self.input_field.returnPressed.disconnect(self.processFleetInput)
        except Exception:
            pass
        self.input_field.returnPressed.connect(self.processFleetInput)
        self.input_field.setFocus()

    def processDistanceInput(self):
        try:
            text = self.input_field.text().strip()
            if not text:
                return
            value = int(text)
            self.distance_inputs.append(value)
            if len(self.distance_inputs) == 1:
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter second system number")
            elif len(self.distance_inputs) == 2:
                num1, num2 = self.distance_inputs
                pos1 = self.button_coords.get(num1)
                pos2 = self.button_coords.get(num2)
                if pos1 is None or pos2 is None:
                    raise ValueError("Invalid system numbers.")
                distance = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
                QMessageBox.information(self, "Distance", f"Distance is {distance:.2f}")
                self.input_field.clear()
                self.input_field.returnPressed.disconnect(self.processDistanceInput)
                self.distance_inputs = []
            else:
                pass
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def processFleetInput(self):
        try:
            text = self.input_field.text().strip()
            if not text:
                return
            value = int(text)
            if len(self.fleet_inputs) == 0:
                if value not in self.buttons:
                    raise ValueError("Invalid system id.")
                source_button = self.buttons[value]
                if source_button.owner != self.player_name:
                    raise ValueError("You can only send fleets from systems you own.")
            self.fleet_inputs.append(value)
            if len(self.fleet_inputs) == 1:
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter destination system number")
            elif len(self.fleet_inputs) == 2:
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter number of ships to send")
            elif len(self.fleet_inputs) == 3:
                src, dest, ships = self.fleet_inputs
                if ships <= 5:
                    self.input_field.clear()
                    self.fleet_inputs = []
                    raise ValueError("Fleet must be larger than 5 ships.")
                QMessageBox.information(self, "Fleet Launched", f"Fleet from {src} to {dest} of {ships} ships.")
                self.input_field.clear()
                self.input_field.returnPressed.disconnect(self.processFleetInput)
                self.fleet_inputs = []
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # New menu dialog: "Create Game" or "Join Game"
    menu_dialog = QDialog()
    menu_dialog.setWindowTitle("Game Menu")
    vbox = QVBoxLayout(menu_dialog)
    
    choice = {"option": None}
    
    btnCreate = QPushButton("Create Game")
    btnJoin = QPushButton("Join Game")
    btnExit = QPushButton("Exit")
    
    def createGame():
        choice["option"] = "create"
        menu_dialog.accept()
    
    def joinGame():
        choice["option"] = "join"
        menu_dialog.accept()
    
    def exitGame():
        choice["option"] = "exit"
        menu_dialog.reject()
    
    btnCreate.clicked.connect(createGame)
    btnJoin.clicked.connect(joinGame)
    btnExit.clicked.connect(exitGame)
    
    vbox.addWidget(btnCreate)
    vbox.addWidget(btnJoin)
    vbox.addWidget(btnExit)
    
    if menu_dialog.exec_() == QDialog.Rejected or choice["option"] == "exit":
        sys.exit(0)
    
    window = ButtonGrid()
    
    if choice["option"] == "create":
        planet_count, ok = QInputDialog.getInt(None, "Planet Count", "Enter number of planets:", 80, 10, 200)
        if not ok:
            sys.exit(0)
        player_name, ok = QInputDialog.getText(None, "Player Name", "Enter your name:")
        if not ok or not player_name.strip():
            player_name = "Player_1"
        window.createGame(planet_count, player_name.strip())
    elif choice["option"] == "join":
        window.sendCommand("LISTSESSIONS")
        session_id, ok = QInputDialog.getText(None, "Join Game", "Enter Session ID to join:")
        if not ok or not session_id.strip():
            sys.exit(0)
        player_name, ok = QInputDialog.getText(None, "Player Name", "Enter your name:")
        if not ok or not player_name.strip():
            player_name = "Player_X"
        window.joinGame(session_id.strip(), player_name.strip())
    
    window.showMaximized()
    sys.exit(app.exec_())