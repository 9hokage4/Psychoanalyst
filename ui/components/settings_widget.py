# ui/components/settings_widget.py
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QDialog, QGraphicsDropShadowEffect, QWidget, QGridLayout, QGroupBox, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QCheckBox, QScrollArea, QFrame, QSizePolicy, QStackedWidget,
    QLineEdit, QMessageBox, QAbstractButton, QLayout, QApplication
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFontMetrics
from PyQt6.QtCore import QPoint, QRect, QRectF, QSize, Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtSvg import QSvgRenderer
from pathlib import Path
from utils.profile_manager import ProfileManager
from ui.components.profile_dialog import ProfileDialog
from utils.fonts import get_font, FontWeights
from utils.resources import get_icon_path
from utils.folder_manager import FolderManager

class QFlowLayout(QLayout):
    """Flow layout для badge с переносом строк"""
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(Qt.Orientation.Horizontal)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size

    def _doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()
        for item in self.itemList:
            widget = item.widget()
            if widget:
                size_hint = widget.sizeHint()
                if x + size_hint.width() > rect.right():
                    x = rect.x()
                    y += line_height + spacing
                    line_height = 0
                if not testOnly:
                    widget.setGeometry(QRect(QPoint(x, y), size_hint))
                x += size_hint.width() + spacing
                line_height = max(line_height, size_hint.height())
        return y + line_height - rect.y()


class EditLevelDialog(QDialog):
    """Диалог редактирования уровня."""
    def __init__(self, name="", boundary=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование уровня")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        name_label = QLabel("Название уровня:")
        name_label.setFont(get_font("form_label"))
        name_label.setStyleSheet("color: #000000;")
        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Например, Низкий")
        self.name_edit.setFixedHeight(40)
        self.name_edit.setFont(get_font("form_input"))
        self.name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 18px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3390EC;
            }
        """)
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)

        bound_label = QLabel("Верхняя граница (баллов):")
        bound_label.setFont(get_font("form_label"))
        bound_label.setStyleSheet("color: #000000;")
        self.boundary_spin = QSpinBox()
        self.boundary_spin.setRange(1, 10000)
        self.boundary_spin.setValue(boundary)
        self.boundary_spin.setFixedHeight(40)
        self.boundary_spin.setFont(get_font("numeric"))
        self.boundary_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 24px 8px 12px;
                font-size: 18px;
                background-color: white;
                color: #000000;
            }
            QSpinBox:focus {
                border-color: #3390EC;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                background: transparent;
            }
            QSpinBox::up-arrow {
                image: url(resources/icons/chevron-up.svg);
                width: 12px;
                height: 12px;
            }
            QSpinBox::down-arrow {
                image: url(resources/icons/chevron-down.svg);
                width: 12px;
                height: 12px;
            }
        """)
        layout.addWidget(bound_label)
        layout.addWidget(self.boundary_spin)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(40)
        ok_btn.setFont(get_font("button"))
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
        """)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setFont(get_font("button"))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #3390EC;
                border: 1px solid #3390EC;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        return self.name_edit.text().strip(), self.boundary_spin.value()


class AnimatedCheckBox(QAbstractButton):
    """Кастомный чекбокс с анимацией переключения между двумя SVG-иконками"""
    def __init__(self, text="", unchecked_svg="resources/icons/checkbox_unchecked.svg",
                 checked_svg="resources/icons/checkbox_checked.svg",
                 icon_size=70, font_size=20, spacing=5, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        
        self.indicator_size = icon_size
        self.spacing = spacing
        self.text_color = QColor("#000000")
        
        font = QFont()
        font.setPointSize(font_size)
        font.setWeight(QFont.Weight.Normal)
        self.setFont(font)
        
        self.renderer_unchecked = QSvgRenderer(unchecked_svg)
        self.renderer_checked = QSvgRenderer(checked_svg)
        
        if not self.renderer_unchecked.isValid():
            print(f"Warning: {unchecked_svg} not found or invalid")
        if not self.renderer_checked.isValid():
            print(f"Warning: {checked_svg} not found or invalid")
        
        self._opacity = 0.0
        self._animation = QPropertyAnimation(self, b"opacity")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.toggled.connect(self._on_toggled)

    def sizeHint(self):
        text_width = self.fontMetrics().horizontalAdvance(self.text())
        return QSize(self.indicator_size + self.spacing + text_width,
                     self.indicator_size + 10)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        y = (self.height() - self.indicator_size) // 2
        icon_rect = QRectF(0, y, self.indicator_size, self.indicator_size)
        
        self._render_svg(painter, self.renderer_unchecked, icon_rect)
        
        if self._opacity > 0:
            painter.save()
            painter.setOpacity(self._opacity)
            self._render_svg(painter, self.renderer_checked, icon_rect)
            painter.restore()
        
        text_x = self.indicator_size + self.spacing
        text_rect = QRectF(text_x, 0, self.width() - text_x, self.height())
        painter.setPen(QPen(self.text_color))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())

    def _render_svg(self, painter, renderer, rect):
        if not renderer or not renderer.isValid():
            return
        viewBox = renderer.viewBox()
        if viewBox.isValid():
            scale = min(rect.width() / viewBox.width(), rect.height() / viewBox.height())
            new_width = viewBox.width() * scale
            new_height = viewBox.height() * scale
            x_offset = (rect.width() - new_width) / 2
            y_offset = (rect.height() - new_height) / 2
            target_rect = QRectF(rect.x() + x_offset, rect.y() + y_offset,
                                 new_width, new_height)
            renderer.render(painter, target_rect)
        else:
            renderer.render(painter, rect)

    def _on_toggled(self, checked):
        self._animation.stop()
        if checked:
            self._animation.setStartValue(0.0)
            self._animation.setEndValue(1.0)
        else:
            self._animation.setStartValue(1.0)
            self._animation.setEndValue(0.0)
        self._animation.start()

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.update()

    opacity = pyqtProperty(float, get_opacity, set_opacity)


class LevelBadge(QWidget):
    edited = pyqtSignal(object)
    deleted = pyqtSignal(object)

    BADGE_HEIGHT = 28

    def sizeHint(self):
        if self.index == self.total - 1:
            text = f"{self.level_data['name']} ({self.level_data['range_start']}+ баллов)"
        else:
            text = f"{self.level_data['name']} ({self.level_data['range_start']}-{self.level_data['range_end']} баллов)"
        font_metrics = self.fontMetrics()
        text_width = font_metrics.horizontalAdvance(text)
        extra_width = 12 + 8 + 8 + 4
        if not self.hide_delete:
            extra_width += 20
        return QSize(max(int(text_width + extra_width), 100), self.BADGE_HEIGHT)

    def __init__(self, level_data, index, total, parent=None, hide_delete=False):
        super().__init__(parent)
        self.level_data = level_data
        self.index = index
        self.total = total
        self.hide_delete = hide_delete

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(self.BADGE_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(100)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 8, 4)
        layout.setSpacing(8)

        if index == total - 1:
            text = f"{level_data['name']} ({level_data['range_start']}+ баллов)"
        else:
            text = f"{level_data['name']} ({level_data['range_start']}-{level_data['range_end']} баллов)"
        self.label = QLabel(text)
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.label)

        self.delete_btn = QPushButton()
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setIcon(QIcon("resources/icons/close.svg"))
        self.delete_btn.setIconSize(QSize(16, 16))
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.1);
            }
        """)
        if not hide_delete:
            self.delete_btn.clicked.connect(lambda: self.deleted.emit(self.level_data))
        layout.addWidget(self.delete_btn)
        if hide_delete:
            self.delete_btn.setVisible(False)

        self.bg_color = QColor(180, 209, 238)   # #b4d1ee
        self.text_color = QColor(6, 120, 234)   # #0678ea

        self.label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 17px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """)

        self.installEventFilter(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 14, 14)
        super().paintEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonDblClick and obj is self:
            self.edited.emit(self.level_data)
            return True
        return super().eventFilter(obj, event)

    def update_level_data(self, level_data):
        self.level_data = level_data
        if self.index == self.total - 1:
            text = f"{level_data['name']} ({level_data['range_start']}+ баллов)"
        else:
            text = f"{level_data['name']} ({level_data['range_start']}-{level_data['range_end']} баллов)"
        self.label.setText(text)
        self.update()
        self.updateGeometry()
        
        
class ScaleItem(QWidget):
    edit_clicked = pyqtSignal(object)
    delete_clicked = pyqtSignal(object)

    CARD_MIN_WIDTH = 640
    CARD_MIN_HEIGHT = 380
    CARD_MAX_WIDTH = 1440
    CARD_MAX_HEIGHT = 1200

    def sizeHint(self):
        return QSize(self.CARD_MIN_WIDTH, self.CARD_MIN_HEIGHT)

    def __init__(self, scale_data, parent=None):
        super().__init__(parent)
        self.scale_data = scale_data
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.setMinimumSize(self.CARD_MIN_WIDTH, self.CARD_MIN_HEIGHT)
        self.setMaximumSize(self.CARD_MAX_WIDTH, self.CARD_MAX_HEIGHT)

        self.setAutoFillBackground(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        self.title_label = QLabel(scale_data["name"])
        self.title_label.setFont(get_font("item_title"))
        self.title_label.setStyleSheet("""
    color: #000000;
    border: 1px solid #DFE1E5;
    border-radius: 12px;
    padding: 6px 14px;
    background-color: #FFFFFF;
