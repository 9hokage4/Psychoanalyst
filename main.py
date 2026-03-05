# main.py
import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Применяем стиль
    style_file = os.path.join(os.path.dirname(__file__), "style.qss")
    with open(style_file, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
    
    window = MainWindow()
    window.showMaximized()  # Полноэкранный режим
    sys.exit(app.exec())


if __name__ == "__main__":
    main()