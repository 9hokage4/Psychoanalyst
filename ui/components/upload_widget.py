# ui/components/upload_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QHBoxLayout, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
import pandas as pd
from ui.components.table_widget import ExcelTable


class UploadWidget(QWidget):
    file_loaded = pyqtSignal(object)
    filename_updated = pyqtSignal(str)
    settings_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_df = None
        self.current_file_path = None
        self.sheet_names = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)

        # === Верхняя панель ===
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # Кнопка загрузки
        self.load_button = QPushButton(" Загрузить Excel")
        self.load_button.setObjectName("btn_load_file")
        self.load_button.setIcon(QIcon("resources/icons/file-download.svg"))
        self.load_button.clicked.connect(self.load_file)
        top_layout.addWidget(self.load_button)

        # Имя файла
        self.file_label = QLabel("Файл: не выбран")
        self.file_label.setObjectName("file_label")
        top_layout.addWidget(self.file_label)

        # Выбор листа
        self.sheet_combo = QComboBox()
        self.sheet_combo.setVisible(False)
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)
        top_layout.addWidget(self.sheet_combo)

        # === Кнопка настройки (справа) ===
        top_layout.addStretch()

        self.settings_button = QPushButton(" Настройка")
        self.settings_button.setObjectName("btn_settings")
        self.settings_button.setIcon(QIcon("resources/icons/cog.svg"))
        self.settings_button.clicked.connect(self.settings_requested.emit)
        top_layout.addWidget(self.settings_button)

        main_layout.addLayout(top_layout)

        # === Таблица ===
        self.table_container = QWidget()
        self.table_container.setObjectName("table_container")
        table_layout = QVBoxLayout(self.table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = ExcelTable()
        table_layout.addWidget(self.table)

        main_layout.addWidget(self.table_container)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите Excel-файл",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            try:
                self.sheet_names = pd.ExcelFile(file_path).sheet_names
                self.current_file_path = file_path

                file_name = file_path.split("/")[-1].split("\\")[-1]
                self.file_label.setText(f"Файл: {file_name}")
                self.filename_updated.emit(file_name)

                if len(self.sheet_names) > 1:
                    self.sheet_combo.clear()
                    self.sheet_combo.addItems(self.sheet_names)
                    self.sheet_combo.setVisible(True)
                    self.load_sheet(self.sheet_names[0])
                else:
                    self.sheet_combo.setVisible(False)
                    self.load_sheet(self.sheet_names[0])

            except Exception as e:
                print(f"Ошибка загрузки: {e}")
                self.file_label.setText("Ошибка загрузки файла")

    def load_sheet(self, sheet_name):
        try:
            df = pd.read_excel(self.current_file_path, sheet_name=sheet_name)
            self.current_df = df
            self.table.set_data_frame(df)
            self.file_loaded.emit(df)
        except Exception as e:
            print(f"Ошибка загрузки листа: {e}")

    def on_sheet_changed(self, sheet_name):
        if sheet_name:
            self.load_sheet(sheet_name)