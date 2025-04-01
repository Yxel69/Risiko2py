import sys
import os
import random
import math
import csv
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QGridLayout, 
    QVBoxLayout, QLineEdit, QHBoxLayout, QMenu, QMessageBox, QInputDialog, QDialog, QFileDialog, QLabel, QStackedWidget)
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtCore import Qt, QEvent
from functools import partial
from worldgen import load_worldgen_options

# Global variable for keeping the chosen load folder.
LOAD_FOLDER = None

class ButtonGrid(QWidget):
    def __init__(self, num_buttons=80, owners=None):
        super().__init__()
        self.setWindowIcon(QIcon("designs/icon.png"))  # Set your custom icon.
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
        self.ready_set = set()   # Track which players have confirmed readiness.
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        # Info label displays current owner and game year.
        self.info_label = QLabel(f"Owner: {getattr(self, 'player_owner', 'N/A')} | Game Year: {self.year}")
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

            # Initialize button properties.
            button.current_ships = 0
            button.ship_production = random.randint(1, 10)
            button.defense_factor = round(random.uniform(0.7, 1.0), 2)
            button.owner = None
            button.setStyleSheet("background-color: #FFFFFF;")
            
            self.grid.addWidget(button, pos[0], pos[1])
            button.installEventFilter(self)
        main_layout.addLayout(self.grid)
        
        # Input field and control buttons.
        hbox = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setMinimumHeight(40)
        next_turn_button = QPushButton("Next Turn")
        next_turn_button.setMinimumHeight(40)
        change_owner_button = QPushButton("Change Owner")
        change_owner_button.setMinimumHeight(40)
        hbox.addWidget(self.input_field)
        hbox.addWidget(next_turn_button)
        hbox.addWidget(change_owner_button)
        next_turn_button.clicked.connect(self.readyNextTurn)
        change_owner_button.clicked.connect(self.changeOwner)
        main_layout.addLayout(hbox)
        
        self.setLayout(main_layout)
        self.input_field.clearFocus()

    def changeOwner(self):
        current, ok = QInputDialog.getItem(self, "Change Current Owner",
                                           "Select your new owner:", self.owners, 0, False)
        if ok and current:
            self.player_owner = current
            self.player_color = self.owner_colors.get(current, "#FFFFFF")
            QMessageBox.information(self, "Owner Changed",
                                    f"Your current owner is now '{current}' with color {self.player_color}.")

    def recreateGridLayout(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        for sys_id, button in self.buttons.items():
            pos = button.grid_pos if button.grid_pos is not None else self.button_coords.get(sys_id)
            if pos:
                self.grid.addWidget(button, pos[0], pos[1])

    def openGameMenuAtStart(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Game Menu")
        layout = QVBoxLayout()
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
        if self.owners:
            current, ok = QInputDialog.getItem(self, "Choose Your Owner",
                                               "Select your owner:", self.owners, 0, False)
            if ok and current:
                self.player_owner = current
            else:
                self.player_owner = random.choice(self.owners)
        else:
            self.player_owner = "Default_Player"
        self.player_color = self.owner_colors.get(self.player_owner, "#FFFFFF")
        QMessageBox.information(self, "Player Owner",
            f"You are '{self.player_owner}' with color {self.player_color}")
        self.updateInfoLabel()

    def assignStartingPlanets(self, galaxy_index, total_galaxies, owner_assignments):
        """
        Assign starting planets evenly across all galaxies.
        Only assign a starting planet for an owner if that owner’s chosen galaxy matches galaxy_index.
        """
        available_ids = list(self.buttons.keys())
        random.shuffle(available_ids)
        self.starting_planets = {}
        for owner in self.owners:
            # Only assign a starting planet in this galaxy for owners preselected for it.
            if owner_assignments.get(owner) == galaxy_index:
                if not available_ids:
                    break
                sys_id = available_ids.pop()
                self.starting_planets[owner] = sys_id
                button = self.buttons[sys_id]
                button.owner = owner
                button.current_ships = 250
                button.ship_production = 10
                button.defense_factor = 0.5
                button.setStyleSheet(f"background-color: {self.owner_colors[owner]};")
                QMessageBox.information(self, "Starting Planet Assigned",
                                        f"System {sys_id} in Galaxy {galaxy_index + 1} is now assigned to {owner}.")

    def assignPiratePlanets(self):
        for sys_id, button in self.buttons.items():
            if button.owner is None and random.random() < 0.35:
                button.owner = "Pirates"
                button.setStyleSheet("background-color: #FFFFFF;")

    def nextTurn(self):
        for num, button in self.buttons.items():
            if button.owner is not None:
                button.current_ships += button.ship_production
        QMessageBox.information(self, "Turn Ended", "Production added and fleets processed!")
        self.year += 1
        self.updateInfoLabel()
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
                if ships_to_send <= 5:
                    self.input_field.clear()
                    self.fleet_inputs = []
                    raise ValueError("Fleet must consist of more than 5 ships to launch.")
                pos1 = self.button_coords.get(src)
                pos2 = self.button_coords.get(dest)
                if pos1 is None or pos2 is None:
                    raise ValueError("Invalid source or destination.")
                distance = math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
                turns_required = math.ceil(distance)
                source_button = self.buttons.get(src)
                if source_button.current_ships < ships_to_send:
                    raise ValueError("Not enough ships available!")
                source_button.current_ships -= ships_to_send
                self.fleets.append({
                    "source": src,
                    "destination": dest,
                    "ships": ships_to_send,
                    "turns": turns_required,
                    "owner": source_button.owner,
                    "year": self.year
                })
                QMessageBox.information(self, "Fleet Launched",
                    f"Fleet from system {src} to system {dest} with {ships_to_send} ships launched.\nArrival in {turns_required} turn(s).")
                self.input_field.clear()
                self.input_field.setPlaceholderText("")
                self.input_field.clearFocus()
                self.input_field.returnPressed.disconnect(self.processFleetInput)
                self.fleet_inputs = []
        except Exception as e:
            QMessageBox.warning(self, "Fleet Input Error", str(e))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F:
            self.startFleetSend()
        elif event.key() == Qt.Key_S:
            self.toggleSaveGame()
        elif event.key() == Qt.Key_E:
            self.startDistanceCalculation()
        elif event.key() == Qt.Key_I:
            self.openGameMenuAtStart()
        elif event.key() == Qt.Key_C:
            self.changeOwner()
        elif event.key() == Qt.Key_J:
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
            from datetime import datetime
            base_save_folder = os.path.join(os.getcwd(), "saves")
            if not os.path.exists(base_save_folder):
                os.makedirs(base_save_folder)
            timestamp = datetime.now().strftime("%d.%m.%Y")
            folder_name = ",".join(self.owners) + "_" + timestamp
            full_path = os.path.join(base_save_folder, folder_name)
            if not os.path.exists(full_path):
                os.makedirs(full_path)
            players_file = os.path.join(full_path, "players.csv")
            with open(players_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Owner", "Color", "Ready"])
                for owner in self.owners:
                    ready_value = "True" if owner in self.ready_set else "False"
                    writer.writerow([owner, self.owner_colors.get(owner, "#FFFFFF"), ready_value])
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
        if not hasattr(self, "current_save_file") or not self.current_save_file:
            return
        try:
            with open(self.current_save_file, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                rows = list(reader)
            sep_index = None
            for i, row in enumerate(rows):
                if not any(cell.strip() for cell in row):
                    sep_index = i
                    break
            if sep_index is None:
                system_rows = rows[1:]
                fleet_rows = []
            else:
                system_rows = rows[2:sep_index]
                fleet_rows = rows[sep_index+2:] if sep_index+2 < len(rows) else []
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
            self.recreateGridLayout()
        except Exception as e:
            QMessageBox.warning(self, "Refresh Error", str(e))

    def readyNextTurn(self):
        non_ready = [owner for owner in self.owners if owner not in self.ready_set]
        if non_ready:
            current, ok = QInputDialog.getItem(self, "Player Confirmation",
                                               "Select a player confirming readiness:", non_ready, 0, False)
            if ok and current:
                self.ready_set.add(current)
                QMessageBox.information(self, "Ready Confirmation",
                                        f"Player {current} is ready for the next turn.")
        if len(self.ready_set) == len(self.owners):
            self.ready_set.clear()
            self.nextTurn()

    def updateInfoLabel(self):
        self.info_label.setText(f"Owner: {self.player_owner} | Game Year: {self.year}")

# New integrated class: MultiGrid combines multiple ButtonGrids and handles arrow key navigation.
class MultiGrid(QWidget):
    def __init__(self, grids):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)  # Accept key events
        self.setFocus()  # Request initial focus
        self.stack = QStackedWidget()
        self.grids = grids

        # Add each ButtonGrid to the stack
        for grid in grids:
            self.stack.addWidget(grid)

        # Create navigation buttons
        self.prev_button = QPushButton("Previous Galaxy")
        self.next_button = QPushButton("Next Galaxy")
        self.prev_button.setFixedWidth(150)
        self.next_button.setFixedWidth(150)

        # Connect navigation buttons to methods
        self.prev_button.clicked.connect(self.showPreviousGalaxy)
        self.next_button.clicked.connect(self.showNextGalaxy)

        # Layout for the navigation buttons and the stack
        layout = QHBoxLayout()
        layout.addWidget(self.prev_button)
        layout.addWidget(self.stack, stretch=1)
        layout.addWidget(self.next_button)
        self.setLayout(layout)

    def showPreviousGalaxy(self):
        current_index = self.stack.currentIndex()
        new_index = (current_index - 1) % self.stack.count()
        self.stack.setCurrentIndex(new_index)

    def showNextGalaxy(self):
        current_index = self.stack.currentIndex()
        new_index = (current_index + 1) % self.stack.count()
        self.stack.setCurrentIndex(new_index)

    def keyPressEvent(self, event):
        current_grid = self.grids[self.stack.currentIndex()]
        key = event.key()
        if key == Qt.Key_Left:
            self.showPreviousGalaxy()
        elif key == Qt.Key_Right:
            self.showNextGalaxy()
        elif key == Qt.Key_S:
            # Save all galaxies and global player data
            self.saveGame()
        elif key == Qt.Key_J:
            # Trigger ready next turn on the current grid
            current_grid.readyNextTurn()
        elif key == Qt.Key_F:
            # Start fleet sending on the current grid
            current_grid.startFleetSend()
        elif key == Qt.Key_E:
            # Start distance calculation on the current grid
            current_grid.startDistanceCalculation()
        elif key == Qt.Key_I:
            # Open the game menu (e.g., at start) on the current grid
            current_grid.openGameMenuAtStart()
        elif key == Qt.Key_C:
            # Change the current owner on the current grid
            current_grid.changeOwner()
        else:
            super().keyPressEvent(event)

    def saveGame(self):
        from datetime import datetime
        base_save_folder = os.path.join(os.getcwd(), "saves")
        if not os.path.exists(base_save_folder):
            os.makedirs(base_save_folder)
        timestamp = datetime.now().strftime("%d.%m.%Y_%H%M%S")
        save_folder = os.path.join(base_save_folder, f"save_{timestamp}")
        os.makedirs(save_folder)
        # Save global players info (assumed same for all grids)
        players_file = os.path.join(save_folder, "players.csv")
        with open(players_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Owner", "Color"])
            for owner in self.grids[0].owners:
                writer.writerow([owner, self.grids[0].owner_colors.get(owner, "#FFFFFF")])
        # Save each galaxy’s state
        for idx, grid in enumerate(self.grids):
            galaxy_folder = os.path.join(save_folder, f"galaxy_{idx}")
            os.makedirs(galaxy_folder)
            # Save systems info
            systems_file = os.path.join(galaxy_folder, "systems.csv")
            with open(systems_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Type", "ID", "Current Ships", "Ship Production", "Defense Factor", "Owner", "Grid Position", "Year"])
                for sys_id, button in grid.buttons.items():
                    writer.writerow(["System", sys_id, button.current_ships, button.ship_production,
                                     button.defense_factor, button.owner, str(button.grid_pos), grid.year])
            # Save fleets info
            fleets_file = os.path.join(galaxy_folder, "fleets.csv")
            with open(fleets_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Type", "Source", "Destination", "Ships", "Turns", "Owner", "Year"])
                for fleet in grid.fleets:
                    writer.writerow(["Fleet", fleet["source"], fleet["destination"], fleet["ships"],
                                     fleet["turns"], fleet["owner"], fleet["year"]])
        QMessageBox.information(self, "Save Game", f"Game state saved in folder:\n{save_folder}")

    # New method: Load game state for all galaxies.
    def loadGame(self):
        global LOAD_FOLDER
        if LOAD_FOLDER is None:
            folder = QFileDialog.getExistingDirectory(self, "Select Save Folder", os.getcwd())
            if not folder:
                return
            LOAD_FOLDER = folder
        else:
            folder = LOAD_FOLDER
        # Load global players info
        players_file = os.path.join(folder, "players.csv")
        players = []
        owner_colors = {}
        try:
            with open(players_file, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # skip header
                for row in reader:
                    if len(row) >= 2:
                        players.append(row[0])
                        owner_colors[row[0]] = row[1]
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load players info: {e}")
            return
        # Get saved galaxy folders (assumed to be galaxy_0, galaxy_1, …)
        galaxy_dirs = [d for d in os.listdir(folder) if d.startswith("galaxy_")]
        galaxy_dirs.sort(key=lambda d: int(d.split("_")[1]))
        if len(galaxy_dirs) != len(self.grids):
            QMessageBox.warning(self, "Load Error", "Mismatch in number of saved galaxies versus current game.")
            return
        # Load each galaxy
        for idx, d in enumerate(galaxy_dirs):
            galaxy_folder = os.path.join(folder, d)
            # Load systems
            systems_file = os.path.join(galaxy_folder, "systems.csv")
            try:
                with open(systems_file, "r", newline="") as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)  # skip header
                    for row in reader:
                        if len(row) >= 8 and row[0] == "System":
                            sys_id = int(row[1])
                            if sys_id in self.grids[idx].buttons:
                                button = self.grids[idx].buttons[sys_id]
                                button.current_ships = int(row[2])
                                button.ship_production = int(row[3])
                                button.defense_factor = float(row[4])
                                button.owner = row[5]
                                try:
                                    button.grid_pos = eval(row[6])
                                except Exception:
                                    button.grid_pos = None
                                if button.owner in owner_colors:
                                    button.setStyleSheet(f"background-color: {owner_colors[button.owner]};")
                                else:
                                    button.setStyleSheet("background-color: #FFFFFF;")
                                self.grids[idx].year = int(row[7])
            except Exception as e:
                QMessageBox.warning(self, "Load Error", f"Failed to load systems for galaxy {idx}: {e}")
            # Load fleets
            fleets_file = os.path.join(galaxy_folder, "fleets.csv")
            try:
                with open(fleets_file, "r", newline="") as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)
                    self.grids[idx].fleets.clear()
                    for row in reader:
                        if len(row) >= 7 and row[0] == "Fleet":
                            fleet = {
                                "source": int(row[1]),
                                "destination": int(row[2]),
                                "ships": int(row[3]),
                                "turns": int(row[4]),
                                "owner": row[5],
                                "year": int(row[6])
                            }
                            self.grids[idx].fleets.append(fleet)
            except Exception as e:
                QMessageBox.warning(self, "Load Error", f"Failed to load fleets for galaxy {idx}: {e}")
            self.grids[idx].recreateGridLayout()
        QMessageBox.information(self, "Load Game", "Game state loaded successfully.")

def loadGameFromFile():
    global LOAD_FOLDER
    if LOAD_FOLDER is None:
        folder = QFileDialog.getExistingDirectory(None, "Select Save Folder", os.getcwd())
        if not folder:
            sys.exit(0)
        LOAD_FOLDER = folder
    else:
        folder = LOAD_FOLDER
    # Load global players info
    players_file = os.path.join(folder, "players.csv")
    players = []
    owner_colors = {}
    try:
        with open(players_file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # skip header
            for row in reader:
                if len(row) >= 2:
                    players.append(row[0])
                    owner_colors[row[0]] = row[1]
    except Exception as e:
        QMessageBox.warning(None, "Load Error", f"Failed to load players info: {e}")
        sys.exit(0)
    # Get saved galaxy folders (assumed to be named galaxy_0, galaxy_1, …)
    galaxy_dirs = [d for d in os.listdir(folder) if d.startswith("galaxy_")]
    galaxy_dirs.sort(key=lambda d: int(d.split("_")[1]))
    grids = []
    for gdir in galaxy_dirs:
        galaxy_folder = os.path.join(folder, gdir)
        systems_file = os.path.join(galaxy_folder, "systems.csv")
        systems_data = []
        try:
            with open(systems_file, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # header line
                for row in reader:
                    if len(row) >= 8 and row[0] == "System":
                        systems_data.append(row)
        except Exception as e:
            QMessageBox.warning(None, "Load Error", f"Failed to load systems for {gdir}: {e}")
            continue
        # Determine number of systems
        num_buttons = max(int(row[1]) for row in systems_data) if systems_data else 80
        # Create a grid for this galaxy using the loaded players
        grid = ButtonGrid(num_buttons=num_buttons, owners=players)
        try:
            grid.year = int(systems_data[0][7])
        except Exception:
            grid.year = 1
        # Update each button's state
        for row in systems_data:
            try:
                sys_id = int(row[1])
                if sys_id in grid.buttons:
                    button = grid.buttons[sys_id]
                    button.current_ships = int(row[2])
                    button.ship_production = int(row[3])
                    button.defense_factor = float(row[4])
                    button.owner = row[5]
                    try:
                        button.grid_pos = eval(row[6])
                    except Exception:
                        button.grid_pos = None
                    if button.owner in owner_colors:
                        button.setStyleSheet(f"background-color: {owner_colors[button.owner]};")
                    else:
                        button.setStyleSheet("background-color: #FFFFFF;")
            except Exception as e:
                QMessageBox.warning(None, "Load Error", f"Error in a system row of {gdir}: {e}")
        # Load fleets data
        fleets_file = os.path.join(galaxy_folder, "fleets.csv")
        try:
            with open(fleets_file, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # skip header
                grid.fleets.clear()
                for row in reader:
                    if len(row) >= 7 and row[0] == "Fleet":
                        fleet = {
                            "source": int(row[1]),
                            "destination": int(row[2]),
                            "ships": int(row[3]),
                            "turns": int(row[4]),
                            "owner": row[5],
                            "year": int(row[6])
                        }
                        grid.fleets.append(fleet)
        except Exception as e:
            QMessageBox.warning(None, "Load Error", f"Failed to load fleets for {gdir}: {e}")
        grid.recreateGridLayout()
        grids.append(grid)
    return grids

# --- Main block ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Game menu dialog
    menu_dialog = QDialog()
    menu_dialog.setWindowTitle("Game Menu")
    vbox = QVBoxLayout(menu_dialog)

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

    grids = []
    if choice["option"] == "load":
        grids = loadGameFromFile()
    elif choice["option"] == "new":
        # Prompt for number of galaxies
        num_galaxies, ok = QInputDialog.getInt(None, "Galaxies",
                                               "Enter number of galaxies (button grids):", 1, 1, 10)
        if not ok:
            sys.exit(0)

        # Prompt for number of systems per galaxy
        num_systems, ok = QInputDialog.getInt(None, "Systems per Galaxy",
                                              "Enter number of systems per galaxy:", 80, 10, 200)
        if not ok:
            sys.exit(0)

        # Prompt for number of players
        num_players, ok = QInputDialog.getInt(None, "Players",
                                              "Enter number of players:", 2, 1, 10)
        if not ok:
            sys.exit(0)

        # Get player names
        players = []
        for i in range(num_players):
            name, ok = QInputDialog.getText(None, "Player Name", f"Enter name for player {i + 1}:")
            if ok and name.strip():
                players.append(name.strip())
            else:
                players.append(f"Player_{i + 1}")

        # *** Ask the human player to choose an owner only once ***
        chosen_owner, ok = QInputDialog.getItem(None, "Choose Your Owner",
                                  "Select your owner (this stays the same across galaxies):", players, 0, False)
        if not ok:
            sys.exit(0)
        # Update all players so that the human player owner is consistent.
        # (If needed, you could also mark the chosen_owner in each grid.)
        # Here we leave players as is but assume the chosen_owner is part of players.

        # Precompute an assignment of each owner to one galaxy.
        # For simplicity, if there are at least as many galaxies as players,
        # assign each owner to a distinct galaxy; otherwise, cycle through.
        owner_assignments = {}
        for i, owner in enumerate(players):
            owner_assignments[owner] = i % num_galaxies

        # Create ButtonGrids (each galaxy)
        for galaxy_index in range(num_galaxies):
            grid = ButtonGrid(num_buttons=num_systems, owners=players)
            # Set the chosen (human) owner in each grid (so it stays the same)
            grid.player_owner = chosen_owner
            grid.player_color = grid.owner_colors.get(chosen_owner, "#FFFFFF")
            # Assign starting planets using the precomputed owner_assignments.
            grid.assignStartingPlanets(galaxy_index, num_galaxies, owner_assignments)
            grid.assignPiratePlanets()
            grids.append(grid)

    # Wrap the grids in MultiGrid
    main_window = MultiGrid(grids)
    if choice["option"] == "load":
        main_window.loadGame()  # call loadGame on the MultiGrid instance
    main_window.showMaximized()
    sys.exit(app.exec_())
