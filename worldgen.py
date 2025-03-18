import csv
import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
                             QLineEdit, QPushButton, QMessageBox, QApplication)

class WorldGenMenu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("World Generation Options")
        layout = QVBoxLayout()

        # Option: Number of Planets.
        planet_layout = QHBoxLayout()
        planet_label = QLabel("Number of Planets:")
        self.planet_spinbox = QSpinBox()
        self.planet_spinbox.setMinimum(1)
        self.planet_spinbox.setMaximum(1000)
        self.planet_spinbox.setValue(80)  # Default value.
        planet_layout.addWidget(planet_label)
        planet_layout.addWidget(self.planet_spinbox)
        layout.addLayout(planet_layout)

        # Option: Owner Names.
        self.owner_edits = []
        for i in range(5):
            owner_layout = QHBoxLayout()
            owner_label = QLabel(f"Owner {chr(65+i)} Name:")
            owner_edit = QLineEdit()
            owner_edit.setText(f"Owner {chr(65+i)}")  # Default name.
            owner_layout.addWidget(owner_label)
            owner_layout.addWidget(owner_edit)
            layout.addLayout(owner_layout)
            self.owner_edits.append(owner_edit)
        
        # Save Options Button.
        save_button = QPushButton("Save Options")
        save_button.clicked.connect(self.saveOptions)
        layout.addWidget(save_button)
        
        self.setLayout(layout)
    
    def saveOptions(self):
        num_planets = self.planet_spinbox.value()
        owners = [edit.text() for edit in self.owner_edits]
        # Save the options into a CSV file.
        try:
            with open('worldgen_options.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Number of Planets', 'Owner Names'])
                writer.writerow([num_planets, "; ".join(owners)])
            QMessageBox.information(self, "Save Successful", 
                                    "Options saved to worldgen_options.csv")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", str(e))
        self.accept()

def load_worldgen_options():
    """Load world generation options from CSV. Returns a tuple: (number of planets, list of owners)."""
    try:
        with open('worldgen_options.csv', 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            lines = list(reader)
            if len(lines) >= 2:
                num_planets = int(lines[1][0])
                owners = lines[1][1].split("; ")
                return num_planets, owners
    except Exception as e:
        print("Error loading worldgen options:", e)
    # Fallback defaults.
    return 80, ["Owner A", "Owner B", "Owner C", "Owner D", "Owner E"]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = WorldGenMenu()
    dialog.exec_()
    # After the dialog is closed, load and display the options.
    num_planets, owners = load_worldgen_options()
    print("Loaded World Generation Options:")
    print("Number of Planets:", num_planets)
    print("Owner Names:", owners)
    sys.exit(0)