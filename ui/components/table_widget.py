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
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragEnabled(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(True)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setVisible(False)
        
        # Плавная прокрутка (как в Excel)
        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)

        # Стиль
        self.setStyleSheet("""
        QTableView {
            background-color: transparent;
            border: none;
            gridline-color: #DEE2E6;
            outline: none;
            show-decoration-selected: 0;
        }
        QTableView::item {
            padding: 4px 8px;
            border-right: 1px solid #F0F0F0;
            border-bottom: 1px solid #F0F0F0;
            outline: none;
            background-color: transparent;
        }
        QTableView::item:focus {
            outline: none;
            background-color: #E3F2FD;
        }
        QTableView::item:selected {
            background-color: #B3D9F5;
            color: #000000;
        }
        QHeaderView::section {
            background-color: #E9ECEF;
            color: #212529;
            font: bold 13px "Vollkorn";
            padding: 8px 12px;
            border: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            outline: none;
        }
        QHeaderView::section:first {
            border-top-left-radius: 8px;
            padding-left: 12px;
        }
        QHeaderView::section:last {
            border-top-right-radius: 8px;
            padding-right: 12px;
        }
        QHeaderView {
            background-color: transparent;
            border: none;
            outline: none;
        }
        QScrollBar:vertical {
            background-color: #F0F0F0;
            width: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background-color: #C4C9CC;
            border-radius: 5px;
            min-height: 40px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #A0A5A9;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        QScrollBar:horizontal {
            background-color: #F0F0F0;
            height: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background-color: #C4C9CC;
            border-radius: 5px;
            min-width: 40px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #A0A5A9;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
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
        font = QFont("Vollkorn", font_size)
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

        # Авто-подбор ширины колонок по содержимому
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for col in range(len(df.columns)):
            self.resizeColumnToContents(col)
            # Минимальная ширина колонки
            current_width = self.columnWidth(col)
            if current_width < 100:
                self.setColumnWidth(col, 100)