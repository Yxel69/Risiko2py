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
        self.initUI()

    def initUI(self):
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

            # Initialize custom variables
            button.current_ships = 0
            button.ship_production = random.randint(1, 10)
            button.defense_factor = round(random.uniform(0.1, 0.5), 2)
            button.owner = "Unclaimed"

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
        # You can also add additional actions if needed
        menu.addSeparator()
        menu.addAction("Action 1")
        menu.addAction("Action 2")
        menu.addAction("Action 3")
        # Display the menu below the button
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

    def keyPressEvent(self, event):
        # When the E key is pressed, start the sequential input mode for distance calculation.
        if event.key() == Qt.Key_E:
            self.startDistanceInput()
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ButtonGrid()
    window.showMaximized()  # Launch the application in fullscreen mode
    sys.exit(app.exec_())
