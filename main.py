import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, 
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from ui.components.excel_preview import ExcelPreviewTable

class ProcessTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # * Основной горизонтальный layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # * Левый блок: кнопки и метка
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_layout.setSpacing(10)  # Отступы между элементами
        left_layout.setContentsMargins(10, 10, 10, 10)  # Внутренние отступы

        # * Кнопка выбора файла
        self.file_button = QPushButton("Выбрать файл (Excel)")
        self.file_button.setObjectName("selectFileButton")
        self.file_button.clicked.connect(self.select_file)
        left_layout.addWidget(self.file_button)

        # * Метка для отображения имени файла
        self.file_label = QLabel("Выбранный файл отсутствует")
        self.file_label.setFixedHeight(30)
        self.file_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        left_layout.addWidget(self.file_label)

        # ! Заглушка под кнопку "Обработка" — пока не активна
        self.run_button = QPushButton("Обработка")
        self.run_button.setEnabled(False)
        left_layout.addWidget(self.run_button)

        # * Статус-строка внизу левого блока
        self.status_label = QLabel("Готов к обработке...")
        self.status_label.setFixedHeight(25)
        self.status_label.setStyleSheet("background-color: #e8e8e8; padding: 3px;")
        left_layout.addStretch()  # Растягивает пространство вниз
        left_layout.addWidget(self.status_label)

        # * Добавляем левый блок в основной layout
        main_layout.addWidget(left_widget, 1)  # 1 — ширина относительно правого блока

        # * Правый блок: таблица
        self.preview_table = ExcelPreviewTable()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.preview_table)
        scroll_area.setMinimumHeight(400)
        scroll_area.setMaximumHeight(800)
        scroll_area.setStyleSheet("border: 1px solid #ccc;")

        # * Добавляем правый блок в основной layout
        main_layout.addWidget(scroll_area, 3)  # 3 — правый блок шире левого
        
    def select_file(self):
        # * Открываем диалог выбора Excel-файла
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать файл", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.file_label.setText(f"Выбрано: {file_path.split('/')[-1]}")
            self.load_preview(file_path)
            self.run_button.setEnabled(True)

    def load_preview(self, file_path: str):
        # * Загружаем весь файл (или можно ограничить nrows для скорости)
        try:
            df = pd.read_excel(file_path)
            self.preview_table.load_dataframe(df)
        except Exception as e:
            # ! Нужно улучшить обработку ошибок
            self.file_label.setText(f"Ошибка: {str(e)}")
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Psychological Test Analyzer")
        self.resize(900, 700)

        # * Центральный виджет для размещения контента
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # * Вкладки для разделения функционала
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # * Инициализация вкладок
        self.process_tab = ProcessTab()
        self.analyze_tab = QWidget()  # ! Заглушка — будет заменена на AnalyzeTab

        self.tabs.addTab(self.process_tab, "Обработка")
        self.tabs.addTab(self.analyze_tab, "Анализ")

if __name__ == "__main__":
    # * Создание и запуск приложения
    app = QApplication(sys.argv)
    
    # * Загрузка стилей из файла
    with open("ui/style.qss", "r", encoding="utf-8") as f:
        app.setStyle(f.read())
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec())