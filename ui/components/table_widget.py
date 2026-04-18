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

        # Стиль - только синие заголовки, без дополнительного оформления
        self.setStyleSheet("""
        QTableView {
            background-color: #FFFFFF;
            border: none;
            gridline-color: #E0E0E0;
            outline: none;
            show-decoration-selected: 0;
            font-size: 13px;
            font-family: 'Segoe UI', Arial;
            alternate-background-color: #FAFAFA;
        }
        QTableView::item {
            padding: 10px 12px;
            border: none;
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
            background-color: #E3F2FD;
            color: #1976D2;
            font: bold 13px "Segoe UI", Arial;
            padding: 12px 8px;
            border: none;
            border-bottom: 2px solid #BBDEFB;
            outline: none;
        }
        QHeaderView {
            background-color: transparent;
            border: none;
            outline: none;
        }
        QScrollBar:vertical {
            background-color: #F5F5F5;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #BDBDBD;
            border-radius: 6px;
            min-height: 40px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #9E9E9E;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        QScrollBar:horizontal {
            background-color: #F5F5F5;
            height: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal {
            background-color: #BDBDBD;
            border-radius: 6px;
            min-width: 40px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #9E9E9E;
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