# ui/components/upload_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, 
    QTableView, QHeaderView, QAbstractItemView,
    QFileDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont
import pandas as pd


class ExcelTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale = 1.0
        
        # Настройка внешнего вида
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(True)
        
        # Заголовки
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setVisible(False)
        
        # Стиль сетки
        self.setStyleSheet("""
            QTableView {
                gridline-color: #dee2e6;
                background-color: white;
            }
            QTableView::item {
                padding: 4px;
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
        
        # Высота строк
        row_height = max(20, int(34 * self.scale))
        self.verticalHeader().setDefaultSectionSize(row_height)
        
        # Ширина колонок (если модель загружена)
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


class UploadWidget(QWidget):
    file_loaded = pyqtSignal(object)  # Сигнал для передачи данных

    def __init__(self):
        super().__init__()
        self.current_df = None
        
        # Основной layout
        main_layout = QVBoxLayout()
        
        # Верхняя панель: кнопка + имя файла
        top_layout = QHBoxLayout()
        
        self.load_button = QPushButton("📂 Загрузить Excel")
        self.load_button.clicked.connect(self.load_file)
        top_layout.addWidget(self.load_button)
        
        self.file_label = QLabel("Файл: не выбран")
        self.file_label.setObjectName("file_label")
        top_layout.addWidget(self.file_label)
        top_layout.addStretch()
        
        main_layout.addLayout(top_layout)
        
        # Таблица
        self.table = ExcelTable()
        main_layout.addWidget(self.table)
        
        self.setLayout(main_layout)
    
    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите Excel-файл",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            try:
                df = pd.read_excel(file_path)
                self.current_df = df
                self.table.set_data_frame(df)
                
                file_name = file_path.split("/")[-1].split("\\")[-1]
                self.file_label.setText(f"Файл: {file_name}")
                
                # Передаём данные в другие вкладки
                self.file_loaded.emit(df)
                
            except Exception as e:
                print(f"Ошибка загрузки: {e}")
                self.file_label.setText("Ошибка загрузки файла")