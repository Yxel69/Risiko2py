import sys
import os
import random
import math
import csv
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QGridLayout, 
                             QVBoxLayout, QLineEdit, QHBoxLayout, QMenu, QMessageBox, QInputDialog, QDialog, QFileDialog, QLabel)
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QEvent
from functools import partial

# Import the worldgen loader from worldgen.py.
from worldgen import load_worldgen_options

class ButtonGrid(QWidget):
    def __init__(self, num_buttons=80, owners=None):
        super().__init__()
        self.year = 1  # Initialize game year.
        self.num_buttons = num_buttons
        # Use provided owners or fallback.
        self.owners = owners if owners is not None else ["Default_Player"]
        # Assign each owner a unique random color.
        self.owner_colors = {}
        for owner in self.owners:
            self.owner_colors[owner] = "#{:06X}".format(random.randint(0, 0xFFFFFF))
        self.button_coords = {}  # Map: system ID -> grid position.
        self.buttons = {}        # Map: system ID -> QPushButton.
        self.fleets = []         # Initialize fleets array.
        self.ready_set = set()   # New: Track which players have confirmed readiness.
        self.initUI()
        # Note: choosePlayerOwner() and assignStartingPlanets() are called from __main__.

    def initUI(self):
        main_layout = QVBoxLayout()
        # New: Add an info label to display the current owner and game year.
        self.info_label = QLabel(f"Owner: {getattr(self, 'player_owner', 'N/A')} | Game Year: {self.year}")
        main_layout.addWidget(self.info_label)
        
        self.grid = QGridLayout()   # Store grid layout in an instance variable.
        rows, cols = 40, 15
        positions = [(row, col) for row in range(rows) for col in range(cols)]
        random.shuffle(positions)
        # Create each system button.
        for i in range(self.num_buttons):
            button = QPushButton(str(i+1))
            pos = positions[i]
            button.grid_pos = pos
            self.button_coords[i+1] = pos
            self.buttons[i+1] = button
            
            # Initialize properties.
            button.current_ships = 0
            button.ship_production = random.randint(1, 10)
            button.defense_factor = round(random.uniform(0.7, 1.0), 2)
            # No owner is assigned by default.
            button.owner = None
            button.setStyleSheet("background-color: #FFFFFF;")
            
            self.grid.addWidget(button, pos[0], pos[1])
            button.installEventFilter(self)
        main_layout.addLayout(self.grid)
        
        # Input field and control buttons.
        hbox = QHBoxLayout()
        self.input_field = QLineEdit()
        # Enlarge the input field height by 200%.
        self.input_field.setMinimumHeight(40)
        next_turn_button = QPushButton("Next Turn")
        # Enlarge the button height by 200%.
        next_turn_button.setMinimumHeight(40)
        change_owner_button = QPushButton("Change Owner")
        change_owner_button.setMinimumHeight(40)
        hbox.addWidget(self.input_field)
        hbox.addWidget(next_turn_button)
        hbox.addWidget(change_owner_button)
        # Bind buttons to methods.
        next_turn_button.clicked.connect(self.readyNextTurn)
        change_owner_button.clicked.connect(self.changeOwner)
        main_layout.addLayout(hbox)
        
        self.setLayout(main_layout)
        # Unfocus the input field at game start.
        self.input_field.clearFocus()

    def changeOwner(self):
        """
        Allow the user to change the current game owner.
        Displays a drop-down menu (as in loadGame) for selecting a new owner.
        """
        current, ok = QInputDialog.getItem(self, "Change Current Owner",
                                           "Select your new owner:", self.owners, 0, False)
        if ok and current:
            self.player_owner = current
            self.player_color = self.owner_colors.get(current, "#FFFFFF")
            QMessageBox.information(self, "Owner Changed",
                                    f"Your current owner is now '{current}' with color {self.player_color}.")

    def recreateGridLayout(self):
        """
        Clear the grid layout and re-add each button based on its grid_pos.
        If a button's grid_pos is None, use its default position from self.button_coords.
        """
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        for sys_id, button in self.buttons.items():
            pos = button.grid_pos if button.grid_pos is not None else self.button_coords.get(sys_id)
            if pos:  # Ensure pos is available.
                self.grid.addWidget(button, pos[0], pos[1])
    
    def openGameMenuAtStart(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Game Menu")
        layout = QVBoxLayout()
        
        # Display current game year.
        year_label = QLabel(f"Current Game Year: {self.year}")
        layout.addWidget(year_label)
        
        start_btn = QPushButton("Start New Game")
        load_btn = QPushButton("Load Game")
        save_btn = QPushButton("Save Game")
        close_btn = QPushButton("Close Game")
        
        start_btn.clicked.connect(lambda: self.startNewGame(dialog))
        load_btn.clicked.connect(lambda: [self.loadGame(), dialog.accept()])
        save_btn.clicked.connect(lambda: [self.toggleSaveGame(), dialog.accept()])
        close_btn.clicked.connect(lambda: [self.close(), dialog.reject()])
        
        layout.addWidget(start_btn)
        layout.addWidget(load_btn)
        layout.addWidget(save_btn)
        layout.addWidget(close_btn)
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Rejected:
            QApplication.instance().quit()
    
    def startNewGame(self, dialog):
        self.choosePlayerOwner()
        self.assignStartingPlanets()
        dialog.accept()
    
    def choosePlayerOwner(self):
        """Let the user choose an owner from the available owner names."""
        if self.owners:
            current, ok = QInputDialog.getItem(self, "Choose Your Owner",
                                               "Select your owner:", self.owners, 0, False)
            if ok and current:
                self.player_owner = current
            else:
                self.player_owner = random.choice(self.owners)
        else:
            self.player_owner = "Default_Player"
        # Use the color already assigned to the owner.
        self.player_color = self.owner_colors.get(self.player_owner, "#FFFFFF")
        QMessageBox.information(self, "Player Owner",
            f"You are '{self.player_owner}' with color {self.player_color}")
        self.updateInfoLabel()
    
    def assignStartingPlanets(self):
        """Assign one unique starting system (planet) to each owner."""
        available_ids = list(self.buttons.keys())
        random.shuffle(available_ids)
        self.starting_planets = {}  # Map owner -> system id.
        for owner in self.owners:
            if not available_ids:
                break  # In case there are more owners than systems.
            sys_id = available_ids.pop()
            self.starting_planets[owner] = sys_id
            button = self.buttons[sys_id]
            button.owner = owner

            # Overwrite starting planet values.
            button.current_ships = 250
            button.ship_production = 10
            button.defense_factor = 0.5

            button.setStyleSheet(f"background-color: {self.owner_colors[owner]};")
            QMessageBox.information(self, "Starting Planet Assigned",
                f"System {sys_id} is now assigned to {owner}.")
    
    def nextTurn(self):
        # Increase ships per system.
        for num, button in self.buttons.items():
            button.current_ships += button.ship_production
        # Process fleets...
        # (Existing fleet processing code here.)
        QMessageBox.information(self, "Turn Ended", "Production added and fleets processed!")
        self.year += 1
        self.updateInfoLabel()
        # Refresh the main game window every year from the current saved CSV.
        self.refreshGameState()
    
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
        self.input_field.setPlaceholderText("Enter second button number")
        try:
            self.input_field.returnPressed.disconnect(self.processDistanceInput)
        except Exception:
            pass
        self.input_field.returnPressed.connect(self.processDistanceInput)
        self.input_field.setFocus()
    
    def selectSourceForFleetSend(self, button):
        if button.owner != self.player_owner:
            QMessageBox.warning(self, "Invalid Source", "You can only send fleets from systems you own.")
            return
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
    
    def startDistanceCalculation(self):
        self.distance_inputs = []
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter first system id for distance calculation")
        try:
            self.input_field.returnPressed.disconnect()
        except Exception:
            pass
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
                    raise ValueError("Invalid button number(s).")
                distance = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
                QMessageBox.information(self, "Distance",
                    f"Distance between system {num1} and system {num2} is: {distance:.2f}")
                self.input_field.clear()
                self.input_field.setPlaceholderText("")
                # Remove focus after successful processing.
                self.input_field.clearFocus()
                self.input_field.returnPressed.disconnect(self.processDistanceInput)
                self.distance_inputs = []
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))
    
    def processFleetInput(self):
        try:
            text = self.input_field.text().strip()
            if not text:
                return
            value = int(text)
            # On the first input, ensure the source belongs to the player.
            if len(self.fleet_inputs) == 0:
                if value not in self.buttons:
                    raise ValueError("Invalid system id.")
                source_button = self.buttons[value]
                if source_button.owner != self.player_owner:
                    raise ValueError("You can only send fleets from systems you own.")
            self.fleet_inputs.append(value)
            if len(self.fleet_inputs) == 1:
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter destination system id")
            elif len(self.fleet_inputs) == 2:
                self.input_field.clear()
                self.input_field.setPlaceholderText("Enter number of ships to send")
            elif len(self.fleet_inputs) == 3:
                src, dest, ships_to_send = self.fleet_inputs
                # Check if fleet size is greater than 5 ships.
                if ships_to_send <= 5:
                    self.input_field.clear()
                    self.fleet_inputs = []
                    raise ValueError("Fleet must consist of more than 5 ships to launch.")
                pos1 = self.button_coords.get(src)
                pos2 = self.button_coords.get(dest)
                if pos1 is None or pos2 is None:
                    raise ValueError("Invalid source or destination.")
                # Calculate distance using proper coordinates.
                distance = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
                turns_required = math.ceil(distance)
                source_button = self.buttons.get(src)
                if source_button.current_ships < ships_to_send:
                    raise ValueError("Not enough ships available!")
                source_button.current_ships -= ships_to_send
                if not hasattr(self, "fleets"):
                    self.fleets = []
                fleet_owner = source_button.owner
                self.fleets.append({
                    "source": src,
                    "destination": dest,
                    "ships": ships_to_send,
                    "turns": turns_required,
                    "owner": fleet_owner,
                    "year": self.year
                })
                QMessageBox.information(self, "Fleet Launched",
                    f"Fleet from system {src} to system {dest} with {ships_to_send} ships launched.\nArrival in {turns_required} turn(s).")
                self.input_field.clear()
                self.input_field.setPlaceholderText("")
                # Remove focus after successful processing.
                self.input_field.clearFocus()
                self.input_field.returnPressed.disconnect(self.processFleetInput)
                self.fleet_inputs = []
        except Exception as e:
            QMessageBox.warning(self, "Fleet Input Error", str(e))
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F:
            self.startFleetSend()  # Existing functionality for sending fleets.
        elif event.key() == Qt.Key_S:
            self.toggleSaveGame()  # Save game functionality.
        elif event.key() == Qt.Key_E:
            self.startDistanceCalculation()  # Start distance calculation.
        elif event.key() == Qt.Key_I:
            self.openGameMenuAtStart()  # Open the game menu.
        elif event.key() == Qt.Key_C:
            self.clearAllButtons()  # Clear all buttons from the GUI.
        elif event.key() == Qt.Key_J:
            # Call readyNextTurn when J is pressed.
            self.readyNextTurn()
        else:
            super().keyPressEvent(event)

    def startDistanceInput(self):
        self.distance_inputs = []
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter first button number")
        self.input_field.returnPressed.connect(self.processDistanceInput)
        self.input_field.setFocus()
    
    def startFleetSend(self):
        # Begin fleet sending via the F key.
        self.fleet_inputs = []
        self.input_field.clear()
        self.input_field.setPlaceholderText("Enter source system id for sending fleet")
        try:
            self.input_field.returnPressed.disconnect()
        except Exception:
            pass
        self.input_field.returnPressed.connect(self.processFleetInput)
        self.input_field.setFocus()

    def toggleSaveGame(self):
        try:
            import os, csv
            from datetime import datetime
            base_save_folder = os.path.join(os.getcwd(), "saves")
            if not os.path.exists(base_save_folder):
                os.makedirs(base_save_folder)
            # Create folder name using all participating players separated by commas
            # and append a timestamp in dd.mm.yyyy format.
            timestamp = datetime.now().strftime("%d.%m.%Y")
            folder_name = ",".join(self.owners) + "_" + timestamp
            full_path = os.path.join(base_save_folder, folder_name)
            if not os.path.exists(full_path):
                os.makedirs(full_path)
            
            # Save players, their colors, and readiness.
            players_file = os.path.join(full_path, "players.csv")
            with open(players_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Owner", "Color", "Ready"])
                for owner in self.owners:
                    ready_value = "True" if owner in self.ready_set else "False"
                    writer.writerow([owner, self.owner_colors.get(owner, "#FFFFFF"), ready_value])
            
            # Save systems.
            systems_file = os.path.join(full_path, "systems.csv")
            with open(systems_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Type", "ID", "Current Ships", "Ship Production", "Defense Factor", "Owner", "Grid Position", "Year"])
                for sys_id, button in self.buttons.items():
                    writer.writerow([
                        "System",
                        sys_id,
                        button.current_ships,
                        button.ship_production,
                        button.defense_factor,
                        button.owner,
                        str(button.grid_pos),
                        self.year
                    ])
            
            # Save fleets.
            fleets_file = os.path.join(full_path, "fleets.csv")
            with open(fleets_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Type", "Source", "Destination", "Ships", "Turns", "Owner", "Year"])
                for fleet in self.fleets:
                    writer.writerow([
                        "Fleet",
                        fleet["source"],
                        fleet["destination"],
                        fleet["ships"],
                        fleet["turns"],
                        fleet["owner"],
                        fleet["year"]
                    ])
            
            self.current_save_folder = full_path
            QMessageBox.information(self, "Save Game", f"Game state saved in folder:\n{full_path}")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", str(e))

    def refreshGameState(self):
        """
        Read the current save file and update button (system) values and fleets.
        The saved grid positions are used to re-add buttons to the grid.
        """
        if not hasattr(self, "current_save_file") or not self.current_save_file:
            return  # Nothing to refresh if no file is saved.
        try:
            with open(self.current_save_file, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                rows = list(reader)
            # Find the blank separator between systems and fleets.
            sep_index = None
            for i, row in enumerate(rows):
                if not any(cell.strip() for cell in row):
                    sep_index = i
                    break
            if sep_index is None:
                system_rows = rows[1:]
                fleet_rows = []
            else:
                system_rows = rows[2:sep_index]  # Skip systems header.
                fleet_rows = rows[sep_index+2:] if sep_index+2 < len(rows) else []
            
            owner_colors = {
                "Owner A": "#FFCCCC",
                "Owner B": "#CCFFCC",
                "Owner C": "#CCCCFF",
                "Owner D": "#FFFFCC",
                "Owner E": "#CCFFFF"
            }
            # Update each system (button) from the save.
            for sys_row in system_rows:
                if len(sys_row) >= 8 and sys_row[0] == "System":
                    sys_id = int(sys_row[1])
                    if sys_id in self.buttons:
                        button = self.buttons[sys_id]
                        button.current_ships = int(sys_row[2])
                        button.ship_production = int(sys_row[3])
                        button.defense_factor = float(sys_row[4])
                        button.owner = sys_row[5]
                        try:
                            button.grid_pos = eval(sys_row[6])
                        except Exception:
                            button.grid_pos = None
                        if button.owner == self.player_owner:
                            button.setStyleSheet(f"background-color: {self.player_color};")
                        else:
                            button.setStyleSheet("background-color: #FFFFFF;")
            if system_rows:
                self.year = int(system_rows[0][7])
            
            # Refresh fleets.
            self.fleets.clear()
            for fleet_row in fleet_rows:
                if len(fleet_row) >= 7 and fleet_row[0] == "Fleet":
                    fleet = {
                        "source": int(fleet_row[1]),
                        "destination": int(fleet_row[2]),
                        "ships": int(fleet_row[3]),
                        "turns": int(fleet_row[4]),
                        "owner": fleet_row[5],
                        "year": int(fleet_row[6])
                    }
                    self.fleets.append(fleet)
            # Recreate the grid layout so that buttons are added back in their saved positions.
            self.recreateGridLayout()
        except Exception as e:
            QMessageBox.warning(self, "Refresh Error", str(e))

    def loadGame(self):
        from PyQt5.QtWidgets import QFileDialog, QInputDialog
        import os, csv
        try:
            # Ask user to select a folder containing the saved game.
            folder = QFileDialog.getExistingDirectory(self, "Load Game Folder")
            if not folder:
                QMessageBox.information(self, "Load Game", "No folder selected, load cancelled.")
                return
            
            # Load players, their colors, and readiness.
            players_file = os.path.join(folder, "players.csv")
            if not os.path.exists(players_file):
                QMessageBox.warning(self, "Load Error", "Players file not found!")
                return
            self.owners = []
            self.owner_colors = {}
            self.ready_set = set()  # Reset readiness.
            with open(players_file, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                for row in reader:
                    if len(row) >= 3:
                        owner, color, ready_str = row[0], row[1], row[2]
                        self.owners.append(owner)
                        self.owner_colors[owner] = color
                        if ready_str.lower() == "true":
                            self.ready_set.add(owner)
            
            # Present a dropdown menu listing all players from the save.
            current, ok = QInputDialog.getItem(self, "Choose Your Player",
                                               "Select your player:", self.owners, 0, False)
            if ok and current:
                self.player_owner = current
            else:
                # Default to first owner if none is chosen.
                self.player_owner = self.owners[0] if self.owners else "Default_Player"
                if self.player_owner not in self.owner_colors:
                    self.owner_colors[self.player_owner] = "#{:06X}".format(random.randint(0, 0xFFFFFF))
            self.player_color = self.owner_colors.get(self.player_owner, "#FFFFFF")
            
            # Load systems.
            systems_file = os.path.join(folder, "systems.csv")
            if not os.path.exists(systems_file):
                QMessageBox.warning(self, "Load Error", "Systems file not found!")
                return
            with open(systems_file, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # Skip header.
                for sys_row in reader:
                    if len(sys_row) >= 8 and sys_row[0] == "System":
                        sys_id = int(sys_row[1])
                        if sys_id in self.buttons:
                            button = self.buttons[sys_id]
                            button.current_ships = int(sys_row[2])
                            button.ship_production = int(sys_row[3])
                            button.defense_factor = float(sys_row[4])
                            button.owner = sys_row[5]
                            grid_pos_str = sys_row[6].strip()
                            if grid_pos_str and grid_pos_str != "None":
                                try:
                                    new_pos = eval(grid_pos_str)
                                    if isinstance(new_pos, tuple) and len(new_pos)==2:
                                        button.grid_pos = new_pos
                                        self.button_coords[sys_id] = new_pos
                                    else:
                                        raise ValueError("grid_pos is not a valid tuple")
                                except Exception:
                                    button.grid_pos = self.button_coords.get(sys_id)
                            else:
                                button.grid_pos = self.button_coords.get(sys_id)
                            
                            # Set button color based on its owner.
                            if button.owner in self.owner_colors:
                                button.setStyleSheet(f"background-color: {self.owner_colors[button.owner]};")
                            else:
                                button.setStyleSheet("background-color: #FFFFFF;")
            
            # Set game year based on first system row.
            with open(systems_file, "r", newline="") as csvfile:
                reader = list(csv.reader(csvfile))
                if len(reader) > 1:
                    self.year = int(reader[1][7])
            
            # Load fleets.
            fleets_file = os.path.join(folder, "fleets.csv")
            if os.path.exists(fleets_file):
                with open(fleets_file, "r", newline="") as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)  # Skip header.
                    self.fleets.clear()
                    for fleet_row in reader:
                        if len(fleet_row) >= 7 and fleet_row[0] == "Fleet":
                            fleet = {
                                "source": int(fleet_row[1]),
                                "destination": int(fleet_row[2]),
                                "ships": int(fleet_row[3]),
                                "turns": int(fleet_row[4]),
                                "owner": fleet_row[5],
                                "year": int(fleet_row[6])
                            }
                            self.fleets.append(fleet)
            else:
                self.fleets.clear()

            # Recreate grid layout and force GUI update.
            self.recreateGridLayout()
            self.update()
            self.repaint()

            QMessageBox.information(self, "Load Game", f"Game loaded successfully from folder:\n{folder}")
            self.showMaximized()
        except Exception as e:
            QMessageBox.warning(self, "Load Error", str(e))
            print("Load error:", e)

    def clearAllButtons(self):
        """
        Clear all buttons from the GUI by removing them from the grid layout.
        Optionally, clear the self.buttons dictionary.
        """
        # Remove all items from the grid layout.
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        # Optionally clear the buttons dictionary (if you want to reset the button storage).
        self.buttons.clear()
        self.update()
        self.repaint()

    def readyNextTurn(self):
        """
        Instead of immediately processing the next turn, prompt for confirmation.
        Each player must confirm readiness before advancing the game year.
        """
        # Compute list of players who haven't confirmed readiness.
        non_ready = [owner for owner in self.owners if owner not in self.ready_set]
        if non_ready:
            current, ok = QInputDialog.getItem(self, "Player Confirmation",
                                               "Select a player confirming readiness:", non_ready, 0, False)
            if ok and current:
                self.ready_set.add(current)
                QMessageBox.information(self, "Ready Confirmation",
                                        f"Player {current} is ready for the next turn.")
        # When all players are ready, clear the set and call nextTurn.
        if len(self.ready_set) == len(self.owners):
            self.ready_set.clear()  # Reset readiness for the next year.
            self.nextTurn()

    def updateInfoLabel(self):
        """Update the info label with the current owner and game year."""
        self.info_label.setText(f"Owner: {self.player_owner} | Game Year: {self.year}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # --- Show the game menu first ---
    menu_dialog = QDialog()
    menu_dialog.setWindowTitle("Game Menu")
    vbox = QVBoxLayout(menu_dialog)
    
    # Dictionary to store the player's choice.
    choice = {"option": None}
    
    btnNew = QPushButton("Start New Game")
    btnLoad = QPushButton("Load Game")
    btnExit = QPushButton("Exit")
    
    def newGame():
        choice["option"] = "new"
        menu_dialog.accept()
    
    def loadGame():
        choice["option"] = "load"
        menu_dialog.accept()
    
    def exitGame():
        choice["option"] = "exit"
        menu_dialog.reject()
    
    btnNew.clicked.connect(newGame)
    btnLoad.clicked.connect(loadGame)
    btnExit.clicked.connect(exitGame)
    
    vbox.addWidget(btnNew)
    vbox.addWidget(btnLoad)
    vbox.addWidget(btnExit)
    
    if menu_dialog.exec_() == QDialog.Rejected or choice["option"] == "exit":
        sys.exit(0)
    
    # --- Now create the main game window ---
    if choice["option"] == "new":
        # Ask for number of systems.
        num_systems, ok = QInputDialog.getInt(None, "Systems", "Enter number of systems:", 80, 10, 200)
        if not ok:
            sys.exit(0)
        # Ask for number of players.
        num_players, ok = QInputDialog.getInt(None, "Players", "Enter number of players:", 2, 1, 10)
        if not ok:
            sys.exit(0)
        # Collect owner names.
        players = []
        for i in range(num_players):
            name, ok = QInputDialog.getText(None, "Player Name", f"Enter name for player {i+1}:")
            if ok and name.strip():
                players.append(name.strip())
            else:
                players.append(f"Player_{i+1}")
        # Create the game window with the chosen parameters.
        window = ButtonGrid(num_buttons=num_systems, owners=players)
        # Let the user choose which owner they will be.
        window.choosePlayerOwner()
        # Randomly assign one system (planet) to the current player.
        window.assignStartingPlanets()
    elif choice["option"] == "load":
        # Create a default instance. (The saved game will update systems and fleets.)
        window = ButtonGrid()
        window.loadGame()
    
    window.showMaximized()
    sys.exit(app.exec_())