""")
        top_layout.addWidget(self.title_label)

        q_count = len(scale_data.get("questions", []))
        self.count_label = QLabel(f"Количество вопросов: {q_count}")
        self.count_label.setFont(get_font("caption"))
        self.count_label.setStyleSheet("color: #58616a; border: none; margin: 0; padding: 0;")
        top_layout.addWidget(self.count_label)

        top_layout.addStretch()

        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon("resources/icons/edit.svg"))
        self.edit_btn.setIconSize(QSize(32, 32))
        self.edit_btn.setFixedSize(40, 40)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.05);
                border-radius: 20px;
            }
        """)
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.scale_data))
        top_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon("resources/icons/trash.svg"))
        self.delete_btn.setIconSize(QSize(32, 32))
        self.delete_btn.setFixedSize(40, 40)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.05);
                border-radius: 20px;
            }
        """)
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.scale_data))
        top_layout.addWidget(self.delete_btn)

        layout.addLayout(top_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #DFE1E5; max-height: 1px; margin: 4px 0 8px 0;")
        layout.addWidget(line)

        levels_title = QLabel("Уровни:")
        levels_title.setFont(get_font("caption"))
        levels_title.setStyleSheet("color: #000000; font-weight: 500; margin-bottom: 4px; border: none;")
        layout.addWidget(levels_title)

        self.levels_scroll = QScrollArea()
        self.levels_scroll.setWidgetResizable(False)
        self.levels_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.levels_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.levels_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.levels_scroll.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.levels_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #C4C9CC;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #A0A5A9;
            }
            QScrollBar:horizontal {
                background-color: transparent;
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background-color: #C4C9CC;
                border-radius: 4px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #A0A5A9;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                height: 0px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.levels_container = QWidget()
        self.levels_container.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.levels_container.setMinimumWidth(800)
        self.levels_container.setMaximumWidth(1600)

        self.BADGE_ROW_HEIGHT = 36
        self.MAX_ROWS_NO_SCROLL = 3

        self.levels_layout = QFlowLayout(self.levels_container)
        self.levels_layout.setContentsMargins(4, 4, 4, 4)
        self.levels_layout.setSpacing(8)
        self.levels_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.levels_scroll.setWidget(self.levels_container)

        self.levels_scroll.setMinimumHeight(self.BADGE_ROW_HEIGHT)
        self.levels_scroll.setMaximumHeight(self.BADGE_ROW_HEIGHT * self.MAX_ROWS_NO_SCROLL)
        self.levels_scroll.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        layout.addWidget(self.levels_scroll)

        questions_title = QLabel("Вопросы для шкалы:")
        questions_title.setFont(get_font("caption"))
        questions_title.setStyleSheet("color: #000000; font-weight: 500; margin: 8px 0 4px 0; border: none;")
        layout.addWidget(questions_title)

        self.questions_container = QWidget()
        self.questions_layout = QVBoxLayout(self.questions_container)
        self.questions_layout.setContentsMargins(0, 0, 0, 0)
        self.questions_layout.setSpacing(8)
        layout.addWidget(self.questions_container)

        self._update_levels_display()
        self._update_questions_display()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor(223, 225, 229), 2))
        painter.drawRoundedRect(self.rect(), 16, 16)
        super().paintEvent(event)

    def _format_questions_groups(self, questions):
        if not questions:
            return []
        q = sorted(questions)
        ranges = []
        start = q[0]
        end = q[0]
        for i in range(1, len(q)):
            if q[i] == end + 1:
                end = q[i]
            else:
                ranges.append(f"{start}-{end}" if start != end else str(start))
                start = q[i]
                end = q[i]
        ranges.append(f"{start}-{end}" if start != end else str(start))
        return ranges

    def _split_into_lines(self, items, max_per_line=5):
        lines = []
        for i in range(0, len(items), max_per_line):
            lines.append(", ".join(items[i:i+max_per_line]))
        return lines

    def _update_questions_display(self):
        while self.questions_layout.count():
            item = self.questions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        groups = self._format_questions_groups(self.scale_data.get("questions", []))
        if not groups:
            label = QLabel("—")
            label.setFont(get_font("table_cell"))
            label.setStyleSheet("""
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 6px 12px;
                background-color: #FFFFFF;
                color: #58616a;
            """)
            label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self.questions_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
            return

        lines = self._split_into_lines(groups, max_per_line=5)
        for line in lines:
            label = QLabel(line)
            label.setFont(get_font("table_cell"))
            label.setStyleSheet("""
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 6px 12px;
                background-color: #FFFFFF;
                color: #000000;
            """)
            label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self.questions_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _update_levels_display(self):
        while self.levels_layout.count():
            item = self.levels_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        levels = self.scale_data.get("levels", [])
        for i, lvl in enumerate(levels):
            badge = LevelBadge(lvl, i, len(levels), self, hide_delete=True)
            badge.setCursor(Qt.CursorShape.ArrowCursor)
            self.levels_layout.addWidget(badge)
        self.levels_layout.activate()

        self.levels_container.updateGeometry()
        self.levels_container.adjustSize()

        QtCore.QTimer.singleShot(100, self._adjust_levels_scroll_height)

    def _adjust_levels_scroll_height(self):
        badge_count = self.levels_layout.count()
        if badge_count == 0:
            return
        
        container_width = self.levels_container.width()
        if container_width <= 0:
            container_width = self.levels_scroll.width()
        
        rows_count = 1
        current_row_width = 0
        
        for i in range(badge_count):
            item = self.levels_layout.itemAt(i)
            if item and item.widget():
                badge = item.widget()
                badge_width = badge.sizeHint().width()
                
                if current_row_width + badge_width > container_width and current_row_width > 0:
                    rows_count += 1
                    current_row_width = badge_width + self.levels_layout.spacing()
                else:
                    current_row_width += badge_width + self.levels_layout.spacing()
        
        display_rows = min(rows_count, self.MAX_ROWS_NO_SCROLL)
        
        new_height = display_rows * self.BADGE_ROW_HEIGHT
        self.levels_scroll.setFixedHeight(new_height)
        
        actual_content_height = rows_count * self.BADGE_ROW_HEIGHT
        self.levels_container.setFixedHeight(actual_content_height)
        
        self.levels_layout.activate()
        self.levels_layout.update()
        self.levels_container.updateGeometry()
        self.levels_scroll.updateGeometry()
        self.levels_scroll.adjustSize()

    def update_data(self, scale_data):
        self.scale_data = scale_data
        self.title_label.setText(scale_data["name"])
        q_count = len(scale_data.get("questions", []))
        self.count_label.setText(f"Количество вопросов: {q_count}")
        self._update_levels_display()
        self._update_questions_display()
        
class ScaleLevelWidget(QWidget):
    """Виджет одного уровня внутри шкалы (для AddScaleDialog)."""
    edit_requested = pyqtSignal(object)
    delete_requested = pyqtSignal(object)

    def __init__(self, level_data, parent=None):
        super().__init__(parent)
        self.level_data = level_data
        self.setFixedHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        start = level_data.get('range_start', 0)
        end = level_data.get('range_end', level_data['boundary'])
        text = f"{level_data['name']} ({start}-{end} баллов)"
        self.label = QLabel(text)
        self.label.setStyleSheet("color: #000000; font-size: 17px;")
        layout.addWidget(self.label, 1)

        edit_btn = QPushButton()
        edit_btn.setIcon(QIcon("resources/icons/edit.svg"))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setFixedSize(24, 24)
        edit_btn.setStyleSheet("border: none; background: transparent;")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.level_data))
        layout.addWidget(edit_btn)

        del_btn = QPushButton()
        del_btn.setIcon(QIcon("resources/icons/close.svg"))
        del_btn.setIconSize(QSize(16, 16))
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("border: none; background: transparent;")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.level_data))
        layout.addWidget(del_btn)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonDblClick and obj is self:
            self.edit_requested.emit(self.level_data)
            return True
        return super().eventFilter(obj, event)

    def update_display(self):
        start = self.level_data.get('range_start', 0)
        end = self.level_data.get('range_end', self.level_data['boundary'])
        text = f"{self.level_data['name']} ({start}-{end} баллов)"
        self.label.setText(text)


class AddLevelToScaleDialog(QDialog):
    """Диалог добавления нового уровня (имя + граница) для шкалы."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить уровень")
        self.setModal(True)
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Название уровня:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("например, Очень высокий")
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Верхняя граница (баллов):"))
        self.boundary_spin = QSpinBox()
        self.boundary_spin.setRange(1, 10000)
        self.boundary_spin.setValue(50)
        layout.addWidget(self.boundary_spin)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Добавить")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        return self.name_edit.text().strip(), self.boundary_spin.value()


