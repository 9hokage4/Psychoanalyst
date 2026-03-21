# main.py
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui.main_window import MainWindow
from utils.fonts import load_fonts, get_font, get_font_family


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Psychoanalyst")

    # Загружаем все шрифты из resources/fonts
    load_fonts()

    # Устанавливаем шрифт по умолчанию для всего приложения
    default_font = get_font("body")
    app.setFont(default_font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()