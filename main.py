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

    # Убираем пунктирное выделение фокуса для всех виджетов
    app.setStyleSheet("""
        QPushButton:focus,
        QSpinBox:focus,
        QLineEdit:focus,
        QTextEdit:focus,
        QCheckBox:focus,
        QRadioButton:focus,
        QComboBox:focus,
        QTabWidget:focus,
        QSlider:focus,
        QScrollBar:focus,
        QToolButton:focus {
            outline: none;
            border: none;
        }
        QTableView:focus,
        QListWidget:focus,
        QTableWidget:focus {
            outline: none;
        }
    """)

    window = MainWindow()
    window.showMaximized()
    # window.showFullScreen()  # Альтернатива: полный экран без рамок окна

    sys.exit(app.exec())


if __name__ == "__main__":
    main()