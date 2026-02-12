# ui/components/lightweight_table.py
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QScrollArea, QVBoxLayout,
    QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
import pandas as pd


class LightweightTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale = 1.0
        self.df = None
        self.rows = []
        self.columns = []
        
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Скролл-область
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setSpacing(0)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
    
    def set_data_frame(self, df):
        self.df = df
        if df is None or df.empty:
            self.clear_table()
            return
        
        self.clear_table()
        
        # Параметры с масштабом
        base_font_size = 11
        font_size = max(8, int(base_font_size * self.scale))
        row_height = max(20, int(34 * self.scale))
        col_width = max(80, int(80 * self.scale))
        
        font = QFont("Arial", font_size)
        
        # Заголовки
        for j, col in enumerate(df.columns):
            label = QLabel(str(col))
            label.setFont(font)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: #e9ecef;
                    color: #212529;
                    border: 1px solid #dee2e6;
                    padding: 4px 8px;
                }
            """)
            
            # Скруглённые углы для угловых ячеек
            if j == 0:
                # Левый верхний угол
                label.setStyleSheet("""
                    QLabel {
                        background-color: #e9ecef;
                        color: #212529;
                        border: 1px solid #dee2e6;
                        padding: 4px 8px;
                        border-top-left-radius: 16px;
                        border-bottom-left-radius: 0px;
                    }
                """)
            elif j == len(df.columns) - 1:
                # Правый верхний угол
                label.setStyleSheet("""
                    QLabel {
                        background-color: #e9ecef;
                        color: #212529;
                        border: 1px solid #dee2e6;
                        padding: 4px 8px;
                        border-top-right-radius: 16px;
                        border-bottom-right-radius: 0px;
                    }
                """)
            else:
                label.setStyleSheet("""
                    QLabel {
                        background-color: #e9ecef;
                        color: #212529;
                        border: 1px solid #dee2e6;
                        padding: 4px 8px;
                        border-top-left-radius: 0px;
                        border-top-right-radius: 0px;
                    }
                """)
            
            self.content_layout.addWidget(label, 0, j)
        
        # Данные
        for i, (_, row) in enumerate(df.iterrows()):
            bg_color = "#ffffff" if i % 2 == 0 else "#f8f9fa"
            for j, val in enumerate(row):
                text = str(val) if pd.notna(val) else ""
                label = QLabel(text)
                label.setFont(font)
                label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                # Скруглённые углы для угловых ячеек
                if i == len(df) - 1 and j == 0:
                    # Левый нижний угол
                    radius = "border-bottom-left-radius: 16px;"
                elif i == len(df) - 1 and j == len(df.columns) - 1:
                    # Правый нижний угол
                    radius = "border-bottom-right-radius: 16px;"
                else:
                    radius = ""
                
                label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {bg_color};
                        color: #212529;
                        border: 1px solid #dee2e6;
                        padding: 4px 8px;
                        {radius}
                    }}
                """)
                
                self.content_layout.addWidget(label, i + 1, j)
        
        # Установка размеров колонок
        for j in range(len(df.columns)):
            self.content_layout.setColumnMinimumWidth(j, col_width)
        for i in range(len(df) + 1):
            self.content_layout.setRowMinimumHeight(i, row_height)
    
    def clear_table(self):
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
    
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.scale = min(self.scale * 1.1, 2.0)
            else:
                self.scale = max(self.scale / 1.1, 0.5)
            if self.df is not None:
                self.set_data_frame(self.df)
            event.accept()
        else:
            super().wheelEvent(event)