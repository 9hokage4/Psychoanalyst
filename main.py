# main.py
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Psychoanalyst")
    
    style_file = "ui/style.qss"  
    
    try:
        with open(style_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        print(f"Стили загружены из {style_file}")
    except FileNotFoundError:
        print(f"Предупреждение: Файл стилей '{style_file}' не найден")
    except Exception as e:
        print(f"Ошибка загрузки стилей: {e}")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()