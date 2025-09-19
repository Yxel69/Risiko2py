from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGridLayout, QMenu,
    QMessageBox, QInputDialog, QDialog, QFileDialog, QStackedWidget, QListWidget, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QIcon, QGuiApplication, QColor
import random
import math
import os
import csv
import requests

# --- new helper ----------------------------------------------------------------
def invert_color(hex_color: str) -> str:
    """
    Return the literal inverse color of hex_color (e.g. #112233 -> #EEDDCC).
    Accepts '#RRGGBB' (also tolerates without '#').
    """
    if not hex_color:
        return "#000000"
    c = hex_color.lstrip('#')
    if len(c) == 3:
        c = ''.join(2 * ch for ch in c)
    try:
        r = 255 - int(c[0:2], 16)
        g = 255 - int(c[2:4], 16)
        b = 255 - int(c[4:6], 16)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#000000"

class ButtonGrid(QWidget):
    def __init__(self, num_buttons=80, owners=None, button_coords=None, owner_colors=None):
        super().__init__()
        self.setWindowIcon(QIcon("designs/icon.png"))
        self.year = 1
        self.num_buttons = num_buttons
        self.owners = owners if owners is not None else ["Default_Player"]
        # Use provided owner_colors or generate
        if owner_colors:
            self.owner_colors = owner_colors.copy()
        else:
            self.owner_colors = {owner: "#{:06X}".format(random.randint(0, 0xFFFFFF)) for owner in self.owners}
        # Use provided button_coords or generate
        if button_coords:
            self.button_coords = {int(k): tuple(v) for k, v in button_coords.items()}
        else:
            rows, cols = 40, 15
            positions = [(row, col) for row in range(rows) for col in range(cols)]
            random.shuffle(positions)
            self.button_coords = {i+1: positions[i] for i in range(self.num_buttons)}
        self.buttons = {}
        self.fleets = []
        self.ready_set = set()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.info_label = QLabel(f"Owner: {getattr(self, 'player_owner', 'N/A')} | Game Year: {getattr(self, 'year', 1)}")
        main_layout.addWidget(self.info_label)
        self.year_label = QLabel(f"Year: {getattr(self, 'year', 1)}")
        main_layout.addWidget(self.year_label)
        self.readiness_label = QLabel("Player readiness: ")
        main_layout.addWidget(self.readiness_label)

        self.grid = QGridLayout()
        for i in range(self.num_buttons):
            button = QPushButton(str(i+1))
            pos = self.button_coords[i+1]
            button.grid_pos = pos
            self.buttons[i+1] = button
            button.current_ships = 0
            button.ship_production = random.randint(1, 10)
            button.defense_factor = round(random.uniform(0.7, 1.0), 2)
            button.owner = None
            # Ensure unowned buttons get explicit bg+text so text is visible
            self.update_button_color(button)
            self.grid.addWidget(button, pos[0], pos[1])
            button.installEventFilter(self)
        main_layout.addLayout(self.grid)

        hbox = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setMinimumHeight(40)
        self.next_turn_button = QPushButton("Next Turn")
        self.next_turn_button.setMinimumHeight(40)
        self.next_turn_button.clicked.connect(self.readyNextTurn)
        change_owner_button = QPushButton("Change Owner")
        change_owner_button.setMinimumHeight(40)
        change_owner_button.clicked.connect(self.changeOwner)
        hbox.addWidget(self.input_field)
        hbox.addWidget(self.next_turn_button)
        hbox.addWidget(change_owner_button)
        main_layout.addLayout(hbox)

        self.setLayout(main_layout)
        self.input_field.clearFocus()
        self.input_field.setFocus()

    def changeOwner(self):
        current, ok = QInputDialog.getItem(self, "Change Current Owner",
                                           "Select your new owner:", self.owners, 0, False)
        if ok and current:
            self.player_owner = current
            self.player_color = self.owner_colors.get(current, "#FFFFFF")
            QMessageBox.information(self, "Owner Changed",
                                    f"Your current owner is now '{current}' with color {self.player_color}.")
            self.updateInfoLabel()
            # --- Update next turn button color according to readiness ---
            self.update_next_turn_button_color()

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

    def assignStartingPlanets(self):
        """
        Assign each player a unique starting planet.
        Set fleet count to 250, production to 10, defense to 1.0.
        """
        available_ids = list(self.buttons.keys())
        random.shuffle(available_ids)
        self.starting_planets = {}
        for owner in self.owners:
            if not available_ids:
                break
            sys_id = available_ids.pop()
            self.starting_planets[owner] = sys_id
            button = self.buttons[sys_id]
            button.owner = owner
            button.current_ships = 250
            button.ship_production = 10
            button.defense_factor = 1.0
            self.update_button_color(button)
            # Optional: show info
            # QMessageBox.information(self, "Starting Planet Assigned",
            #     f"System {sys_id} is now assigned to {owner}.")

    def assignPiratePlanets(self):
        for sys_id, button in self.buttons.items():
            if button.owner is None and random.random() < 0.35:
                button.owner = "Pirates"
                self.update_button_color(button)

    def nextTurn(self):
        # Increase production on each system.
        for num, button in self.buttons.items():
            if button.owner is not None:
                button.current_ships += button.ship_production

        # Process fleets: decrement turns and deliver if arrival reached.
        fleets_to_remove = []
        for fleet in list(self.fleets):
            fleet["turns"] -= 1
            if fleet["turns"] <= 0:
                dest_button = self.buttons.get(fleet["destination"])
                if dest_button:
                    # If the destination is unowned or owned by the same player, add ships.
                    if dest_button.owner == fleet["owner"] or dest_button.owner is None:
                        dest_button.current_ships += fleet["ships"]
                        dest_button.owner = fleet["owner"]
                        self.update_button_color(dest_button)
                    else:
                        # Simple combat logic: if fewer ships, take over.
                        if fleet["ships"] > dest_button.current_ships:
                            dest_button.owner = fleet["owner"]
                            dest_button.current_ships = fleet["ships"] - dest_button.current_ships
                            self.update_button_color(dest_button)
                        else:
                            dest_button.current_ships -= fleet["ships"]
                fleets_to_remove.append(fleet)
        
        # Remove processed fleets.
        for f in fleets_to_remove:
            self.fleets.remove(f)

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
        self.input_field.setPlaceholderText("Enter destination system id")
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
                # --- SEND TO SERVER ---
                if hasattr(self, 'game_id') and hasattr(self, 'client'):
                    headers = {"Authorization": f"Bearer {self.client.token}"}
                    data = {
                        "game_id": self.game_id,
                        "source": src,
                        "destination": dest,
                        "ships": ships_to_send,
                        "owner": source_button.owner
                    }
                    response = requests.post(f"{self.client.api_url}/game/send_fleet", json=data, headers=headers)
                    if response.status_code == 200:
                        new_state = response.json().get("state")
                        self.update_from_state(new_state)
                        QMessageBox.information(self, "Fleet Launched", "Fleet sent to server!")
                    else:
                        QMessageBox.warning(self, "Fleet Error", f"Failed to send fleet: {response.text}")
                else:
                    QMessageBox.warning(self, "Error", "Game ID or client not set.")
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
            self.input_field.returnPressed.disconnect(self.processDistanceInput)
        except Exception:
            pass
        try:
            self.input_field.returnPressed.disconnect(self.processFleetInput)
        except Exception:
            pass
        self.input_field.returnPressed.connect(self.processFleetInput)
        self.input_field.setFocus()
    
    def readyNextTurn(self):
        if hasattr(self, 'game_id') and hasattr(self, 'client'):
            headers = {"Authorization": f"Bearer {self.client.token}"}
            data = {"game_id": self.game_id, "player": self.player_owner}
            response = requests.post(f"{self.client.api_url}/game/ready", json=data, headers=headers)
            if response.status_code == 200:
                new_state = response.json().get("state")
                self.update_from_state(new_state)
                # --- Set button green after declaring readiness ---
                bg = "#1a7f1a"
                self.next_turn_button.setStyleSheet(f"background-color: {bg}; color: {invert_color(bg)};")
            else:
                QMessageBox.warning(self, "Error", f"Failed to mark ready: {response.text}")
        else:
            QMessageBox.warning(self, "Error", "Game ID or client not set.")

    def declareReadiness(self):
        if hasattr(self, 'game_id') and hasattr(self, 'client'):
            headers = {"Authorization": f"Bearer {self.client.token}"}
            data = {"game_id": self.game_id, "player": self.player_owner}
            response = requests.post(f"{self.client.api_url}/game/ready", json=data, headers=headers)
            if response.status_code == 200:
                new_state = response.json().get("state")
                self.update_from_state(new_state)
                self.show_readiness_status(new_state)
            else:
                QMessageBox.warning(self, "Error", f"Failed to declare readiness: {response.text}")
        else:
            QMessageBox.warning(self, "Error", "Game ID or client not set.")

    def show_readiness_status(self, state):
        import json
        # If state is a JSON string, parse it
        if isinstance(state, str):
            state = json.loads(state)
        # You may need to fetch players from the server or keep them in self.owners
        # Here, assume you have a list of players with 'owner' and 'ready'
        players = state.get("players", [])
        if not players and hasattr(self, "owners"):
            # fallback: try to get from self.owners and ready_set
            players = [{"owner": o, "ready": o in getattr(self, "ready_set", set())} for o in self.owners]
        status = []
        all_ready = True
        for p in players:
            name = p["owner"] if isinstance(p, dict) else str(p)
            ready = p.get("ready", False) if isinstance(p, dict) else False
            status.append(f"{name}: {'✔' if ready else '✘'}")
            if not ready:
                all_ready = False
        self.readiness_label.setText("Player readiness: " + ", ".join(status))
        if all_ready:
            QMessageBox.information(self, "Next Turn", "All players are ready. The next turn will proceed now!")
        else:
            QMessageBox.information(self, "Waiting", "Waiting for all players to declare readiness.")

    def updateInfoLabel(self):
        galaxy_num = getattr(self, 'galaxy_index', 0)
        self.info_label.setText(f"Owner: {self.player_owner} | Game Year: {self.year} | Galaxy: {galaxy_num + 1}")
        if hasattr(self, "year_label"):
            self.year_label.setText(f"Year: {self.year}")

    def update_button_color(self, button):
        if button.owner and button.owner in self.owner_colors:
            bg = self.owner_colors[button.owner]
            # text = inverse for owner-colored buttons
            text_col = invert_color(bg)
        else:
            # Unowned: white background, force black text so it's always visible
            bg = "#FFFFFF"
            text_col = "#000000"
        button.setStyleSheet(f"background-color: {bg}; color: {text_col};")

    def update_from_state(self, state):
        import json
        if isinstance(state, str):
            state = json.loads(state)
        systems = state.get("systems", [])
        fleets = state.get("fleets", [])
        year = state.get("year", 1)

        # Store previous year to detect change
        prev_year = getattr(self, "year", 1)

        # Update systems (planets)
        for sys in systems:
            if hasattr(self, "galaxy_index") and sys.get("galaxy") != self.galaxy_index:
                continue
            btn = self.buttons.get(sys["system_id"])
            if btn:
                btn.owner = sys["owner"]
                btn.current_ships = sys["current_ships"]
                btn.ship_production = sys["ship_production"]
                btn.defense_factor = sys["defense_factor"]
                self.update_button_color(btn)

        self.fleets = [fleet for fleet in fleets if hasattr(self, "galaxy_index") and (
            fleet.get("source_galaxy", self.galaxy_index) == self.galaxy_index or
            fleet.get("dest_galaxy", self.galaxy_index) == self.galaxy_index
        )]

        self.year = year
        self.updateInfoLabel()
        if hasattr(self, "year_label"):
            self.year_label.setText(f"Year: {self.year}")

        # --- Set button red if year has advanced ---
        if year != prev_year:
            bg = "#a11a1a"
            self.next_turn_button.setStyleSheet(f"background-color: {bg}; color: {invert_color(bg)};")

    def update_next_turn_button_color(self):
        # Check if the current owner is ready (in self.ready_set or via server state if available)
        ready = False
        if hasattr(self, "ready_set"):
            ready = self.player_owner in self.ready_set
        # If you have a more up-to-date state (e.g. from server), check there instead.
        if ready:
            bg = "#1a7f1a"
        else:
            bg = "#a11a1a"
        self.next_turn_button.setStyleSheet(f"background-color: {bg}; color: {invert_color(bg)};")
    
    def set_next_turn_button_color(self, ready):
        bg = "#ffffff" if ready else "#ffffff"
        # text color must be inverse of background
        text = invert_color(bg)
        self.next_turn_button.setStyleSheet(f"background-color: {bg}; color: {text}; font-weight: bold;")
    
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
        self.prev_button.setFocusPolicy(Qt.NoFocus)
        self.next_button.setFocusPolicy(Qt.NoFocus)

        # Connect navigation buttons to methods
        self.prev_button.clicked.connect(self.showPreviousGalaxy)
        self.next_button.clicked.connect(self.showNextGalaxy)

        # Layout for the navigation buttons and the stack
        layout = QHBoxLayout()
        layout.addWidget(self.prev_button)
        layout.addWidget(self.stack, stretch=1)
        layout.addWidget(self.next_button)
        self.setLayout(layout)

        # Set the first galaxy as current and update its info label.
        self.stack.setCurrentIndex(0)
        self.grids[0].updateInfoLabel()

    def showPreviousGalaxy(self):
        current_index = self.stack.currentIndex()
        new_index = (current_index - 1) % self.stack.count()
        self.stack.setCurrentIndex(new_index)
        self.grids[new_index].updateInfoLabel()

    def showNextGalaxy(self):
        current_index = self.stack.currentIndex()
        new_index = (current_index + 1) % self.stack.count()
        self.stack.setCurrentIndex(new_index)
        self.grids[new_index].updateInfoLabel()

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
            
