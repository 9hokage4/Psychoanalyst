# ui/components/simple_table.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt, QRectF, QPointF, QSizeF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
import pandas as pd


class SimpleTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale = 1.0
        self.df = None
        self.radius = 16
        self.cell_h = 34
        self.cell_w = 80
        self.setFont(QFont("Arial", 11))

    def set_data_frame(self, df):
        self.df = df
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        if self.df is None or self.df.empty:
            return

        # Параметры
        base_font_size = 11
        font_size = max(8, int(base_font_size * self.scale))
        self.cell_h = max(20, int(34 * self.scale))
        self.cell_w = max(80, int(80 * self.scale))
        font = QFont("Arial", font_size)
        painter.setFont(font)

        cols = len(self.df.columns)
        rows = len(self.df)
        total_w = cols * self.cell_w
        total_h = (rows + 1) * self.cell_h

        # Рамка таблицы
        rect = QRectF(0, 0, total_w, total_h)
        painter.setPen(QPen(QColor("#dee2e6"), 1))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRoundedRect(rect, self.radius, self.radius)

        # Заголовки
        for j, col in enumerate(self.df.columns):
            x = j * self.cell_w
            y = 0
            w, h = self.cell_w, self.cell_h

            if j == 0:  # левый верхний угол
                path = QPainterPath()
                path.moveTo(x, y)
                path.lineTo(x + w, y)
                path.lineTo(x + w, y + h)
                path.lineTo(x + self.radius, y + h)
                path.arcTo(x, y + h - 2*self.radius, 2*self.radius, 2*self.radius, 90, 90)
                path.closeSubpath()
                painter.setBrush(QBrush(QColor("#e9ecef")))
                painter.drawPath(path)
                painter.setPen(QPen(QColor("#212529")))
                painter.drawText(QRectF(x + 4, y + 4, w - 8, h - 8), str(col))
            elif j == cols - 1:  # правый верхний угол
                path = QPainterPath()
                path.moveTo(x, y)
                path.lineTo(x + w - self.radius, y)
                path.arcTo(x + w - 2*self.radius, y, 2*self.radius, 2*self.radius, 0, 90)
                path.lineTo(x + w, y + h)
                path.lineTo(x, y + h)
                path.closeSubpath()
                painter.setBrush(QBrush(QColor("#e9ecef")))
                painter.drawPath(path)
                painter.setPen(QPen(QColor("#212529")))
                painter.drawText(QRectF(x + 4, y + 4, w - 8, h - 8), str(col))
            else:
                painter.setBrush(QBrush(QColor("#e9ecef")))
                painter.setPen(QPen(QColor("#dee2e6"), 1))
                painter.drawRect(x, y, w, h)
                painter.setPen(QPen(QColor("#212529")))
                painter.drawText(QRectF(x + 4, y + 4, w - 8, h - 8), str(col))

        # Данные
        for i, (_, row) in enumerate(self.df.iterrows()):
            bg = QColor("#ffffff") if i % 2 == 0 else QColor("#f8f9fa")
            y = (i + 1) * self.cell_h
            for j, val in enumerate(row):
                x = j * self.cell_w
                w, h = self.cell_w, self.cell_h

                if i == rows - 1 and j == 0:  # левый нижний
                    path = QPainterPath()
                    path.moveTo(x, y)
                    path.lineTo(x + w, y)
                    path.lineTo(x + w, y + h)
                    path.lineTo(x + self.radius, y + h)
                    path.arcTo(x, y + h - 2*self.radius, 2*self.radius, 2*self.radius, 90, 90)
                    path.closeSubpath()
                    painter.setBrush(bg)
                    painter.drawPath(path)
                elif i == rows - 1 and j == cols - 1:  # правый нижний
                    path = QPainterPath()
                    path.moveTo(x, y)
                    path.lineTo(x + w - self.radius, y)
                    path.arcTo(x + w - 2*self.radius, y, 2*self.radius, 2*self.radius, 0, 90)
                    path.lineTo(x + w, y + h)
                    path.lineTo(x, y + h)
                    path.closeSubpath()
                    painter.setBrush(bg)
                    painter.drawPath(path)
                else:
                    painter.setBrush(bg)
                    painter.setPen(QPen(QColor("#dee2e6"), 1))
                    painter.drawRect(x, y, w, h)

                painter.setPen(QPen(QColor("#212529")))
                text = str(val) if pd.notna(val) else ""
                painter.drawText(QRectF(x + 4, y + 4, w - 8, h - 8), text)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.scale = min(self.scale * 1.1, 2.0)
            else:
                self.scale = max(self.scale / 1.1, 0.5)
            self.update()
            event.accept()
        else:
            super().wheelEvent(event)