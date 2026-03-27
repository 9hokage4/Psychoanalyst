# ui/components/graphics_table.py
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem
from PyQt6.QtCore import Qt, QRectF, QPointF, QSizeF
from PyQt6.QtGui import QFont, QColor, QPen, QBrush, QPainter, QPainterPath
import pandas as pd


class GraphicsTable(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale = 1.0
        self.df = None
        self.radius = 16
        self.cell_height = 34
        self.cell_width = 80
        self.header_height = 34

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

    def set_data_frame(self, df):
        self.df = df
        self.scene.clear()

        if df is None or df.empty:
            return

        # Параметры с масштабом
        base_font_size = 11
        font_size = max(8, int(base_font_size * self.scale))
        self.cell_height = max(20, int(34 * self.scale))
        self.cell_width = max(80, int(80 * self.scale))
        self.header_height = self.cell_height

        font = QFont("Vollkorn", font_size)
        cols = len(df.columns)
        rows = len(df)
        total_width = cols * self.cell_width
        total_height = (rows + 1) * self.cell_height

        # Рамка таблицы (скруглённая)
        frame_path = QPainterPath()
        frame_path.addRoundedRect(0, 0, total_width, total_height, self.radius, self.radius)
        frame_item = QGraphicsPathItem(frame_path)
        frame_item.setPen(QPen(QColor("#dee2e6"), 1))
        frame_item.setBrush(QBrush(QColor("white")))
        self.scene.addItem(frame_item)

        # Заголовки
        for j, col in enumerate(df.columns):
            x = j * self.cell_width
            y = 0
            rect = QRectF(x, y, self.cell_width, self.header_height)
            pen = QPen(QColor("#dee2e6"), 1)
            brush = QBrush(QColor("#e9ecef"))

            if j == 0:  # левый верхний угол
                path = QPainterPath()
                path.moveTo(rect.topLeft())
                path.lineTo(rect.topRight())
                path.lineTo(rect.bottomRight())
                path.lineTo(rect.bottomLeft() + QPointF(self.radius, 0))
                path.arcTo(QRectF(rect.bottomLeft(), QSizeF(2*self.radius, 2*self.radius)), 90, 90)
                path.closeSubpath()
                path_item = QGraphicsPathItem(path)
                path_item.setPen(pen)
                path_item.setBrush(brush)
                self.scene.addItem(path_item)
            elif j == cols - 1:  # правый верхний угол
                path = QPainterPath()
                path.moveTo(rect.topLeft())
                path.lineTo(rect.topRight() - QPointF(self.radius, 0))
                path.arcTo(QRectF(rect.topRight() - QPointF(2*self.radius, 0), QSizeF(2*self.radius, 2*self.radius)), 0, 90)
                path.lineTo(rect.bottomRight())
                path.lineTo(rect.bottomLeft())
                path.closeSubpath()
                path_item = QGraphicsPathItem(path)
                path_item.setPen(pen)
                path_item.setBrush(brush)
                self.scene.addItem(path_item)
            else:
                from PyQt6.QtWidgets import QGraphicsRectItem
                rect_item = QGraphicsRectItem(rect)
                rect_item.setPen(pen)
                rect_item.setBrush(brush)
                self.scene.addItem(rect_item)

            # Текст заголовка
            text_item = self.scene.addText(str(col), font)
            text_item.setDefaultTextColor(QColor("#212529"))
            text_item.setPos(x + 4, y + 4)

        # Данные
        for i, (_, row) in enumerate(df.iterrows()):
            bg_color = QColor("#ffffff") if i % 2 == 0 else QColor("#f8f9fa")
            y = (i + 1) * self.cell_height
            for j, val in enumerate(row):
                x = j * self.cell_width
                rect = QRectF(x, y, self.cell_width, self.cell_height)
                pen = QPen(QColor("#dee2e6"), 1)
                brush = QBrush(bg_color)

                if i == rows - 1 and j == 0:  # левый нижний угол
                    path = QPainterPath()
                    path.moveTo(rect.topLeft())
                    path.lineTo(rect.topRight())
                    path.lineTo(rect.bottomRight())
                    path.lineTo(rect.bottomLeft() + QPointF(self.radius, 0))
                    path.arcTo(QRectF(rect.bottomLeft(), QSizeF(2*self.radius, 2*self.radius)), 90, 90)
                    path.closeSubpath()
                    path_item = QGraphicsPathItem(path)
                    path_item.setPen(pen)
                    path_item.setBrush(brush)
                    self.scene.addItem(path_item)
                elif i == rows - 1 and j == cols - 1:  # правый нижний угол
                    path = QPainterPath()
                    path.moveTo(rect.topLeft())
                    path.lineTo(rect.topRight() - QPointF(self.radius, 0))
                    path.arcTo(QRectF(rect.topRight() - QPointF(2*self.radius, 0), QSizeF(2*self.radius, 2*self.radius)), 0, 90)
                    path.lineTo(rect.bottomRight())
                    path.lineTo(rect.bottomLeft())
                    path.closeSubpath()
                    path_item = QGraphicsPathItem(path)
                    path_item.setPen(pen)
                    path_item.setBrush(brush)
                    self.scene.addItem(path_item)
                else:
                    from PyQt6.QtWidgets import QGraphicsRectItem
                    rect_item = QGraphicsRectItem(rect)
                    rect_item.setPen(pen)
                    rect_item.setBrush(brush)
                    self.scene.addItem(rect_item)

                # Текст данных
                text = str(val) if pd.notna(val) else ""
                text_item = self.scene.addText(text, font)
                text_item.setDefaultTextColor(QColor("#212529"))
                text_item.setPos(x + 4, y + 4)

        # Обновляем размер сцены
        self.scene.setSceneRect(0, 0, total_width, total_height)
        self.fitInView(QRectF(0, 0, total_width, total_height), Qt.AspectRatioMode.IgnoreAspectRatio)

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