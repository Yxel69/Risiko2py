import sys
import random
import math
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QVBoxLayout, QLineEdit, QHBoxLayout, QMenu, QMessageBox
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt
from functools import partial

class ButtonGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.button_coords = {}  # Map button number to its grid position
        self.buttons = {}        # Map button number to its button widget
        self.initUI()

    def initUI(self):
        # Define the five possible owners.
        owners = ["Owner A", "Owner B", "Owner C", "Owner D", "Owner E"]

        # Create a vertical layout to hold the grid and the input field with submit button
        main_layout = QVBoxLayout()
        grid = QGridLayout()
        # Define the grid dimensions (for example, 40 rows and 15 columns)
        rows, cols = 40, 15
        # Create list of all possible positions so that the whole grid is filled
        positions = [(row, col) for row in range(rows) for col in range(cols)]
        random.shuffle(positions)
        # Randomly assign the 80 buttons into these grid positions
        for i in range(80):
            button = QPushButton(str(i + 1))
            # Store the grid position in the button object and in a dictionary
            pos = positions[i]
            button.grid_pos = pos
            self.button_coords[i + 1] = pos
            self.buttons[i + 1] = button          # Save reference to the button

            # Initialize custom variables
            button.current_ships = 0
            button.ship_production = random.randint(1, 10)
            button.defense_factor = round(random.uniform(0.7, 1.0), 2)
            # Assign a random owner from the list of five.
            button.owner = random.choice(owners)

            grid.addWidget(button, pos[0], pos[1])
            button.clicked.connect(partial(self.openMenu, button))
        main_layout.addLayout(grid)

        # Set stretch factors for each row and column so that the grid fills the available space
        for row in range(rows):
            grid.setRowStretch(row, 1)
        for col in range(cols):
            grid.setColumnStretch(col, 1)

        # Add a stretch to push the input field and button to the bottom
        main_layout.addStretch(1)

        # Create a horizontal layout for the input field and submit button
        hbox = QHBoxLayout()
        self.input_field = QLineEdit()
        submit_button = QPushButton("Submit")
        hbox.addWidget(self.input_field)
        hbox.addWidget(submit_button)
        main_layout.addLayout(hbox)

        self.setLayout(main_layout)
        self.setWindowTitle('Risiko2py')

    def openMenu(self, button):
        # Create a menu and add actions that display the button's variable values.
        menu = QMenu(self)
        menu.addAction(f"Current Ships: {button.current_ships}")
        menu.addAction(f"Ship Production: {button.ship_production}")
        menu.addAction(f"Defense Factor: {button.defense_factor}")
        menu.addAction(f"Owner: {button.owner}")
        menu.addSeparator()
        # Rewrite Action 1 to select this button as the first system for distance calculation.
        selectAction = menu.addAction("Select as first system for distance calculation")
        selectAction.triggered.connect(lambda: self.selectFirstSystem(button))
        # Keep additional actions as desired.
        menu.addAction("Action 2")
        menu.addAction("Action 3")
        # Display the menu below the button.
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

    def selectFirstSystem(self, button):
        # Get the button number from its text.
        num = int(button.text())
        # Set this button as the first system for distance calculation.
        self.distance_inputs = [num]
        # Clear the input field and set the placeholder for the second button.
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter second button number")
        # Disconnect any previously connected signal to avoid multiple connections.
        try:
            self.input_field.returnPressed.disconnect(self.processDistanceInput)
        except Exception:
            pass
        # Connect the returnPressed signal to handle the second input.
        self.input_field.returnPressed.connect(self.processDistanceInput)
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
        # Initialize the input mode for distance calculation.
        self.distance_inputs = []
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter first button number")
        # Connect the returnPressed signal to our handler.
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
                # Ask for the second number.
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter second button number")
            elif len(self.distance_inputs) == 2:
                num1, num2 = self.distance_inputs
                pos1 = self.button_coords.get(num1)
                pos2 = self.button_coords.get(num2)
                if pos1 is None or pos2 is None:
                    raise ValueError("One or both button numbers are invalid.")
                # Compute Euclidean distance.
                distance = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                QMessageBox.information(self, "Distance",
                    f"Distance between button {num1} and button {num2} is: {distance:.2f}")
                # Reset the input field and disconnect the signal.
                self.input_field.clear()
                self.input_field.setPlaceholderText("")
                self.input_field.returnPressed.disconnect(self.processDistanceInput)
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def startFleetSend(self):
        # Prepare to collect fleet information: source, destination, number of ships.
        self.fleet_inputs = []  # Will store [source, destination, ship_count]
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter source button number")
        # Disconnect any existing connections for other input modes.
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
                # Collected source; now ask for destination.
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter destination button number")
            elif len(self.fleet_inputs) == 2:
                # Collected destination; now ask for ship count to send.
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter number of ships to send")
            elif len(self.fleet_inputs) == 3:
                # We have all inputs. Unpack them.
                src, dest, ships_to_send = self.fleet_inputs
                pos1 = self.button_coords.get(src)
                pos2 = self.button_coords.get(dest)
                if pos1 is None or pos2 is None:
                    raise ValueError("Invalid source or destination system.")
                # Calculate distance and number of turns required (round up)
                distance = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                turns_required = math.ceil(distance)
                source_button = self.buttons.get(src)
                if source_button.current_ships < ships_to_send:
                    raise ValueError("Not enough ships available in the source system!")
                # Deduct the ships from the source system.
                source_button.current_ships -= ships_to_send
                # Create the fleet. Ensure self.fleets exists.
                if not hasattr(self, "fleets"):
                    self.fleets = []
                # Add an owner variable to the fleet from the source system.
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
                # Reset the input field and disconnect this signal.
                self.input_field.clear()
                self.input_field.setPlaceholderText("")
                self.input_field.returnPressed.disconnect(self.processFleetInput)
        except Exception as e:
            QMessageBox.warning(self, "Fleet Input Error", str(e))

    def nextTurn(self):
        # First, update production for all systems.
        for num, button in self.buttons.items():
            button.current_ships += button.ship_production

        # Then process any fleets in transit.
        if hasattr(self, "fleets"):
            fleets_arrived = []
            for fleet in self.fleets:
                fleet["turns"] -= 1
                if fleet["turns"] <= 0:
                    dest_button = self.buttons.get(fleet["destination"])
                    if dest_button:
                        # Check if fleet's owner matches destination system's owner.
                        if dest_button.owner == fleet["owner"]:
                            dest_button.current_ships += fleet["ships"]
                            QMessageBox.information(self, "Fleet Arrived",
                                f"Fleet from system {fleet['source']} has arrived at destination {fleet['destination']} and merged with existing forces.")
                        else:
                            # Hostile encounter.
                            effective_attack = fleet["ships"] * dest_button.defense_factor
                            if effective_attack > dest_button.current_ships:
                                # Attacking fleet wins and captures the planet.
                                dest_button.owner = fleet["owner"]
                                dest_button.current_ships = fleet["ships"]
                                QMessageBox.information(self, "Planet Captured",
                                    f"Fleet from system {fleet['source']} (Owner: {fleet['owner']}) has captured destination {fleet['destination']}.\n"
                                    f"New ship count is {fleet['ships']}.")
                            else:
                                # Defenders repel the attack, reduce defending ships.
                                dest_button.current_ships = max(0, dest_button.current_ships - effective_attack)
                                QMessageBox.information(self, "Attack Repelled",
                                    f"Fleet from system {fleet['source']} (Owner: {fleet['owner']}) attacked destination {fleet['destination']}.\n"
                                    f"Defenders reduced to {dest_button.current_ships} ships.")
                    fleets_arrived.append(fleet)
            # Remove fleets that have arrived.
            for fleet in fleets_arrived:
                self.fleets.remove(fleet)
        QMessageBox.information(self, "Turn Ended",
            "Production has been added and fleets have been processed!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ButtonGrid()
    window.showMaximized()  # Launch the application in fullscreen mode
    sys.exit(app.exec_())