class AddScaleDialog(QDialog):
    """Диалог добавления/редактирования шкалы с редактируемыми уровнями."""
    def __init__(self, parent=None, scale_data=None):
        super().__init__(parent)
        self.parent_dialog = parent
        self.scale_data = scale_data or {}
        self.setWindowTitle("Добавить шкалу" if not scale_data else "Редактировать шкалу")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
            QLabel {
                color: #000000;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Название шкалы
        name_label = QLabel("Название шкалы:")
        name_label.setStyleSheet("font-size: 17px; font-weight: 500; color: #707579;")
        self.name_edit = QLineEdit(self.scale_data.get("name", ""))
        self.name_edit.setPlaceholderText("например, 'Тревожность'")
        self.name_edit.setFixedHeight(40)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 18px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3390EC;
            }
        """)
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)

        # Вопросы
        questions_label = QLabel("Вопросы:")
        questions_label.setStyleSheet("font-size: 17px; font-weight: 500; color: #707579;")
        self.questions_edit = QLineEdit()
        if "questions" in self.scale_data:
            q_list = sorted(self.scale_data["questions"])
            ranges = []
            if q_list:
                start = q_list[0]
                end = q_list[0]
                for i in range(1, len(q_list)):
                    if q_list[i] == end + 1:
                        end = q_list[i]
                    else:
                        ranges.append(f"{start}-{end}" if start != end else str(start))
                        start = q_list[i]
                        end = q_list[i]
                ranges.append(f"{start}-{end}" if start != end else str(start))
                self.questions_edit.setText(", ".join(ranges))
        self.questions_edit.setPlaceholderText("Пример: 1-20, 25, 30-40")
        self.questions_edit.setFixedHeight(40)
        self.questions_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 18px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3390EC;
            }
        """)
        layout.addWidget(questions_label)
        layout.addWidget(self.questions_edit)

        # Уровни
        levels_label = QLabel("Уровни:")
        levels_label.setStyleSheet("font-size: 17px; font-weight: 500; color: #707579; margin-top: 8px;")
        layout.addWidget(levels_label)

        self.levels_container = QWidget()
        self.levels_layout = QVBoxLayout(self.levels_container)
        self.levels_layout.setContentsMargins(0, 0, 0, 0)
        self.levels_layout.setSpacing(6)
        layout.addWidget(self.levels_container)

        add_level_btn = QPushButton("+ Добавить уровень")
        add_level_btn.setFixedHeight(32)
        add_level_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        font_metrics = add_level_btn.fontMetrics()
        text_width = font_metrics.horizontalAdvance(add_level_btn.text())
        add_level_btn.setFixedWidth(text_width + 40)
        add_level_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 17px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
        """)
        add_level_btn.clicked.connect(self._add_new_level)
        layout.addWidget(add_level_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setFixedHeight(36)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
        """)
        self.save_btn.clicked.connect(self._validate_and_accept)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #3390EC;
                border: 1px solid #3390EC;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.selected_levels = []
        self._init_levels()

    def _init_levels(self):
        if self.scale_data and "levels" in self.scale_data:
            self.selected_levels = [lvl.copy() for lvl in self.scale_data["levels"]]
        else:
            parent = self.parent_dialog
            if hasattr(parent, 'levels_data'):
                global_levels = parent.levels_data
                prev_boundary = 0
                self.selected_levels = []
                for lvl in global_levels:
                    boundary = lvl['boundary']
                    start = prev_boundary + 1
                    end = boundary
                    self.selected_levels.append({
                        'name': lvl['name'],
                        'boundary': boundary,
                        'range_start': start,
                        'range_end': end
                    })
                    prev_boundary = boundary
        self._refresh_levels_display()

    def _refresh_levels_display(self):
        while self.levels_layout.count():
            item = self.levels_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.selected_levels.sort(key=lambda x: x['boundary'])

        prev = 0
        for lvl in self.selected_levels:
            lvl['range_start'] = prev + 1
            lvl['range_end'] = lvl['boundary']
            prev = lvl['boundary']

        for lvl in self.selected_levels:
            widget = ScaleLevelWidget(lvl)
            widget.edit_requested.connect(self._edit_level)
            widget.delete_requested.connect(self._delete_level)
            self.levels_layout.addWidget(widget)

        self.levels_layout.addStretch()

    def _add_new_level(self):
        dialog = AddLevelToScaleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, boundary = dialog.get_data()
            if name and boundary > 0:
                new_level = {
                    'name': name,
                    'boundary': boundary,
                    'range_start': 0,
                    'range_end': 0
                }
                self.selected_levels.append(new_level)
                self._refresh_levels_display()

    def _edit_level(self, level_data):
        dialog = EditLevelDialog(level_data['name'], level_data['boundary'], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name, new_boundary = dialog.get_data()
            if new_name and new_boundary > 0:
                level_data['name'] = new_name
                level_data['boundary'] = new_boundary
                self._refresh_levels_display()

    def _delete_level(self, level_data):
        self.selected_levels.remove(level_data)
        self._refresh_levels_display()

    def _validate_and_accept(self):
        data = self.get_data()
        if data is not None:
            self.accept()

    def get_data(self):
        name = self.name_edit.text().strip()
        questions_text = self.questions_edit.text().strip()

        if not name:
            self.parent_dialog._show_error_message("Ошибка валидации", "Название шкалы обязательно.")
            return None

        questions = self._parse_questions(questions_text)
        if questions is None:
            return None

        if not questions:
            self.parent_dialog._show_error_message("Ошибка валидации", "Укажите хотя бы один вопрос.")
            return None

        max_question = max(questions)
        max_allowed = self.parent_dialog.questions_spin.value()
        if max_question > max_allowed:
            self.parent_dialog._show_error_message(
                "Ошибка валидации",
                f"Номер вопроса {max_question} превышает лимит ({max_allowed})."
            )
            return None

        if not self.parent_dialog.shared_checkbox.isChecked():
            all_questions = {}
            scales = self.parent_dialog.scales
            if self.scale_data and "name" in self.scale_data:
                scales = [s for s in scales if s.get("name") != self.scale_data["name"]]

            for scale in scales:
                for q in scale.get("questions", []):
                    if q not in all_questions:
                        all_questions[q] = []
                    all_questions[q].append(scale["name"])

            duplicate = [q for q in questions if q in all_questions]
            if duplicate:
                error = f"Вопросы {', '.join(map(str, duplicate))} уже используются:\n"
                for q in sorted(duplicate):
                    error += f"  Вопрос {q}: {', '.join(all_questions[q])}\n"
                error += "\nРазрешите повтор вопросов в настройках."
                self.parent_dialog._show_error_message("Ошибка валидации", error)
                return None

        if not self.selected_levels:
            self.parent_dialog._show_error_message("Ошибка валидации", "Добавьте хотя бы один уровень.")
            return None

        return {"name": name, "questions": questions, "levels": self.selected_levels.copy()}

    def _parse_questions(self, text):
        if not text:
            return []
        parts = text.split(',')
        questions = set()
        invalid = []
        max_allowed = self.parent_dialog.questions_spin.value()

        for part in parts:
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if start > end or start < 1 or end > max_allowed:
                        invalid.append(part)
                        continue
                    questions.update(range(start, end + 1))
                except ValueError:
                    invalid.append(part)
            else:
                try:
                    q = int(part)
                    if q < 1 or q > max_allowed:
                        invalid.append(part)
                        continue
                    questions.add(q)
                except ValueError:
                    invalid.append(part)

        if invalid:
            self.parent_dialog._show_error_message(
                "Ошибка валидации",
                f"Некорректные номера: {', '.join(invalid)}.\n"
                f"Допустимы числа 1-{max_allowed} или диапазоны вида 1-10."
            )
            return None

        return sorted(questions)
    
class SettingsWidget(QWidget):
    config_saved = pyqtSignal(dict, str)
    profile_loaded_with_name = pyqtSignal(str, dict)

    def __init__(self, parent=None, initial_config=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки теста")
        self.scales = []
        self.levels = []
        self.level_order = []
        self.levels_data = []
        self.profile_manager = ProfileManager()
        self.current_config = initial_config
        self.current_profile_name = None
        self.output_folder_path = ""
        self.folder_manager = FolderManager()
        self._load_folder_settings()
        self.init_ui()
        if initial_config:
            self._load_config(initial_config)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Горизонтальный контейнер: боковая панель + контентная панель (как в результатах)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # === ЛЕВАЯ ВЕРТИКАЛЬНАЯ ПАНЕЛЬ (точно как в ResultsWidget) ===
        self.sidebar = QWidget()
        self.sidebar.setObjectName("settings_sidebar")
        self.sidebar.setFixedSize(140, 550)
        sidebar_shadow = QGraphicsDropShadowEffect()
        sidebar_shadow.setBlurRadius(20)
        sidebar_shadow.setOffset(0, 4)
        sidebar_shadow.setColor(QColor(0, 0, 0, 20))
        self.sidebar.setGraphicsEffect(sidebar_shadow)
        self.sidebar.setStyleSheet("""
            QWidget#settings_sidebar {
                background-color: #FFFFFF;
                border-radius: 70px;
            }
        """)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 40)
        sidebar_layout.setSpacing(16)
        sidebar_layout.addStretch()

        self.nav_buttons = []
        from ui.components.results_nav_button import ResultsNavButton
        btn_data = [
            ("resources/icons/cog.svg", "Основные"),
            ("resources/icons/chart-line.svg", "Уровни"),
            ("resources/icons/charts.svg", "Шкалы"),
            ("resources/icons/scale.svg", "Веса")
        ]
        for icon, text in btn_data:
            btn = ResultsNavButton(icon, text)
            btn.setObjectName(f"settings_nav_{text}")
            btn.clicked.connect(lambda checked=False, idx=len(self.nav_buttons): self.switch_settings_tab(idx))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        sidebar_layout.addStretch()
        content_layout.addWidget(self.sidebar)

        # === КОНТЕНТНАЯ ПАНЕЛЬ ===
        content_panel = QWidget()
        content_panel.setObjectName("settings_content")
        content_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_shadow = QGraphicsDropShadowEffect()
        content_shadow.setBlurRadius(20)
        content_shadow.setOffset(0, 4)
        content_shadow.setColor(QColor(0, 0, 0, 20))
        content_panel.setGraphicsEffect(content_shadow)
        content_panel.setStyleSheet("""
            QWidget#settings_content {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
        """)
        content_inner = QVBoxLayout(content_panel)
        content_inner.setContentsMargins(24, 24, 24, 24)
        content_inner.setSpacing(16)

        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet("background-color: transparent;")
        self.basic_tab = self._create_basic_tab()
        self.levels_tab = self._create_levels_tab()
        self.scales_tab = self._create_scales_tab()
        self.weights_tab = self._create_weights_tab()
        self.stacked.addWidget(self.basic_tab)
        self.stacked.addWidget(self.levels_tab)
        self.stacked.addWidget(self.scales_tab)
        self.stacked.addWidget(self.weights_tab)
        content_inner.addWidget(self.stacked)
        content_layout.addWidget(content_panel, 1)  # растягивается

        main_layout.addLayout(content_layout)

        # === КНОПКИ ПОД КОНТЕНТОМ, ПО ЦЕНТРУ ЭКРАНА ===
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(10)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.profile_btn = QPushButton("Профили")
        self.profile_btn.setObjectName("btn_profile")
        self.profile_btn.setFixedHeight(56)
        self.profile_btn.setFont(get_font("button", size=16, weight=FontWeights.SEMIBOLD))
        self.profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 48px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #CCCCCC; }
        """)
        self.profile_btn.clicked.connect(self.open_profile_dialog)
        btn_row.addWidget(self.profile_btn)

        self.save_btn = QPushButton("Сохранить настройки")
        self.save_btn.setObjectName("btn_save")
        self.save_btn.setFixedHeight(56)
        self.save_btn.setFont(get_font("button", size=16, weight=FontWeights.SEMIBOLD))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6BBF8A;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 48px;
            }
            QPushButton:hover { background-color: #5AA878; }
            QPushButton:disabled { background-color: #CCCCCC; }
        """)
        self.save_btn.clicked.connect(self.save_config)
        btn_row.addWidget(self.save_btn)

        main_layout.addLayout(btn_row)

        # === СТИЛИ ДЛЯ КНОПОК НАВИГАЦИИ (как в ResultsWidget) ===
        self.setStyleSheet("""
            ResultsNavButton {
                background-color: transparent;
                border: none;
                min-width: 80px;
                max-width: 80px;
                min-height: 90px;
                max-height: 90px;
                border-radius: 70px;
                padding: 8px;
                font-size: 12px;
            }
            ResultsNavButton:hover {
                background-color: #F4F4F5;
            }
            ResultsNavButton:checked {
                background-color: #b4d1ee;
            }
            ResultsNavButton QLabel {
                background-color: transparent;
            }
            ResultsNavButton #nav_text {
                font-size: 12px;
            }
        """)

        self.nav_buttons[0].setChecked(True)
        self.switch_settings_tab(0)

    def switch_settings_tab(self, index):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stacked.setCurrentIndex(index)

    # ========== Методы создания вкладок ==========
    def _create_basic_tab(self):
        from PyQt6.QtWidgets import QFileDialog
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical { background-color: #F5F5F5; width: 12px; border-radius: 6px; }
            QScrollBar::handle:vertical { background-color: #BDBDBD; border-radius: 6px; min-height: 40px; }
            QScrollBar::handle:vertical:hover { background-color: #9E9E9E; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(24)

        # Название теста
        name_group = QVBoxLayout()
        name_group.setSpacing(6)
        name_label = QLabel("Название теста")
        name_label.setFont(get_font("form_label"))
        name_label.setStyleSheet("color: #707579;")
        self.test_name_edit = QLineEdit()
        self.test_name_edit.setPlaceholderText("Введите название")
        self.test_name_edit.setFixedHeight(40)
        self.test_name_edit.setFont(get_font("form_input"))
        self.test_name_edit.setStyleSheet("""
            QLineEdit { border: 1px solid #DFE1E5; border-radius: 8px; padding: 8px 12px; font-size: 18px; background-color: white; color: #000000; }
            QLineEdit:focus { border-color: #3390EC; }
        """)
        self.test_name_edit.textChanged.connect(self._update_folder_display)
        name_group.addWidget(name_label)
        name_group.addWidget(self.test_name_edit)

        questions_group = QVBoxLayout()
        questions_group.setSpacing(6)
        questions_label = QLabel("Количество вопросов")
        questions_label.setFont(get_font("form_label"))
        questions_label.setStyleSheet("color: #707579;")
        self.questions_spin = QSpinBox()
        self.questions_spin.setRange(1, 1000)
        self.questions_spin.setValue(10)
        self.questions_spin.setFixedHeight(40)
        self.questions_spin.setFont(get_font("numeric"))
        self.questions_spin.setStyleSheet("""
            QSpinBox { border: 1px solid #DFE1E5; border-radius: 8px; padding: 8px 24px 8px 12px; font-size: 18px; background-color: white; color: #000000; }
            QSpinBox:focus { border-color: #3390EC; }
            QSpinBox::up-button, QSpinBox::down-button { width: 20px; border: none; background: transparent; }
            QSpinBox::up-arrow { image: url(resources/icons/chevron-up.svg); width: 12px; height: 12px; }
            QSpinBox::down-arrow { image: url(resources/icons/chevron-down.svg); width: 12px; height: 12px; }
        """)
        self.questions_spin.valueChanged.connect(self.on_questions_changed)
        questions_group.addWidget(questions_label)
        questions_group.addWidget(self.questions_spin)

        row1 = QHBoxLayout()
        row1.setSpacing(16)
        row1.addLayout(name_group)
        row1.addLayout(questions_group)
        content_layout.addLayout(row1)

        answers_group = QVBoxLayout()
        answers_group.setSpacing(6)
        answers_label = QLabel("Количество вариантов ответов")
        answers_label.setFont(get_font("form_label"))
        answers_label.setStyleSheet("color: #707579;")
        self.answers_spin = QSpinBox()
        self.answers_spin.setRange(2, 100)
        self.answers_spin.setValue(5)
        self.answers_spin.setFixedHeight(40)
        self.answers_spin.setFont(get_font("numeric"))
        self.answers_spin.setStyleSheet("""
            QSpinBox { border: 1px solid #DFE1E5; border-radius: 8px; padding: 8px 24px 8px 12px; font-size: 18px; background-color: white; color: #000000; }
            QSpinBox:focus { border-color: #3390EC; }
            QSpinBox::up-button, QSpinBox::down-button { width: 20px; border: none; background: transparent; }
            QSpinBox::up-arrow { image: url(resources/icons/chevron-up.svg); width: 12px; height: 12px; }
            QSpinBox::down-arrow { image: url(resources/icons/chevron-down.svg); width: 12px; height: 12px; }
        """)
        self.answers_spin.valueChanged.connect(self.on_answers_changed)
        answers_group.addWidget(answers_label)
        answers_group.addWidget(self.answers_spin)
        content_layout.addLayout(answers_group)

        desc_group = QVBoxLayout()
        desc_group.setSpacing(6)
        desc_label = QLabel("Описание теста")
        desc_label.setFont(get_font("form_label"))
        desc_label.setStyleSheet("color: #707579;")
        self.test_description_edit = QTextEdit()
        self.test_description_edit.setPlaceholderText("Введите описание теста...")
        self.test_description_edit.setFixedHeight(100)
        self.test_description_edit.setFont(get_font("form_input"))
        self.test_description_edit.setStyleSheet("""
            QTextEdit { border: 1px solid #DFE1E5; border-radius: 8px; padding: 8px 12px; font-size: 18px; background-color: white; color: #000000; }
            QTextEdit:focus { border-color: #3390EC; }
        """)
        desc_group.addWidget(desc_label)
        desc_group.addWidget(self.test_description_edit)
        content_layout.addLayout(desc_group)

        checkbox_group = QVBoxLayout()
        checkbox_group.setSpacing(4)
        self.shared_checkbox = AnimatedCheckBox("Вопросы для различных шкал одинаковы")
        self.shared_checkbox.setChecked(False)
        checkbox_group.addWidget(self.shared_checkbox)
        hint = QLabel("Если активно — один вопрос может относиться к нескольким шкалам")
        hint.setFont(get_font("hint"))
        hint.setStyleSheet("color: #707579;")
        hint.setContentsMargins(32, 0, 0, 0)
        checkbox_group.addWidget(hint)
        content_layout.addLayout(checkbox_group)

        folder_layout = QHBoxLayout()
        folder_layout.setContentsMargins(0, 10, 0, 0)
        folder_layout.setSpacing(8)
        self.folder_btn = QPushButton("Выбор папки")
        self.folder_btn.setFixedHeight(40)
        self.folder_btn.setFont(get_font("button_small"))
        self.folder_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #3390EC; border: 1px solid #3390EC; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background-color: #F4F4F5; }
        """)
        self.folder_btn.clicked.connect(self.select_folder)
        self.folder_btn.setMaximumWidth(200)
        folder_layout.addWidget(self.folder_btn)
        folder_layout.addStretch()
        content_layout.addLayout(folder_layout)

        self.folder_path_label = QLabel("")
        self.folder_path_label.setFont(get_font("hint"))
        self.folder_path_label.setStyleSheet("color: #707579;")
        self.folder_path_label.setWordWrap(True)
        content_layout.addWidget(self.folder_path_label)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        return tab

    def _create_levels_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        title_label = QLabel("Активные уровни")
        title_label.setStyleSheet("color: #000000; font-size: 18px; font-weight: 600;")
        layout.addWidget(title_label)
        layout.addSpacing(8)

        self.levels_container = QWidget()
        self.levels_container.setMinimumHeight(36)
        self.levels_container.setStyleSheet("background-color: transparent")
        self.levels_layout = QFlowLayout(self.levels_container)
        self.levels_layout.setContentsMargins(0, 0, 0, 0)
        self.levels_layout.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.levels_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(150)
        scroll.setMinimumWidth(400)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background-color: #F0F0F0; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background-color: #C4C9CC; border-radius: 4px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background-color: #A0A5A9; }
            QScrollBar:horizontal { background-color: #F0F0F0; height: 8px; border-radius: 4px; }
            QScrollBar::handle:horizontal { background-color: #C4C9CC; border-radius: 4px; min-width: 30px; }
            QScrollBar::handle:horizontal:hover { background-color: #A0A5A9; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { height: 0px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        layout.addWidget(scroll)
        layout.addSpacing(16)

        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame { background-color: #F8F9FA; border: 1px solid #DFE1E5; border-radius: 8px; padding: 8px; }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(6)

        form_title = QLabel("Настройка уровня")
        form_title.setStyleSheet("color: #000000; font-size: 14px; font-weight: 600; margin-bottom: 0px; border: none; background: transparent;")
        form_title.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        form_layout.addWidget(form_title)

        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(10)
        self.level_name_edit = QLineEdit()
        self.level_name_edit.setPlaceholderText("Название уровня")
        self.level_name_edit.setFixedHeight(40)
        self.level_name_edit.setStyleSheet("""
            QLineEdit { border: 1px solid #DFE1E5; border-radius: 8px; padding: 6px 12px; font-size: 18px; background-color: white; }
            QLineEdit:focus { border-color: #3390EC; }
        """)
        fields_layout.addWidget(self.level_name_edit, 1)

        self.level_boundary_spin = QSpinBox()
        self.level_boundary_spin.setRange(1, 10000)
        self.level_boundary_spin.setValue(10)
        self.level_boundary_spin.setFixedHeight(40)
        self.level_boundary_spin.setStyleSheet("""
            QSpinBox { border: 1px solid #DFE1E5; border-radius: 8px; padding: 6px 12px; font-size: 18px; background-color: white; color: #000000; }
            QSpinBox:focus { border-color: #3390EC; }
            QSpinBox::up-button, QSpinBox::down-button { width: 20px; border: none; background: transparent; }
            QSpinBox::up-arrow { image: url(resources/icons/chevron-up.svg); width: 12px; height: 12px; }
            QSpinBox::down-arrow { image: url(resources/icons/chevron-down.svg); width: 12px; height: 12px; }
        """)
        fields_layout.addWidget(self.level_boundary_spin, 1)
        form_layout.addLayout(fields_layout)

        add_btn = QPushButton("+ Добавить уровень")
        add_btn.setFixedHeight(36)
        add_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        fm = add_btn.fontMetrics()
        add_btn.setFixedWidth(fm.horizontalAdvance(add_btn.text()) + 60)
        add_btn.setStyleSheet("""
            QPushButton { background-color: #3390EC; color: white; border: none; border-radius: 8px; padding: 8px 16px; font-size: 18px; font-weight: 500; }
            QPushButton:hover { background-color: #2B80D9; }
        """)
        add_btn.clicked.connect(self._add_level_from_form)
        form_layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(form_frame)
        self.levels_data = [
            {'name': 'Низкий', 'boundary': 15},
            {'name': 'Средний', 'boundary': 30},
            {'name': 'Высокий', 'boundary': 45}
        ]
        self._refresh_levels_display()
        return tab

    def _create_scales_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("Список шкал")
        title_label.setStyleSheet("color: #000000; font-size: 20px; font-weight: 600;")
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        add_btn = QPushButton("+ Добавить шкалу")
        add_btn.setFixedHeight(40)
        add_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        fm = add_btn.fontMetrics()
        add_btn.setFixedWidth(fm.horizontalAdvance(add_btn.text()) + 70)
        add_btn.setStyleSheet("""
            QPushButton { background-color: #3390EC; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 19px; font-weight: 500; }
            QPushButton:hover { background-color: #2B80D9; }
        """)
        add_btn.clicked.connect(self._add_scale_from_form)
        top_layout.addWidget(add_btn)
        layout.addLayout(top_layout)

        line_container = QWidget()
        line_container.setStyleSheet("background-color: transparent;")
        line_layout = QHBoxLayout(line_container)
        line_layout.setContentsMargins(0, 0, 0, 0)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #DFE1E5; max-height: 1px;")
        line_layout.addWidget(line)
        layout.addWidget(line_container)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background-color: #F5F5F5; border: none; border-radius: 12px; }
            QScrollBar:vertical { background-color: transparent; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background-color: #C4C9CC; border-radius: 5px; min-height: 40px; }
            QScrollBar::handle:vertical:hover { background-color: #A0A5A9; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self.scales_container = QWidget()
        self.scales_container.setStyleSheet("background-color: transparent;")
        self.scales_layout = QVBoxLayout(self.scales_container)
        self.scales_layout.setContentsMargins(12, 12, 12, 12)
        self.scales_layout.setSpacing(12)
        self.scales_layout.addStretch()
        scroll.setWidget(self.scales_container)
        layout.addWidget(scroll, 1)
        self._refresh_scales_list()
        return tab

    def _create_weights_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        weights_group = QGroupBox("Веса ответов для каждого вопроса")
        weights_group.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #DFE1E5; border-radius: 8px; margin-top: 12px; padding-top: 12px; color: #212529; font-size: 14px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px; color: #3390EC; font-size: 14px; }
        """)
        group_layout = QVBoxLayout(weights_group)
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(0)

        self.weights_container = QWidget()
        self.weights_container.setStyleSheet("background: transparent;")
        self.weights_layout = QVBoxLayout(self.weights_container)
        self.weights_layout.setContentsMargins(0, 0, 0, 0)
        self.weights_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.weights_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        scroll.setMinimumHeight(60)
        scroll.setMaximumHeight(300)
        scroll.setObjectName("weights_scroll_area")
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background-color: #F0F0F0; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background-color: #C4C9CC; border-radius: 4px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background-color: #A0A5A9; }
            QScrollBar:horizontal { background-color: #F0F0F0; height: 8px; border-radius: 4px; }
            QScrollBar::handle:horizontal { background-color: #C4C9CC; border-radius: 4px; min-width: 30px; }
            QScrollBar::handle:horizontal:hover { background-color: #A0A5A9; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { height: 0px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        group_layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 8, 0, 0)
        btn_layout.setSpacing(10)
        self.cancel_unify_btn = QPushButton("Отмена")
        self.cancel_unify_btn.setFixedHeight(32)
        self.cancel_unify_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.cancel_unify_btn.setFixedWidth(self.cancel_unify_btn.fontMetrics().horizontalAdvance("Отмена") + 40)
        self.cancel_unify_btn.setStyleSheet("""
            QPushButton { background-color: #FFFFFF; color: #3390EC; border: 1px solid #3390EC; border-radius: 8px; padding: 6px 12px; font-size: 17px; font-weight: 500; }
            QPushButton:hover { background-color: #F5F5F5; }
        """)
        self.cancel_unify_btn.clicked.connect(self._cancel_unify_weights)
        self.cancel_unify_btn.setVisible(False)
        btn_layout.addWidget(self.cancel_unify_btn)

        self.apply_all_btn = QPushButton("Применить ко всем вопросам")
        self.apply_all_btn.setFixedHeight(32)
        self.apply_all_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.apply_all_btn.setFixedWidth(self.apply_all_btn.fontMetrics().horizontalAdvance("Применить ко всем вопросам") + 40)
        self.apply_all_btn.setStyleSheet("""
            QPushButton { background-color: #FFFFFF; color: #3390EC; border: 1px solid #3390EC; border-radius: 8px; padding: 6px 12px; font-size: 17px; font-weight: 500; }
            QPushButton:hover { background-color: #F5F5F5; }
            QPushButton:disabled { background-color: #F5F5F5; color: #ADB5BD; border-color: #ADB5BD; }
        """)
        self.apply_all_btn.clicked.connect(self._apply_weights_to_all)
        btn_layout.addWidget(self.apply_all_btn)
        group_layout.addLayout(btn_layout)

        layout.addWidget(weights_group)
        self._refresh_weights_tab()
        return tab

    # ========== Веса ==========
    def _refresh_weights_tab(self):
        q_count = self.questions_spin.value()
        a_count = self.answers_spin.value()
        while self.weights_layout.count():
            item = self.weights_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.weight_spins = []
        if hasattr(self, '_weights_unified') and self._weights_unified:
            row, spins = self._create_unified_weights_row(q_count, a_count)
            self.weights_layout.addWidget(row)
            self.weight_spins.append(spins)
            self.apply_all_btn.setEnabled(False)
            self.cancel_unify_btn.setVisible(True)
        else:
            for i in range(1, q_count + 1):
                row, spins = self._create_question_row(i, a_count)
                self.weights_layout.addWidget(row)
                self.weight_spins.append(spins)
            self.apply_all_btn.setEnabled(True)
            self.cancel_unify_btn.setVisible(False)

    def _create_question_row(self, question_num, answer_count):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        label = QLabel(f"Вопрос {question_num}")
        label.setStyleSheet("font-size: 18px; font-weight: 500; color: #000000; min-width: 80px; margin-left: 8px;")
        layout.addWidget(label)
        spins = []
        for j in range(1, answer_count + 1):
            spin = QSpinBox()
            spin.setRange(1, 100)
            spin.setValue(j)
            spin.setFixedHeight(40)
            spin.setStyleSheet("""
                QSpinBox { border: 1px solid #DFE1E5; border-radius: 8px; padding: 4px 8px; font-size: 18px; background-color: white; color: #000000; }
                QSpinBox:focus { border-color: #3390EC; }
                QSpinBox::up-button, QSpinBox::down-button { width: 20px; border: none; background: transparent; }
                QSpinBox::up-arrow { image: url(resources/icons/chevron-up.svg); width: 12px; height: 12px; }
                QSpinBox::down-arrow { image: url(resources/icons/chevron-down.svg); width: 12px; height: 12px; }
            """)
            layout.addWidget(spin)
            spins.append(spin)
        layout.addStretch()
        return row, spins

    def _create_unified_weights_row(self, question_count, answer_count):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        label = QLabel("Вопрос")
        label.setStyleSheet("font-size: 18px; font-weight: 500; color: #000000; min-width: 80px; margin-left: 8px;")
        layout.addWidget(label)
        spins = []
        for j in range(1, answer_count + 1):
            spin = QSpinBox()
            spin.setRange(1, 100)
            spin.setValue(j)
            spin.setFixedHeight(40)
            spin.setStyleSheet("""
                QSpinBox { border: 1px solid #DFE1E5; border-radius: 8px; padding: 4px 8px; font-size: 18px; background-color: white; color: #000000; }
                QSpinBox:focus { border-color: #3390EC; }
                QSpinBox::up-button, QSpinBox::down-button { width: 20px; border: none; background: transparent; }
                QSpinBox::up-arrow { image: url(resources/icons/chevron-up.svg); width: 12px; height: 12px; }
                QSpinBox::down-arrow { image: url(resources/icons/chevron-down.svg); width: 12px; height: 12px; }
            """)
            layout.addWidget(spin)
            spins.append(spin)
        layout.addStretch()
        return row, spins

    def _apply_weights_to_all(self):
        if self.weights_layout.count() <= 1:
            return
        first_row = self.weights_layout.itemAt(0).widget()
        first_row_spins = [child for child in first_row.findChildren(QSpinBox)]
        while self.weights_layout.count() > 1:
            item = self.weights_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        label = first_row.findChild(QLabel)
        if label:
            label.setText("Вопрос")
        self._weights_unified = True
        self.apply_all_btn.setEnabled(False)
        self.cancel_unify_btn.setVisible(True)
        self.weight_spins = [first_row_spins]
        scroll = self.weights_tab.findChild(QScrollArea, "weights_scroll_area")
        if scroll:
            scroll.setMinimumHeight(60)
            scroll.setMaximumHeight(60)
        self.weights_layout.activate()
        self.weights_container.updateGeometry()
        self.weights_container.adjustSize()

    def _cancel_unify_weights(self):
        self._weights_unified = False
        if hasattr(self, '_weights_unified'):
            del self._weights_unified
        self._refresh_weights_tab()
        scroll = self.weights_tab.findChild(QScrollArea, "weights_scroll_area")
        if scroll:
            scroll.setMinimumHeight(60)
            scroll.setMaximumHeight(300)

    def on_questions_changed(self, value):
        if hasattr(self, 'weights_layout'):
            self._refresh_weights_tab()

    def on_answers_changed(self, value):
        if hasattr(self, 'weights_layout'):
            self._refresh_weights_tab()

    # ========== Сохранение и загрузка ==========
    def save_config(self):
        if self.questions_spin.value() < 1:
            self._show_error_message("Ошибка", "Количество вопросов должно быть больше 0")
            return
        if self.answers_spin.value() < 2:
            self._show_error_message("Ошибка", "Количество ответов должно быть минимум 2")
            return
        if len(self.levels_data) < 1:
            self._show_error_message("Ошибка", "Добавьте хотя бы один уровень показателей")
            self.switch_settings_tab(1)
            return
        for i, lvl in enumerate(self.levels_data):
            if not lvl['name'].strip():
                self._show_error_message("Ошибка", f"Уровень {i+1} не имеет названия")
                self.switch_settings_tab(1)
                return
        if len(self.scales) < 1:
            self._show_error_message("Ошибка", "Добавьте хотя бы одну шкалу")
            self.switch_settings_tab(2)
            return

        level_order = []
        level_ru = {}
        for i, lvl in enumerate(self.levels_data):
            if i == 0: key = "low"
            elif i == 1: key = "mid_low"
            elif i == 2: key = "mid_high"
            elif i == 3: key = "high"
            else: key = f"level{i+1}"
            level_order.append(key)
            level_ru[key] = lvl['name']

        scales_config = {}
        for sd in self.scales:
            questions = sorted(sd["questions"])
            bounds = {}
            levels = sorted(sd["levels"], key=lambda x: x['boundary'])
            for i, lvl in enumerate(levels):
                if i == 0:
                    bounds[f"{level_order[i]}_max"] = lvl['boundary']
                else:
                    bounds[f"{level_order[i]}_min"] = levels[i-1]['boundary'] + 1
                    bounds[f"{level_order[i]}_max"] = lvl['boundary']
            scales_config[sd["name"]] = {"title_ru": sd["name"], "qnums": questions, "bounds": bounds}

        answer_weights = {}
        a_count = self.answers_spin.value()
        q_count = self.questions_spin.value()
        if hasattr(self, '_weights_unified') and self._weights_unified:
            if hasattr(self, 'weight_spins') and self.weight_spins:
                for i, spin in enumerate(self.weight_spins[0]):
                    answer_weights[i+1] = spin.value()
            else:
                for i in range(1, a_count+1): answer_weights[i] = i
        else:
            if hasattr(self, 'weight_spins') and self.weight_spins and isinstance(self.weight_spins[0], list):
                for q_idx, row_spins in enumerate(self.weight_spins):
                    for a_idx, spin in enumerate(row_spins):
                        answer_weights[q_idx*a_count + a_idx + 1] = spin.value()
            else:
                for q in range(q_count):
                    for a in range(1, a_count+1):
                        answer_weights[q*a_count + a] = a

        if not self.shared_checkbox.isChecked():
            all_q = {}
            for sd in self.scales:
                for q in sd["questions"]:
                    if q not in all_q: all_q[q] = []
                    all_q[q].append(sd["name"])
            dup = {q: names for q, names in all_q.items() if len(names) > 1}
            if dup:
                msg = "Вопросы не должны повторяться между шкалами!\nПовторяющиеся вопросы:\n"
                for q, names in sorted(dup.items()):
                    msg += f"Вопрос {q}: {', '.join(names)}\n"
                self._show_error_message("Ошибка валидации", msg)
                self.switch_settings_tab(2)
                return

        full_config = {
            "test_name": self.test_name_edit.text().strip(),
            "test_description": self.test_description_edit.toPlainText().strip(),
            "questions_count": self.questions_spin.value(),
            "answers_count": self.answers_spin.value(),
            "shared_questions": self.shared_checkbox.isChecked(),
            "levels": {key: level_ru[key] for key in level_order},
            "level_boundaries": {key: lvl['boundary'] for key, lvl in zip(level_order, self.levels_data)},
            "level_order": level_order,
            "scales": scales_config,
            "answer_weights": answer_weights,
            "weights_unified": hasattr(self, '_weights_unified') and self._weights_unified,
        }
        self.current_config = full_config
        test_name = self.test_name_edit.text().strip()
        if self.output_folder_path and test_name:
            self.folder_manager.ensure_folder_exists(test_name, self.output_folder_path)
        self.config_saved.emit(full_config, self.current_profile_name or "")

    def open_profile_dialog(self):
        self.current_config = self._get_current_config()
        dlg = ProfileDialog(self, self.current_config)
        dlg.profile_loaded.connect(self.on_profile_loaded)
        dlg.profile_saved_with_name.connect(self.on_profile_saved)
        dlg.exec()

    def on_profile_saved(self, profile_name):
        self.current_profile_name = profile_name

    def _get_current_config(self):
        scales = {}
        for sd in self.scales:
            name = sd["name"]
            if name:
                scales[name] = {"title_ru": name, "qnums": sorted(sd["questions"]), "bounds": {}}
                levels = sorted(sd["levels"], key=lambda x: x['boundary'])
                for i, lvl in enumerate(levels):
                    if i == 0: scales[name]["bounds"][f"{self.level_order[i]}_max"] = lvl['boundary']
                    else:
                        scales[name]["bounds"][f"{self.level_order[i]}_min"] = levels[i-1]['boundary'] + 1
                        scales[name]["bounds"][f"{self.level_order[i]}_max"] = lvl['boundary']
        levels_dict = {}
        boundaries = {}
        for i, lvl in enumerate(self.levels_data):
            key = self.level_order[i] if i < len(self.level_order) else f"level{i+1}"
            levels_dict[key] = lvl['name']
            boundaries[key] = lvl['boundary']
        answer_weights = {}
        a_count = self.answers_spin.value()
        if hasattr(self, '_weights_unified') and self._weights_unified:
            if hasattr(self, 'weight_spins') and self.weight_spins:
                for i, spin in enumerate(self.weight_spins[0]): answer_weights[i+1] = spin.value()
            else:
                for i in range(1, a_count+1): answer_weights[i] = i
        else:
            if hasattr(self, 'weight_spins') and self.weight_spins and isinstance(self.weight_spins[0], list):
                for q_idx, row_spins in enumerate(self.weight_spins):
                    for a_idx, spin in enumerate(row_spins):
                        answer_weights[q_idx*a_count + a_idx + 1] = spin.value()
            else:
                for a in range(1, a_count+1): answer_weights[a] = a
        return {
            "test_name": self.test_name_edit.text().strip(),
            "test_description": self.test_description_edit.toPlainText().strip(),
            "scales": scales,
            "levels": levels_dict,
            "level_boundaries": boundaries,
            "level_order": self.level_order,
            "answer_weights": answer_weights,
            "questions_count": self.questions_spin.value(),
            "answers_count": self.answers_spin.value(),
            "shared_questions": self.shared_checkbox.isChecked(),
            "weights_unified": hasattr(self, '_weights_unified') and self._weights_unified,
        }

    def on_profile_loaded(self, config):
        self.current_profile_name = None
        if "questions_count" in config: self.questions_spin.setValue(config["questions_count"])
        if "answers_count" in config: self.answers_spin.setValue(config["answers_count"])
        if "shared_questions" in config: self.shared_checkbox.setChecked(config["shared_questions"])
        if "test_name" in config: self.test_name_edit.setText(config["test_name"])
        if "test_description" in config: self.test_description_edit.setPlainText(config["test_description"])
        self._update_folder_display()
        self.levels_data = []
        if "levels" in config:
            boundaries = config.get("level_boundaries", {})
            for key, name in config["levels"].items():
                b = boundaries.get(key, 0)
                if b > 0: self.levels_data.append({'name': name, 'boundary': b})
        self._refresh_levels_display()
        self.scales = []
        if "scales" in config:
            for name, sc in config["scales"].items():
                questions = sc.get("qnums", [])
                levels = []
                bounds = sc.get("bounds", {})
                order = config.get("level_order", [])
                for i, key in enumerate(order):
                    max_key = f"{key}_max"
                    if max_key in bounds:
                        boundary = bounds[max_key]
                        for lvl in self.levels_data:
                            if lvl['boundary'] == boundary:
                                start = (levels[-1]['boundary'] + 1) if levels else 1
                                levels.append({'name': lvl['name'], 'boundary': boundary, 'range_start': start, 'range_end': boundary})
                                break
                if not levels:
                    prev = 0
                    for lvl in self.levels_data:
                        start = prev + 1
                        end = lvl['boundary']
                        levels.append({'name': lvl['name'], 'boundary': lvl['boundary'], 'range_start': start, 'range_end': end})
                        prev = lvl['boundary']
                self.scales.append({"name": name, "questions": questions, "levels": levels})
        self._refresh_scales_list()
        if "answer_weights" in config:
            weights = config["answer_weights"]
            unified = config.get("weights_unified", False)
            self._weights_unified = unified
            self._refresh_weights_tab()
            if unified and weights:
                if hasattr(self, 'weight_spins') and self.weight_spins:
                    for i, spin in enumerate(self.weight_spins[0]):
                        spin.setValue(weights.get(str(i+1), i+1))
            elif weights:
                w_spins = getattr(self, 'weight_spins', [])
                if isinstance(w_spins, list) and len(w_spins) > 0 and isinstance(w_spins[0], list):
                    for q_idx, row_spins in enumerate(w_spins):
                        for a_idx, spin in enumerate(row_spins):
                            key = q_idx*len(row_spins) + a_idx + 1
                            if key in weights: spin.setValue(weights[key])
        self.current_config = config
        if self.current_profile_name:
            self.profile_loaded_with_name.emit(self.current_profile_name, config)
        self._show_success_message("Успех", "Профиль загружен!")

    def _load_config(self, config):
        if "questions_count" in config: self.questions_spin.setValue(config["questions_count"])
        if "answers_count" in config: self.answers_spin.setValue(config["answers_count"])
        if "shared_questions" in config: self.shared_checkbox.setChecked(config["shared_questions"])
        if "test_name" in config: self.test_name_edit.setText(config["test_name"])
        if "test_description" in config: self.test_description_edit.setPlainText(config["test_description"])
        self._update_folder_display()
        self.levels_data = []
        if "levels" in config:
            boundaries = config.get("level_boundaries", {})
            for key, name in config["levels"].items():
                b = boundaries.get(key, 0)
                if b > 0: self.levels_data.append({'name': name, 'boundary': b})
        self._refresh_levels_display()
        self.scales = []
        if "scales" in config:
            for name, sc in config["scales"].items():
                questions = sc.get("qnums", [])
                levels = []
                bounds = sc.get("bounds", {})
                order = config.get("level_order", [])
                for i, key in enumerate(order):
                    max_key = f"{key}_max"
                    if max_key in bounds:
                        boundary = bounds[max_key]
                        for lvl in self.levels_data:
                            if lvl['boundary'] == boundary:
                                start = (levels[-1]['boundary'] + 1) if levels else 1
                                levels.append({'name': lvl['name'], 'boundary': boundary, 'range_start': start, 'range_end': boundary})
                                break
                if not levels:
                    prev = 0
                    for lvl in self.levels_data:
                        start = prev + 1
                        end = lvl['boundary']
                        levels.append({'name': lvl['name'], 'boundary': lvl['boundary'], 'range_start': start, 'range_end': end})
                        prev = lvl['boundary']
                self.scales.append({"name": name, "questions": questions, "levels": levels})
        self._refresh_scales_list()
        if "answer_weights" in config:
            weights = config["answer_weights"]
            unified = config.get("weights_unified", False)
            self._weights_unified = unified
            self._refresh_weights_tab()
            if unified and weights and hasattr(self, 'weight_spins') and self.weight_spins:
                for i, spin in enumerate(self.weight_spins[0]): spin.setValue(weights.get(str(i+1), i+1))
            elif weights:
                w_spins = getattr(self, 'weight_spins', [])
                if isinstance(w_spins, list) and len(w_spins) > 0 and isinstance(w_spins[0], list):
                    for q_idx, row_spins in enumerate(w_spins):
                        for a_idx, spin in enumerate(row_spins):
                            key = q_idx*len(row_spins) + a_idx + 1
                            if key in weights: spin.setValue(weights[key])

    # ========== Уровни и шкалы ==========
    def _refresh_levels_display(self):
        self.levels_data.sort(key=lambda x: x['boundary'])
        while self.levels_layout.count():
            item = self.levels_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        prev_boundary = 0
        for i, level in enumerate(self.levels_data):
            boundary = level['boundary']
            start = prev_boundary + 1
            end = boundary
            display_data = {'name': level['name'], 'boundary': boundary, 'range_start': start, 'range_end': end}
            badge = LevelBadge(display_data, i, len(self.levels_data))
            badge.edited.connect(lambda lvl=level, idx=i: self._edit_level(lvl, idx))
            badge.deleted.connect(lambda lvl=level: self._delete_level(lvl))
            self.levels_layout.addWidget(badge)
            prev_boundary = boundary
        self._sync_levels_with_old_format()
        self._refresh_scales_list()

    def _sync_levels_with_old_format(self):
        self.levels = []
        self.level_order = []
        for i, lvl in enumerate(self.levels_data):
            if i == 0: key = "low"
            elif i == 1: key = "mid_low"
            elif i == 2: key = "mid_high"
            elif i == 3: key = "high"
            else: key = f"level{i+1}"
            self.level_order.append(key)

    def _add_level_from_form(self):
        name = self.level_name_edit.text().strip()
        boundary = self.level_boundary_spin.value()
        if not name:
            self._show_error_message("Ошибка", "Введите название уровня.")
            return
        for i, lvl in enumerate(self.levels_data):
            if lvl['boundary'] == boundary:
                self.levels_data[i]['name'] = name
                self._refresh_levels_display()
                self.level_name_edit.clear()
                return
        self.levels_data.append({'name': name, 'boundary': boundary})
        self._refresh_levels_display()
        self.level_name_edit.clear()

    def _edit_level(self, level, index):
        dlg = EditLevelDialog(level['name'], level['boundary'], self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_name, new_boundary = dlg.get_data()
            if new_name and new_boundary > 0:
                level['name'] = new_name
                level['boundary'] = new_boundary
                self.levels_data.sort(key=lambda x: x['boundary'])
                self._refresh_levels_display()

    def _delete_level(self, level):
        if len(self.levels_data) <= 1:
            self._show_error_message("Ошибка", "Должен быть хотя бы один уровень")
            return
        self.levels_data.remove(level)
        self._refresh_levels_display()

    def _refresh_scales_list(self):
        if not hasattr(self, 'scales_layout'): return
        while self.scales_layout.count():
            item = self.scales_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for sd in self.scales:
            item = ScaleItem(sd)
            item.edit_clicked.connect(self._edit_scale)
            item.delete_clicked.connect(self._delete_scale)
            self.scales_layout.addWidget(item)
        self.scales_layout.addStretch()

    def _add_scale_from_form(self):
        dlg = AddScaleDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if data is None: return
            new_scale = {"name": data["name"], "questions": data["questions"], "levels": data["levels"]}
            self.scales.append(new_scale)
            self._refresh_scales_list()

    def _edit_scale(self, scale_data):
        index = self.scales.index(scale_data)
        dlg = AddScaleDialog(self, scale_data=scale_data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_data = dlg.get_data()
            if new_data is None: return
            self.scales[index] = new_data
            self._refresh_scales_list()

    def _delete_scale(self, scale_data):
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить шкалу '{scale_data['name']}'?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.scales.remove(scale_data)
            self._refresh_scales_list()

    # ========== Вспомогательные ==========
    def _show_error_message(self, title, message):
        self._show_message_box(title, message, "error")

    def _show_success_message(self, title, message):
        self._show_message_box(title, message, "success")

    def _show_message_box(self, title, message, msg_type="error"):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; border-radius: 12px; }
            QMessageBox QLabel { color: #000000; font-size: 14px; }
            QPushButton { background-color: #3390EC; color: white; border: none; border-radius: 8px; padding: 8px 16px; font-size: 14px; font-weight: 500; }
            QPushButton:hover { background-color: #2B80D9; }
        """)
        icon_label = QLabel()
        if msg_type == "success":
            pixmap = QPixmap("resources/icons/attention-circle.svg")
        else:
            pixmap = QPixmap("resources/icons/alert-triangle.svg")
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            icon_label.setPixmap(self.style().standardIcon(QMessageBox.Icon.Warning).pixmap(48, 48))
        layout = msg_box.layout()
        layout.addWidget(icon_label, 0, 0, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        msg_box.exec()

    def select_folder(self):
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Выберите место для сохранения", self.output_folder_path or "")
        if folder:
            self.output_folder_path = folder
            self.folder_manager.set_base_folder(folder)
            self._save_folder_settings()
            self._update_folder_display()

    def _load_folder_settings(self):
        from PyQt6.QtCore import QSettings
        self.output_folder_path = QSettings("Psychoanalyst", "Settings").value("output_folder_path", "", str)

    def _save_folder_settings(self):
        from PyQt6.QtCore import QSettings
        QSettings("Psychoanalyst", "Settings").setValue("output_folder_path", self.output_folder_path)

    def _update_folder_display(self):
        if not hasattr(self, 'folder_path_label'): return
        if not self.output_folder_path:
            self.folder_path_label.setText("")
            return
        test_name = self.test_name_edit.text().strip() or f"Психологический тест {__import__('datetime').datetime.now().strftime('%d-%m-%Y')}"
        self.folder_manager.ensure_folder_exists(test_name, self.output_folder_path)
        full_path = Path(self.output_folder_path) / test_name
        self.folder_path_label.setText(f"📁 {full_path}")

    def _save_debug_config(self, scales_config, level_order, level_ru, answer_weights):
        import json
        from datetime import datetime
        debug = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scales_config": scales_config,
            "level_order": level_order,
            "level_ru": level_ru,
            "answer_weights": answer_weights
        }
        with open("debug_config.json", "w", encoding="utf-8") as f:
            json.dump(debug, f, indent=2, ensure_ascii=False)

    def set_config(self, config):
        self.config = config