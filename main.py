import sys
from PyQt6.QtWidgets import QApplication
from gui import CraftingGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CraftingGUI()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())