class GameSetupDialog(QDialog):
    """
    New game creation dialog that fetches registered users from server and allows searching.
    Selected users become in-game players. The creator must select which player is their own account.
    """
    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("Game Setup")
        self.layout = QVBoxLayout()

        # Basic options
        galaxy_layout = QHBoxLayout()
        galaxy_label = QLabel("Number of Galaxies:")
        self.galaxy_spin = QSpinBox()
        self.galaxy_spin.setMinimum(1)
        self.galaxy_spin.setMaximum(10)
        self.galaxy_spin.setValue(1)
        galaxy_layout.addWidget(galaxy_label)
        galaxy_layout.addWidget(self.galaxy_spin)
        self.layout.addLayout(galaxy_layout)

        planet_layout = QHBoxLayout()
        planet_label = QLabel("Planets per Galaxy:")
        self.planet_spin = QSpinBox()
        self.planet_spin.setMinimum(10)
        self.planet_spin.setMaximum(200)
        self.planet_spin.setValue(80)
        planet_layout.addWidget(planet_label)
        planet_layout.addWidget(self.planet_spin)
        self.layout.addLayout(planet_layout)

        # Player search and pick
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        self.layout.addLayout(search_layout)

        lists_layout = QHBoxLayout()
        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QListWidget.SingleSelection)
        lists_layout.addWidget(self.results_list)

        middle_btns = QVBoxLayout()
        add_btn = QPushButton("Add →")
        add_btn.clicked.connect(self.add_selected_user)
        remove_btn = QPushButton("← Remove")
        remove_btn.clicked.connect(self.remove_selected_player)
        middle_btns.addWidget(add_btn)
        middle_btns.addWidget(remove_btn)
        middle_btns.addStretch()
        lists_layout.addLayout(middle_btns)

        self.selected_list = QListWidget()
        lists_layout.addWidget(self.selected_list)

        self.layout.addLayout(lists_layout)

        # Creator owner selection
        owner_layout = QHBoxLayout()
        owner_layout.addWidget(QLabel("You will play as:"))
        self.creator_combo = QComboBox()
        owner_layout.addWidget(self.creator_combo)
        self.layout.addLayout(owner_layout)

        # OK/Cancel
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        self.layout.addLayout(btn_box)

        self.setLayout(self.layout)

        # initial search (empty -> list many users)
        self.perform_search()

    def perform_search(self):
        q = self.search_input.text().strip()
        if not self.client or not getattr(self.client, 'token', None) or not getattr(self.client, 'api_url', None):
            QMessageBox.warning(self, "Error", "Client not authenticated for user search.")
            return
        headers = {"Authorization": f"Bearer {self.client.token}"}
        try:
            # Fix: Remove duplicated /api/ from URL construction
            api_url = self.client.api_url.rstrip('/')
            resp = requests.get(f"{api_url}/user/list", params={"q": q}, headers=headers, timeout=5)
        except Exception as e:
            QMessageBox.warning(self, "Search Error", f"Network error: {e}")
            return
        if resp.status_code != 200:
            QMessageBox.warning(self, "Search Error", f"Failed to fetch users: {resp.text}")
            return
        users = resp.json()
        self.results_list.clear()
        for u in users:
            self.results_list.addItem(u["username"])

    def add_selected_user(self):
        item = self.results_list.currentItem()
        if not item:
            return
        username = item.text()
        # avoid duplicates
        if any(self.selected_list.item(i).text() == username for i in range(self.selected_list.count())):
            return
        self.selected_list.addItem(username)
        self.update_creator_combo()

    def remove_selected_player(self):
        item = self.selected_list.currentItem()
        if item:
            self.selected_list.takeItem(self.selected_list.row(item))
            self.update_creator_combo()

    def update_creator_combo(self):
        # Keep selected creator if possible, otherwise default to logged-in username if present
        current = self.creator_combo.currentText()
        self.creator_combo.clear()
        for i in range(self.selected_list.count()):
            self.creator_combo.addItem(self.selected_list.item(i).text())
        # Try to restore previous selection or default to client.username
        if current and current in [self.creator_combo.itemText(i) for i in range(self.creator_combo.count())]:
            self.creator_combo.setCurrentText(current)
        elif getattr(self.client, "username", None) and self.client.username in [self.creator_combo.itemText(i) for i in range(self.creator_combo.count())]:
            self.creator_combo.setCurrentText(self.client.username)

    def get_params(self):
        players = [self.selected_list.item(i).text() for i in range(self.selected_list.count())]
        creator_owner = self.creator_combo.currentText() if self.creator_combo.count() > 0 else getattr(self.client, "username", None)
        return {
            "galaxies": self.galaxy_spin.value(),
            "planets": self.planet_spin.value(),
            "players": players,
            "creator_owner": creator_owner
        }

