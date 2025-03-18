import sys
import random
import math
import csv
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QGridLayout, 
                             QVBoxLayout, QLineEdit, QHBoxLayout, QMenu, QMessageBox)
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QEvent
from functools import partial

# Import the worldgen loader from worldgen.py.
from worldgen import load_worldgen_options

class ButtonGrid(QWidget):
    def __init__(self, num_buttons=80, owners=None):
        super().__init__()
        self.num_buttons = num_buttons
        # Use provided owner names or fallback defaults.
        if owners is None:
            self.owners = ["Owner A", "Owner B", "Owner C", "Owner D", "Owner E"]
        else:
            self.owners = owners
        self.button_coords = {}  # Map button number to its grid position
        self.buttons = {}        # Map button number to its button widget
        self.initUI()

    def initUI(self):
        # Define colors for each owner.
        owner_colors = {
            "Owner A": "#FFCCCC",  # light red
            "Owner B": "#CCFFCC",  # light green
            "Owner C": "#CCCCFF",  # light blue
            "Owner D": "#FFFFCC",  # light yellow
            "Owner E": "#CCFFFF"   # light cyan
        }

        main_layout = QVBoxLayout()
        grid = QGridLayout()
        # Grid dimensions: adjust if needed; here we choose fixed values.
        rows, cols = 40, 15
        positions = [(row, col) for row in range(rows) for col in range(cols)]
        random.shuffle(positions)
        # Create the number of buttons as specified by num_buttons.
        for i in range(self.num_buttons):
            button = QPushButton(str(i + 1))
            pos = positions[i]
            button.grid_pos = pos
            self.button_coords[i + 1] = pos
            self.buttons[i + 1] = button

            # Initialize custom variables.
            button.current_ships = 0
            button.ship_production = random.randint(1, 10)
            button.defense_factor = round(random.uniform(0.7, 1.0), 2)
            button.owner = random.choice(self.owners)
            button.setStyleSheet(f"background-color: {owner_colors[button.owner]};")

            grid.addWidget(button, pos[0], pos[1])
            button.installEventFilter(self)
        main_layout.addLayout(grid)

        for row in range(rows):
            grid.setRowStretch(row, 1)
        for col in range(cols):
            grid.setColumnStretch(col, 1)

        main_layout.addStretch(1)

        hbox = QHBoxLayout()
        self.input_field = QLineEdit()
        next_turn_button = QPushButton("Next Turn")
        hbox.addWidget(self.input_field)
        hbox.addWidget(next_turn_button)
        next_turn_button.clicked.connect(self.nextTurn)
        main_layout.addLayout(hbox)

        self.setLayout(main_layout)
        self.setWindowTitle('Risiko2py')

    def eventFilter(self, obj, event):
        if isinstance(obj, QPushButton):
            if event.type() == QEvent.Enter:
                self.openMenu(obj)
                return True
            elif event.type() == QEvent.Leave:
                if hasattr(self, "current_menu") and self.current_menu is not None:
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
        selectAction = menu.addAction("Select as first system for distance calculation")
        selectAction.triggered.connect(lambda: self.selectFirstSystem(button))
        fleetAction = menu.addAction("Send Fleet from this System")
        fleetAction.triggered.connect(lambda: self.selectSourceForFleetSend(button))
        menu.addAction("Action 3")
        self.current_menu = menu
        menu.popup(button.mapToGlobal(button.rect().bottomLeft()))

    def selectFirstSystem(self, button):
        num = int(button.text())
        self.distance_inputs = [num]
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter second button number")
        try:
            self.input_field.returnPressed.disconnect(self.processDistanceInput)
        except Exception:
            pass
        self.input_field.returnPressed.connect(self.processDistanceInput)
        self.input_field.setFocus()

    def selectSourceForFleetSend(self, button):
        src = int(button.text())
        self.fleet_inputs = [src]
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter destination button number")
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_E:
            self.startDistanceInput()
        elif event.key() == Qt.Key_J:
            self.nextTurn()
        elif event.key() == Qt.Key_F:
            self.startFleetSend()
        else:
            super().keyPressEvent(event)

    def startDistanceInput(self):
        self.distance_inputs = []
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter first button number")
        self.input_field.returnPressed.connect(self.processDistanceInput)
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
                self.input_field.setPlaceholderText("Enter second button number")
            elif len(self.distance_inputs) == 2:
                num1, num2 = self.distance_inputs
                pos1 = self.button_coords.get(num1)
                pos2 = self.button_coords.get(num2)
                if pos1 is None or pos2 is None:
                    raise ValueError("One or both button numbers are invalid.")
                distance = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                QMessageBox.information(self, "Distance",
                    f"Distance between button {num1} and button {num2} is: {distance:.2f}")
                self.input_field.clear()
                self.input_field.setPlaceholderText("")
                self.input_field.returnPressed.disconnect(self.processDistanceInput)
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def startFleetSend(self):
        self.fleet_inputs = []
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter source button number")
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

    def processFleetInput(self):
        try:
            text = self.input_field.text().strip()
            if not text:
                return
            value = int(text)
            self.fleet_inputs.append(value)
            if len(self.fleet_inputs) == 1:
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter destination button number")
            elif len(self.fleet_inputs) == 2:
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter number of ships to send")
            elif len(self.fleet_inputs) == 3:
                src, dest, ships_to_send = self.fleet_inputs
                pos1 = self.button_coords.get(src)
                pos2 = self.button_coords.get(dest)
                if pos1 is None or pos2 is None:
                    raise ValueError("Invalid source or destination system.")
                distance = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                turns_required = math.ceil(distance)
                source_button = self.buttons.get(src)
                if source_button.current_ships < ships_to_send:
                    raise ValueError("Not enough ships available in the source system!")
                source_button.current_ships -= ships_to_send
                if not hasattr(self, "fleets"):
                    self.fleets = []
                fleet_owner = source_button.owner
                self.fleets.append({
                    "source": src,
                    "destination": dest,
                    "ships": ships_to_send,
                    "turns": turns_required,
                    "owner": fleet_owner
                })
                QMessageBox.information(self, "Fleet Launched",
                    f"Fleet of {ships_to_send} ships (Owner: {fleet_owner}) sent from {src} to {dest}.\n"
                    f"Arrival in {turns_required} turn(s).")
                self.input_field.clear()
                self.input_field.setPlaceholderText("")
                self.input_field.returnPressed.disconnect(self.processFleetInput)
        except Exception as e:
            QMessageBox.warning(self, "Fleet Input Error", str(e))

    def nextTurn(self):
        for num, button in self.buttons.items():
            button.current_ships += button.ship_production
        if hasattr(self, "fleets"):
            fleets_arrived = []
            for fleet in self.fleets:
                fleet["turns"] -= 1
                if fleet["turns"] <= 0:
                    dest_button = self.buttons.get(fleet["destination"])
                    if dest_button:
                        if dest_button.owner == fleet["owner"]:
                            dest_button.current_ships += fleet["ships"]
                            QMessageBox.information(self, "Fleet Arrived",
                                f"Fleet from system {fleet['source']} has merged with forces at {fleet['destination']}.")
                        else:
                            effective_attack = fleet["ships"] * dest_button.defense_factor
                            if effective_attack > dest_button.current_ships:
                                dest_button.owner = fleet["owner"]
                                dest_button.current_ships = fleet["ships"]
                                QMessageBox.information(self, "Planet Captured",
                                    f"Fleet from system {fleet['source']} captured {fleet['destination']}.\n"
                                    f"New ship count: {fleet['ships']}.")
                            else:
                                dest_button.current_ships = max(0, dest_button.current_ships - effective_attack)
                                QMessageBox.information(self, "Attack Repelled",
                                    f"Fleet from system {fleet['source']} attacked {fleet['destination']}.\n"
                                    f"Defenders now at {dest_button.current_ships} ships.")
                    fleets_arrived.append(fleet)
            for fleet in fleets_arrived:
                self.fleets.remove(fleet)
        QMessageBox.information(self, "Turn Ended", "Production added and fleets processed!")

if __name__ == '__main__':
    # Load world generation options from worldgen.py.
    num_planets, owners = load_worldgen_options()
    app = QApplication(sys.argv)
    window = ButtonGrid(num_buttons=num_planets, owners=owners)
    window.showMaximized()
    sys.exit(app.exec_())
