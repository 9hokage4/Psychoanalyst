# ui/components/upload_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QTableView, QHeaderView, QAbstractItemView,
    QFileDialog, QHBoxLayout, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont
import pandas as pd


class ExcelTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale = 1.0

        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(True)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setVisible(False)

        self.setStyleSheet("""
            QTableView {
                background-color: transparent;
                border: none;
                gridline-color: #dee2e6;
            }
            QTableView::item {
                padding: 4px 8px;
                border-right: 1px solid #f0f0f0;
                border-bottom: 1px solid #f0f0f0;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                color: #212529;
                font: bold 12px "Arial";
                padding: 6px 8px;
                border: none;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
            QHeaderView::section:first {
                border-top-left-radius: 16px;
                padding-left: 0px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 16px;
                padding-right: 0px;
            }
        """)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.scale = min(self.scale * 1.1, 2.0)
            else:
                self.scale = max(self.scale / 1.1, 0.5)
            self.update_font_size()
            event.accept()
        else:
            super().wheelEvent(event)

    def update_font_size(self):
        base_font_size = 11
        font_size = max(8, int(base_font_size * self.scale))
        font = QFont("Arial", font_size)
        self.setFont(font)

        row_height = max(20, int(34 * self.scale))
        self.verticalHeader().setDefaultSectionSize(row_height)

        if self.model():
            for col in range(self.model().columnCount()):
                self.setColumnWidth(col, max(80, int(80 * self.scale)))

    def set_data_frame(self, df):
        if df is None or df.empty:
            self.setModel(None)
            return

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(df.columns.astype(str).tolist())

        for row in df.itertuples(index=False):
            items = []
            for val in row:
                item = QStandardItem(str(val) if pd.notna(val) else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                items.append(item)
            model.appendRow(items)

        self.setModel(model)
        self.update_font_size()

        # Логика растяжения
        cols = len(df.columns)
        if cols <= 10:
            self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        else:
            self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            visible_width = self.viewport().width()
            col_width = max(80, int(visible_width / 10))
            for col in range(cols):
                self.setColumnWidth(col, col_width)


class UploadWidget(QWidget):
    file_loaded = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.current_df = None
        self.current_file_path = None
        self.sheet_names = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)

        # === Верхняя панель: кнопка + имя файла + выбор листа ===
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        self.load_button = QPushButton("📂 Загрузить Excel")
        self.load_button.clicked.connect(self.load_file)
        top_layout.addWidget(self.load_button)

        self.file_label = QLabel("Файл: не выбран")
        self.file_label.setObjectName("file_label")
        top_layout.addWidget(self.file_label)

        # Выбор листа (изначально скрыт) — кастомный стиль
        self.sheet_combo = QComboBox()
        self.sheet_combo.setVisible(False)
        self.sheet_combo.setStyleSheet("""
            QComboBox {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 5px 10px;
                font: 12px "Arial";
                color: #212529;
                min-width: 120px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 0px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QComboBox:hover {
                border-color: #a0a0a0;
            }
        """)
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)
        top_layout.addWidget(self.sheet_combo)

        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # === Таблица ===
        self.table_container = QWidget()
        self.table_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 16px;
                margin: 0px;
                padding: 0px;
            }
        """)
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
                # Получаем список листов
                self.sheet_names = pd.ExcelFile(file_path).sheet_names
                self.current_file_path = file_path

                if len(self.sheet_names) > 1:
                    # Показываем выпадающий список
                    self.sheet_combo.clear()
                    self.sheet_combo.addItems(self.sheet_names)
                    self.sheet_combo.setVisible(True)
                    # Загружаем первый лист по умолчанию
                    self.load_sheet(self.sheet_names[0])
                else:
                    # Один лист — скрываем комбо
                    self.sheet_combo.setVisible(False)
                    self.load_sheet(self.sheet_names[0])

                file_name = file_path.split("/")[-1].split("\\")[-1]
                self.file_label.setText(f"Файл: {file_name}")

            except Exception as e:
                print(f"Ошибка загрузки: {e}")
                self.file_label.setText("Ошибка загрузки файла")

    def load_sheet(self, sheet_name):
        """Загружает данные из указанного листа"""
        try:
            df = pd.read_excel(self.current_file_path, sheet_name=sheet_name)
            self.current_df = df
            self.table.set_data_frame(df)
            self.file_loaded.emit(df)
        except Exception as e:
            print(f"Ошибка загрузки листа: {e}")

    def on_sheet_changed(self, sheet_name):
        """Обработчик смены листа"""
        if sheet_name:
            self.load_sheet(sheet_name)