# ui/components/table_frame.py
from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush


class TableFrame(QFrame):
    def __init__(self, radius=16, border_color="#dee2e6", bg_color="white"):
        super().__init__()
        self.radius = radius
        self.border_color = border_color
        self.bg_color = bg_color
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        # Фон
        painter.setBrush(QColor(self.bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, self.radius, self.radius)
        
        # Граница
        painter.setPen(QPen(QColor(self.border_color), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), self.radius, self.radius)