class GameUI(QWidget):
    def __init__(self, client=None):
        super().__init__()
        self.client = client
        self.setWindowTitle("Risiko Game")
        self.setGeometry(100, 100, 600, 400)
        self.layout = QVBoxLayout()
        
        self.info_label = QLabel("Welcome to Risiko!")
        self.layout.addWidget(self.info_label)

        self.start_game_btn = QPushButton("Start New Game")
        self.start_game_btn.clicked.connect(self.start_new_game)
        self.layout.addWidget(self.start_game_btn)

        self.save_game_button = QPushButton("Save Game")
        self.save_game_button.clicked.connect(self.save_game)
        self.layout.addWidget(self.save_game_button)

        self.load_game_button = QPushButton("Load Game")
        self.load_game_button.clicked.connect(self.load_game)
        self.layout.addWidget(self.load_game_button)

        # --- Add this for deleting all games ---
        self.delete_games_button = QPushButton("Delete All Games")
        self.delete_games_button.clicked.connect(self.delete_all_games)
        self.layout.addWidget(self.delete_games_button)

        self.setLayout(self.layout)

    def delete_all_games(self):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Delete All Games",
            "Are you sure you want to delete all games? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if not self.client or not self.client.token or not self.client.api_url:
                QMessageBox.warning(self, "Error", "Client not authenticated.")
                return
            headers = {"Authorization": f"Bearer {self.client.token}"}
            import requests
            response = requests.post(f"{self.client.api_url}/game/delete_all", headers=headers)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", "All games have been deleted.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete games: {response.text}")

    def start_new_game(self):
        if not self.client or not self.client.token or not self.client.api_url:
            QMessageBox.warning(self, "Error", "Client not authenticated.")
            return

        dialog = GameSetupDialog(self, client=self.client)
        if (dialog.exec_() != QDialog.Accepted):
            return
        params = dialog.get_params()
        if not params["players"]:
            QMessageBox.warning(self, "Error", "At least one player required.")
            return

        headers = {"Authorization": f"Bearer {self.client.token}"}
        response = requests.post(
            f"{self.client.api_url}/game/start",
            json={
                "players": params["players"],
                "galaxies": params["galaxies"],
                "planets": params["planets"],
                "creator_owner": params.get("creator_owner")
            },
            headers=headers
        )
        if response.status_code == 201:
            data = response.json()
            game_id = data.get('game_id')
            QMessageBox.information(self, "Game Started", f"New game started! Game ID: {data.get('game_id')}")
            


    def save_game(self):
        # Collect all systems, fleets, players, year, etc. into a dict
        state = {
            "systems": [...],  # list of dicts for each system
            "fleets": [...],   # list of dicts for each fleet
            "year": self.year,
            # ...etc...
        }
        players = [
            {"owner": owner, "color": self.owner_colors[owner], "ready": owner in self.ready_set}
            for owner in self.owners
        ]
        data = {
            "game_id": self.current_game_id,
            "state": state,
            "players": players
        }
        headers = {"Authorization": f"Bearer {self.client.token}"}
        response = requests.post(f"{self.client.api_url}/game/save", json=data, headers=headers)
        # handle response...

    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QMessageBox

    def load_game(self):
        if not self.client or not self.client.token or not self.client.api_url:
            QMessageBox.warning(self, "Error", "Client not authenticated.")
            return
        headers = {"Authorization": f"Bearer {self.client.token}"}
        # Fetch all games from the server
        response = requests.get(f"{self.client.api_url}/game/list", headers=headers)
        if response.status_code != 200:
            QMessageBox.warning(self, "Error", f"Failed to fetch games: {response.text}")
            return
        games = response.json()
        if not games:
            QMessageBox.information(self, "No Games", "No games found on the server.")
            return

        # Show games in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Game to Load")
        layout = QVBoxLayout()
        list_widget = QListWidget()
        for game in games:
            # Show game ID and player names
            player_names = ", ".join(
                p["owner"] if isinstance(p, dict) and "owner" in p else str(p)
                for p in game.get("players", [])
            )
            list_widget.addItem(f"Game {game['game_id']} | Players: {player_names}")
        layout.addWidget(list_widget)
        load_btn = QPushButton("Load Selected Game")
        layout.addWidget(load_btn)
        dialog.setLayout(layout)

        selected_game_id = {"id": None}

        def on_load():
            idx = list_widget.currentRow()
            if idx < 0:
                QMessageBox.warning(dialog, "No Selection", "Please select a game to load.")
                return
            selected_game_id["id"] = games[idx]["game_id"]
            dialog.accept()

        load_btn.clicked.connect(on_load)

        if dialog.exec_() != QDialog.Accepted or selected_game_id["id"] is None:
            return

        game_id = selected_game_id["id"]
        # Now load the selected game as before
        response = requests.get(f"{self.client.api_url}/game/{game_id}", headers=headers)
        if response.status_code == 200:
            game_data = response.json()
            game_id = game_data["game_id"]
            import json
            state = json.loads(game_data["state"])
            players = json.loads(game_data["players"])
            owners = [p["owner"] if isinstance(p, dict) and "owner" in p else p for p in players]
            num_galaxies = state.get("galaxies", 1)
            num_planets = state.get("planets", 80)
            systems = state.get("systems", [])
            button_coords_all = state.get("button_coords", {})
            owner_colors = state.get("owner_colors", {})

            grids = []
            for galaxy_index in range(num_galaxies):
                button_coords = button_coords_all.get(str(galaxy_index)) or button_coords_all.get(galaxy_index)
                grid = ButtonGrid(
                    num_buttons=num_planets,
                    owners=owners,
                    button_coords=button_coords,
                    owner_colors=owner_colors
                )
                grid.galaxy_index = galaxy_index
                grid.game_id = game_id
                grid.client = self.client
                if owner_colors:
                    grid.owner_colors = owner_colors.copy()
                if button_coords:
                    for sys_id, pos in button_coords.items():
                        sys_id = int(sys_id)
                        if sys_id in grid.buttons:
                            grid.buttons[sys_id].grid_pos = tuple(pos)
                            grid.button_coords[sys_id] = tuple(pos)
                for sys in systems:
                    if sys["galaxy"] == galaxy_index:
                        btn = grid.buttons.get(sys["system_id"])
                        if btn:
                            btn.owner = sys["owner"]
                            btn.current_ships = sys["current_ships"]
                            btn.ship_production = sys["ship_production"]
                            btn.defense_factor = sys["defense_factor"]
                            grid.update_button_color(btn)
                grid.player_owner = owners[0] if owners else "Default_Player"
                grid.player_color = grid.owner_colors.get(grid.player_owner, "#FFFFFF")
                grids.append(grid)
            multigrid = MultiGrid(grids)
            win = QDialog(self)
            win.setWindowTitle(f"Loaded Game {game_id}")
            layout = QVBoxLayout()
            layout.addWidget(multigrid)
            win.setLayout(layout)

            # --- Ensure window fits the screen and is resizable ---
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            min_width, min_height = 800, 600
            max_width, max_height = screen_geometry.width(), screen_geometry.height()
            # Set sensible minimum and maximum
            win.setMinimumSize(min_width, min_height)
            win.setMaximumSize(max_width, max_height)
            # Resize to 90% of screen, but not below minimum
            width = max(min_width, int(max_width * 0.9))
            height = max(min_height, int(max_height * 0.9))
            win.resize(width, height)
            # Center the window
            win.move(
                screen_geometry.left() + (max_width - width) // 2,
                screen_geometry.top() + (max_height - height) // 2
            )

            win.show()
            self.loaded_game_window = win
            QMessageBox.information(self, "Game Loaded", "Game state has been loaded successfully!")
        else:
            QMessageBox.warning(self, "Error", f"Failed to load the game: {response.text}")

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QLineEdit, QPushButton, QColorDialog, QSlider
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class PlayerColorWidget(QHBoxLayout):
    def __init__(self, player_name, default_color):
        super().__init__()
        self.label = QLabel(player_name)
        self.color = QColor(default_color)
        self.color_btn = QPushButton()
        self.color_btn.setFixedWidth(40)
        self.update_btn_color()
        self.color_btn.clicked.connect(self.choose_color)
        self.addWidget(self.label)
        self.addWidget(self.color_btn)

    def choose_color(self):
        color = QColorDialog.getColor(self.color)
        if color.isValid():
            self.color = color
            self.update_btn_color()

    def update_btn_color(self):
        # ensure inverse text color for button label
        bg = self.color.name()
        self.color_btn.setStyleSheet(f"background-color: {bg}; color: {invert_color(bg)};")

    def get_color(self):
        return self.color.name()

