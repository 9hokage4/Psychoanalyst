# ui/components/table_widget.py
from PyQt6.QtWidgets import QTableView, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont
import pandas as pd


class ExcelTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale = 1.0

        # Настройки
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(True)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setVisible(False)

        # Стиль
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
            parent_width = self.parent().width() if self.parent() else 800
            col_width = max(80, int(parent_width / 10))
            for col in range(cols):
                self.setColumnWidth(col, col_width)