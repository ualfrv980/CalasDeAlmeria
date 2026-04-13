import sys
import os

# Support both normal execution and PyInstaller frozen .exe
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    sys.path.insert(0, BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.database import Database
from src.main_window import MainWindow


def main():
    # Windows high-DPI support
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Calas de Almería")
    app.setApplicationDisplayName("Calas de Almería")
    app.setOrganizationName("CalasDeAlmeria")

    # Default font
    app.setFont(QFont("Segoe UI", 10))

    try:
        db = Database()
        db.initialize()
    except Exception as e:
        QMessageBox.critical(None, "Error de base de datos",
                             f"No se pudo inicializar la base de datos:\n{e}")
        sys.exit(1)

    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
