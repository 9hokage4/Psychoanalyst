from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt
import pandas as pd

class ExcelPreviewTable(QTableWidget):
    """
    Таблица для предпросмотра Excel-данных.
    Принимает pandas DataFrame и отображает его как в Excel.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(0)
        self.setRowCount(0)
        # Настройка внешнего вида
        self.setAlternatingRowColors(True)
        self.setStyleSheet("alternate-background-color: #f9f9f9;")

    def load_dataframe(self, df: pd.DataFrame):
        """Загружает DataFrame и отображает его в таблице."""
        if df.empty:
            self.clear()
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        # Очищаем текущее содержимое
        self.clear()
        
        # Устанавливаем размеры
        self.setRowCount(len(df))
        self.setColumnCount(len(df.columns))
        
        # Устанавливаем заголовки столбцов
        self.setHorizontalHeaderLabels(df.columns.tolist())
        
        # Заполняем ячейки
        for row_idx, row in df.iterrows():
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Только для чтения
                self.setItem(row_idx, col_idx, item)