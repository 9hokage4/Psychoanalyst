# ui/components/settings_dialog.py
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QGroupBox, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QCheckBox, QScrollArea, QWidget,
    QLineEdit, QMessageBox, QTabWidget, QFrame, QSizePolicy
)
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from pathlib import Path
from utils.profile_manager import ProfileManager
from ui.components.profile_dialog import ProfileDialog
from PyQt6.QtCore import Qt, QPropertyAnimation, QRectF, QPointF, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtWidgets import QAbstractButton, QSizePolicy, QLayout
from PyQt6.QtSvg import QSvgRenderer
from utils.fonts import get_font, FontWeights


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
                background-color: white;
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
                 icon_size=24, font_size=14, spacing=10, parent=None):
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
    edited = pyqtSignal()
    deleted = pyqtSignal()
    
    def __init__(self, level_data, index, total, parent=None, hide_delete=False):
        super().__init__(parent)
        self.level_data = level_data
        self.index = index
        self.total = total
        self.hide_delete = hide_delete

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 8, 6)
        layout.setSpacing(8)

        text = f"{level_data['name']} ({level_data['range_start']}-{level_data['range_end']} баллов)"
        self.label = QLabel(text)
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
            self.delete_btn.clicked.connect(self.deleted.emit)
        layout.addWidget(self.delete_btn)
        if hide_delete:
            self.delete_btn.setVisible(False)

        # Telegram-цвета (замена зелёного на голубой)
        self.bg_color = QColor(180, 209, 238)   # #b4d1ee
        self.text_color = QColor(6, 120, 234)   # #0678ea

        self.label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 13px;
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
        painter.drawRoundedRect(self.rect(), 20, 20)
        super().paintEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonDblClick and obj is self:
            self.edited.emit()
            return True
        return super().eventFilter(obj, event)

    def update_level_data(self, level_data):
        self.level_data = level_data
        text = f"{level_data['name']} ({level_data['range_start']}-{level_data['range_end']} баллов)"
        self.label.setText(text)
        self.update()


class ScaleItem(QWidget):
    edit_clicked = pyqtSignal(object)
    delete_clicked = pyqtSignal(object)
    
    def sizeHint(self):
        return QSize(200, 100)

    def __init__(self, scale_data, parent=None):
        super().__init__(parent)
        self.scale_data = scale_data
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        self.setMinimumHeight(100)  # временно, чтобы убедиться, что виджет имеет размер

        # Ручная отрисовка фона и рамки
        self.setAutoFillBackground(False)  # отключаем автоматический фон

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)  # увеличенные отступы
        layout.setSpacing(10)

        # Верхняя панель: название + количество вопросов справа
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(6)

        self.title_label = QLabel(scale_data["name"])
        self.title_label.setFont(get_font("item_title"))
        self.title_label.setStyleSheet("""
    color: #000000;
    border: 2px solid #000000;
    border-radius: 8px;
    padding: 4px 8px;
    background-color: #FFFFFF;
""")
        top_layout.addWidget(self.title_label)

        # Количество вопросов
        q_count = len(scale_data.get("questions", []))
        self.count_label = QLabel(f"Количество вопросов: {q_count}")
        self.count_label.setFont(get_font("caption"))
        self.count_label.setStyleSheet("color: #58616a; border: none; margin: 0; padding: 0;")
        top_layout.addWidget(self.count_label)
        
        top_layout.addStretch()

        # Иконки справа
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon("resources/icons/edit.svg"))
        self.edit_btn.setIconSize(QSize(24, 24))
        self.edit_btn.setFixedSize(28, 28)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.05);
                border-radius: 14px;
            }
        """)
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.scale_data))
        top_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon("resources/icons/trash.svg"))
        self.delete_btn.setIconSize(QSize(24, 24))
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.05);
                border-radius: 14px;
            }
        """)
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.scale_data))
        top_layout.addWidget(self.delete_btn)

        layout.addLayout(top_layout)

        # Линия под шапкой
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #000000; max-height: 1px; margin: 4px 0 8px 0;")
        layout.addWidget(line)

        # Уровни
        levels_title = QLabel("Уровни:")
        levels_title.setFont(get_font("caption"))
        levels_title.setStyleSheet("color: #000000; font-weight: 500; margin-bottom: 4px; border: none;")
        layout.addWidget(levels_title)

        # Контейнер для уровней (горизонтальный flow layout)
        self.levels_container = QWidget()
        self.levels_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.levels_layout = QFlowLayout(self.levels_container)
        self.levels_layout.setContentsMargins(0, 0, 0, 0)
        self.levels_layout.setSpacing(8)
        layout.addWidget(self.levels_container)

        # Вопросы для шкалы
        questions_title = QLabel("Вопросы для шкалы:")
        questions_title.setFont(get_font("caption"))
        questions_title.setStyleSheet("color: #000000; font-weight: 500; margin: 8px 0 4px 0; border: none;")
        layout.addWidget(questions_title)

        # Контейнер для строк вопросов (вертикальный layout)
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
        # Белый фон
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.drawRoundedRect(self.rect(), 8, 8)
        super().paintEvent(event)

    def _format_questions_groups(self, questions):
        """Формирует список строк с диапазонами для отображения."""
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
        """Разбивает список элементов на строки по max_per_line штук."""
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
            label.setStyleSheet("border: 2px solid #000000; border-radius: 8px; padding: 6px 12px; background-color: #FFFFFF;")
            label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self.questions_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
            return

        lines = self._split_into_lines(groups, max_per_line=5)
        for line in lines:
            label = QLabel(line)
            label.setFont(get_font("table_cell"))
            label.setStyleSheet("border: 2px solid #000000; border-radius: 8px; padding: 6px 12px; background-color: #FFFFFF;")
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
            badge.setCursor(Qt.CursorShape.ArrowCursor)   # убираем руку, если не нужно
            self.levels_layout.addWidget(badge)
        self.levels_layout.activate()

    def update_data(self, scale_data):
        self.scale_data = scale_data
        self.title_label.setText(scale_data["name"])
        q_count = len(scale_data.get("questions", []))
        self.count_label.setText(f"Количество вопросов: {q_count}")
        self._update_levels_display()
        self._update_questions_display()


class AddScaleDialog(QDialog):
    """Диалог добавления/редактирования шкалы."""
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
        name_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #707579;")
        self.name_edit = QLineEdit(self.scale_data.get("name", ""))
        self.name_edit.setPlaceholderText("например, 'Тревожность'")
        self.name_edit.setFixedHeight(36)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 14px;
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
        questions_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #707579;")
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
        self.questions_edit.setFixedHeight(36)
        self.questions_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 14px;
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
        levels_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #707579; margin-top: 8px;")
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
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
        """)
        add_level_btn.clicked.connect(self._on_add_level)
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
        self.save_btn.clicked.connect(self.accept)

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
        parent = self.parent()
        if hasattr(parent, 'levels_data'):
            global_levels = parent.levels_data
            if self.scale_data and "levels" in self.scale_data:
                self.selected_levels = self.scale_data["levels"].copy()
            else:
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

        for idx, lvl in enumerate(self.selected_levels):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            label = QLabel(f"{lvl['name']} ({lvl['range_start']}-{lvl['range_end']} баллов)")
            label.setStyleSheet("color: #000000; font-size: 13px;")
            row_layout.addWidget(label, 1)

            del_btn = QPushButton()
            del_btn.setIcon(QIcon("resources/icons/close.svg"))
            del_btn.setIconSize(QSize(16, 16))
            del_btn.setFixedSize(24, 24)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background: rgba(0,0,0,0.05);
                    border-radius: 12px;
                }
            """)
            del_btn.clicked.connect(lambda checked, i=idx: self._remove_level(i))
            row_layout.addWidget(del_btn)

            self.levels_layout.addWidget(row)

    def _remove_level(self, index):
        self.selected_levels.pop(index)
        self._refresh_levels_display()

    def _on_add_level(self):
        parent = self.parent()
        if not hasattr(parent, 'levels_data'):
            return

        available = []
        for lvl in parent.levels_data:
            if not any(sl['name'] == lvl['name'] and sl['boundary'] == lvl['boundary'] for sl in self.selected_levels):
                available.append(lvl)

        if not available:
            QMessageBox.information(self, "Нет доступных уровней", "Все уровни уже добавлены.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите уровни")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)

        checkboxes = []
        for lvl in available:
            cb = QCheckBox(f"{lvl['name']} (до {lvl['boundary']} баллов)")
            cb.setStyleSheet("margin: 4px;")
            layout.addWidget(cb)
            checkboxes.append((cb, lvl))

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Добавить")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
        """)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #3390EC;
                border: 1px solid #3390EC;
                border-radius: 8px;
                padding: 8px 16px;
            }
        """)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def add_selected():
            for cb, lvl in checkboxes:
                if cb.isChecked():
                    prev = 0
                    for gl in parent.levels_data:
                        if gl['boundary'] == lvl['boundary']:
                            break
                        prev = gl['boundary']
                    start = prev + 1
                    new_lvl = lvl.copy()
                    new_lvl['range_start'] = start
                    new_lvl['range_end'] = lvl['boundary']
                    self.selected_levels.append(new_lvl)
            self.selected_levels.sort(key=lambda x: x['boundary'])
            self._refresh_levels_display()
            dialog.accept()

        ok_btn.clicked.connect(add_selected)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def get_data(self):
        name = self.name_edit.text().strip()
        questions_text = self.questions_edit.text().strip()
        questions = self._parse_questions(questions_text)
        levels = self.selected_levels
        return {"name": name, "questions": questions, "levels": levels}

    def _parse_questions(self, text):
        if not text:
            return []
        parts = text.split(',')
        questions = set()
        for part in parts:
            part = part.strip()
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if start > end:
                        continue
                    questions.update(range(start, end + 1))
                except ValueError:
                    continue
            else:
                try:
                    questions.add(int(part))
                except ValueError:
                    continue
        return sorted(questions)


class SettingsDialog(QDialog):
    config_saved = pyqtSignal(dict, list, dict, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Настройки теста")
        self.setWindowIcon(QIcon("resources/icons/cog.svg"))
        self.setMinimumSize(900, 350)
        self.setModal(True)
        self.scales = []
        self.levels = []
        self.level_order = []
        self.levels_data = []
        self.profile_manager = ProfileManager()
        self.current_config = None
        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QDialog { background-color: #F5F5F5; }")
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setIconSize(QSize(20, 20))
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #F5F5F5;
                top: -1px;
            }
            QTabBar::tab {
                background-color: transparent;
                color: #707579;
                border: none;
                border-bottom: 2px solid transparent;
                padding: 12px 24px;
                margin-right: 4px;
                font-size: 14px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                color: #3390EC;
                border-bottom: 2px solid #3390EC;
            }
            QTabBar::tab:hover:!selected {
                background-color: #F5F5F5;
                border-radius: 8px 8px 0 0;
            }
        """)
        
        self.basic_tab = self._create_basic_tab()
        self.scales_tab = self._create_scales_tab()
        self.levels_tab = self._create_levels_tab()
        self.weights_tab = self._create_weights_tab()
        
        self.tabs.addTab(self.basic_tab, QIcon("resources/icons/cog.svg"), "Основные")
        self.tabs.addTab(self.levels_tab, QIcon("resources/icons/chart-line.svg"), "Уровни")
        self.tabs.addTab(self.scales_tab, QIcon("resources/icons/charts.svg"), "Шкалы")
        self.tabs.addTab(self.weights_tab, QIcon("resources/icons/scale.svg"), "Веса")
        
        main_layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        btn_frame = QFrame()
        btn_frame.setObjectName("btn_frame")
        btn_frame.setStyleSheet("""
            QFrame#btn_frame {
                background-color: #FFFFFF;
                border-top: 1px solid #DFE1E5;
                padding: 20px 24px;
            }
        """)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)
        
        self.profile_btn = QPushButton("📁 Профили")
        self.profile_btn.setObjectName("btn_profile")
        self.profile_btn.setIcon(QIcon("resources/icons/folder.svg"))
        self.profile_btn.setFont(get_font("button"))
        self.profile_btn.setStyleSheet("""
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
        self.profile_btn.clicked.connect(self.open_profile_dialog)
        btn_layout.addWidget(self.profile_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("💾 Сохранить профиль")
        self.save_btn.setObjectName("btn_save")
        self.save_btn.setIcon(QIcon("resources/icons/save.svg"))
        self.save_btn.setFont(get_font("button"))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6BBF8A;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #5AA878;
            }
        """)
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("btn_cancel")
        self.cancel_btn.setIcon(QIcon("resources/icons/close.svg"))
        self.cancel_btn.setFont(get_font("button"))
        self.cancel_btn.setStyleSheet("""
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
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_frame.setLayout(btn_layout)
        main_layout.addWidget(btn_frame)
        
        self.setLayout(main_layout)
        
    def on_tab_changed(self, index):
        # Получаем название активной вкладки
        current_tab = self.tabs.widget(index)
        if current_tab == self.levels_tab:
            # Ограничиваем высоту окна, например, 600
            self.setMaximumHeight(480)
        else:
            # Сбрасываем ограничение (устанавливаем очень большое значение)
            self.setMaximumHeight(16777215)  # максимальное значение высоты в Qt
        self.adjustSize()

    def _create_basic_tab(self):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        name_group = QVBoxLayout()
        name_group.setSpacing(6)
        name_label = QLabel("Название теста")
        name_label.setFont(get_font("form_label"))
        name_label.setStyleSheet("color: #707579;")
        name_group.addWidget(name_label)

        self.test_name_edit = QLineEdit()
        self.test_name_edit.setPlaceholderText("Введите название")
        self.test_name_edit.setText("Опросник агрессивности")
        self.test_name_edit.setFixedHeight(40)
        self.test_name_edit.setFont(get_font("form_input"))
        self.test_name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: white;
                color: #000000;
            }
            QLineEdit:focus {
                border-color: #3390EC;
            }
        """)
        name_group.addWidget(self.test_name_edit)

        questions_group = QVBoxLayout()
        questions_group.setSpacing(6)
        questions_label = QLabel("Количество вопросов")
        questions_label.setFont(get_font("form_label"))
        questions_label.setStyleSheet("color: #707579;")
        questions_group.addWidget(questions_label)

        self.questions_spin = QSpinBox()
        self.questions_spin.setRange(1, 1000)
        self.questions_spin.setValue(10)
        self.questions_spin.setFixedHeight(40)
        self.questions_spin.setFont(get_font("numeric"))
        self.questions_spin.setObjectName("questions_spin")
        self.questions_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 24px 8px 12px;
                font-size: 14px;
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
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #F0F0F0;
                border-radius: 4px;
            }
        """)
        self.questions_spin.valueChanged.connect(self.on_questions_changed)
        questions_group.addWidget(self.questions_spin)
        
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(16)
        row1_layout.addLayout(name_group)
        row1_layout.addLayout(questions_group)
        main_layout.addLayout(row1_layout)
        
        answers_group = QVBoxLayout()
        answers_group.setSpacing(6)
        answers_label = QLabel("Количество вариантов ответов")
        answers_label.setFont(get_font("form_label"))
        answers_label.setStyleSheet("color: #707579;")
        answers_group.addWidget(answers_label)

        self.answers_spin = QSpinBox()
        self.answers_spin.setRange(2, 10)
        self.answers_spin.setValue(5)
        self.answers_spin.setFixedHeight(40)
        self.answers_spin.setFont(get_font("numeric"))
        self.answers_spin.setObjectName("answers_spin")
        self.answers_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 24px 8px 12px;
                font-size: 14px;
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
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #F0F0F0;
                border-radius: 4px;
            }
        """)
        self.answers_spin.valueChanged.connect(self.on_answers_changed)
        answers_group.addWidget(self.answers_spin)
        main_layout.addLayout(answers_group)
        
        desc_group = QVBoxLayout()
        desc_group.setSpacing(6)
        desc_label = QLabel("Описание теста")
        desc_label.setFont(get_font("form_label"))
        desc_label.setStyleSheet("color: #707579;")
        desc_group.addWidget(desc_label)

        self.test_description_edit = QTextEdit()
        self.test_description_edit.setPlaceholderText("Введите описание теста...")
        self.test_description_edit.setFixedHeight(100)
        self.test_description_edit.setFont(get_font("form_input"))
        self.test_description_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: white;
                color: #000000;
            }
            QTextEdit:focus {
                border-color: #3390EC;
            }
        """)
        desc_group.addWidget(self.test_description_edit)
        main_layout.addLayout(desc_group)

        checkbox_group = QVBoxLayout()
        checkbox_group.setSpacing(4)
        self.shared_checkbox = AnimatedCheckBox("Вопросы для различных шкал одинаковы")
        self.shared_checkbox.setChecked(False)
        checkbox_group.addWidget(self.shared_checkbox)

        hint_label = QLabel("Если активно — один вопрос может относиться к нескольким шкалам")
        hint_label.setFont(get_font("hint"))
        hint_label.setStyleSheet("color: #707579;")
        hint_label.setContentsMargins(32, 0, 0, 0)
        checkbox_group.addWidget(hint_label)

        main_layout.addLayout(checkbox_group)
        main_layout.addStretch()
        
        return tab

    def _create_levels_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        title_label = QLabel("Активные уровни")
        title_label.setStyleSheet("color: #000000; font-size: 14px; font-weight: 600; margin-bottom: 4px;")
        layout.addWidget(title_label)

        self.levels_container = QWidget()
        self.levels_container.setMinimumHeight(40)   # минимальная высота
        self.levels_layout = QFlowLayout(self.levels_container)
        self.levels_layout.setContentsMargins(6, 2, 6, 2)
        self.levels_layout.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.levels_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(150)                 # ограничиваем высоту
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #FFFFFF;
            }
            QScrollBar:vertical {
                background-color: #F0F0F0;
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
        """)
        layout.addWidget(scroll)

        # Форма настройки уровня
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(6)

        form_title = QLabel("Настройка уровня")
        form_title.setStyleSheet("""
            color: #000000;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 0px;
            border: none;
            background: transparent;
        """)
        form_title.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        form_layout.addWidget(form_title)

        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(10)

        self.level_name_edit = QLineEdit()
        self.level_name_edit.setPlaceholderText("Название уровня")
        self.level_name_edit.setFixedHeight(36)
        self.level_name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3390EC;
            }
        """)
        fields_layout.addWidget(self.level_name_edit, 1)

        self.level_boundary_spin = QSpinBox()
        self.level_boundary_spin.setRange(1, 10000)
        self.level_boundary_spin.setValue(10)
        self.level_boundary_spin.setFixedHeight(36)
        self.level_boundary_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 14px;
                background-color: white;
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
        fields_layout.addWidget(self.level_boundary_spin, 1)

        form_layout.addLayout(fields_layout)

        add_btn = QPushButton("+ Добавить уровень")
        add_btn.setFixedHeight(36)
        add_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        font_metrics = add_btn.fontMetrics()
        text_width = font_metrics.horizontalAdvance(add_btn.text())
        add_btn.setFixedWidth(text_width + 60)
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self._add_level_from_form)
        form_layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(form_frame)

        # Инициализация данных
        self.levels_data = [
            {'name': 'Низкий', 'boundary': 15},
            {'name': 'Средний', 'boundary': 30},
            {'name': 'Высокий', 'boundary': 45}
        ]
        self._refresh_levels_display()

        return tab

    def _sync_levels_with_old_format(self):
        self.levels = []
        self.level_order = []
        for i, lvl in enumerate(self.levels_data):
            if i == 0:
                key = "low"
            elif i == 1:
                key = "mid_low"
            elif i == 2:
                key = "mid_high"
            elif i == 3:
                key = "high"
            else:
                key = f"level{i+1}"
            self.level_order.append(key)
            self.levels.append({
                "key": key,
                "name_input": None,
                "boundary": lvl['boundary'],
                "boundary_label": None,
                "hint_label": None,
                "widget": None,
                "num_label": None
            })

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
        dialog = EditLevelDialog(level['name'], level['boundary'], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name, new_boundary = dialog.get_data()
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

    def _create_scales_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Верхняя панель
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Список шкал")
        title_label.setStyleSheet("color: #000000; font-size: 16px; font-weight: 600;")
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        add_btn = QPushButton("+ Добавить шкалу")
        add_btn.setFixedHeight(40)
        add_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        font_metrics = add_btn.fontMetrics()
        text_width = font_metrics.horizontalAdvance(add_btn.text())
        add_btn.setFixedWidth(text_width + 70)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
        """)
        add_btn.clicked.connect(self._add_scale_from_form)
        top_layout.addWidget(add_btn)

        layout.addLayout(top_layout)

        # Обёртка для скролла
        wrapper = QFrame()
        wrapper.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 2px solid #000000;
                border-radius: 12px;
            }
        """)
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)

        # Контейнер для списка шкал
        self.scales_container = QWidget()
        self.scales_container.setStyleSheet("background: transparent;")
        self.scales_layout = QVBoxLayout(self.scales_container)
        self.scales_layout.setContentsMargins(12, 12, 12, 12)
        self.scales_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.scales_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumHeight(200)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
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
        """)
        wrapper_layout.addWidget(scroll)

        layout.addWidget(wrapper, 1)

        self._refresh_scales_list()
        return tab

    def _refresh_scales_list(self):
        if not hasattr(self, 'scales_layout') or self.scales_layout is None:
            return
        while self.scales_layout.count():
            item = self.scales_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for scale_data in self.scales:
            item = ScaleItem(scale_data)
            item.edit_clicked.connect(self._edit_scale)
            item.delete_clicked.connect(self._delete_scale)
            self.scales_layout.addWidget(item)
        self.adjustSize()

    def _add_scale_from_form(self):
        dialog = AddScaleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Ошибка", "Название шкалы обязательно.")
                return
            if not data["questions"]:
                QMessageBox.warning(self, "Ошибка", "Укажите вопросы для шкалы.")
                return
            if not self.shared_checkbox.isChecked():
                all_questions = {}
                for scale in self.scales:
                    for q in scale.get("questions", []):
                        if q not in all_questions:
                            all_questions[q] = []
                        all_questions[q].append(scale["name"])
                duplicate = [q for q in data["questions"] if q in all_questions]
                if duplicate:
                    error = f"Вопросы {', '.join(map(str, duplicate))} уже используются в других шкалах.\n"
                    error += "Отметьте 'Вопросы для различных шкал одинаковы' на вкладке 'Основные', чтобы разрешить повтор."
                    QMessageBox.warning(self, "Ошибка", error)
                    return
            new_scale = {
                "name": data["name"],
                "questions": data["questions"],
                "levels": data["levels"]
            }
            self.scales.append(new_scale)
            self._refresh_scales_list()

    def _edit_scale(self, scale_data):
        index = self.scales.index(scale_data)
        dialog = AddScaleDialog(self, scale_data=scale_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if not new_data["name"]:
                QMessageBox.warning(self, "Ошибка", "Название шкалы обязательно.")
                return
            if not new_data["questions"]:
                QMessageBox.warning(self, "Ошибка", "Укажите вопросы для шкалы.")
                return
            if not self.shared_checkbox.isChecked():
                all_questions = {}
                for i, scale in enumerate(self.scales):
                    if i == index:
                        continue
                    for q in scale.get("questions", []):
                        if q not in all_questions:
                            all_questions[q] = []
                        all_questions[q].append(scale["name"])
                duplicate = [q for q in new_data["questions"] if q in all_questions]
                if duplicate:
                    error = f"Вопросы {', '.join(map(str, duplicate))} уже используются в других шкалах.\n"
                    error += "Отметьте 'Вопросы для различных шкал одинаковы' на вкладке 'Основные', чтобы разрешить повтор."
                    QMessageBox.warning(self, "Ошибка", error)
                    return
            self.scales[index] = new_data
            self._refresh_scales_list()

    def _delete_scale(self, scale_data):
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить шкалу '{scale_data['name']}'?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.scales.remove(scale_data)
            self._refresh_scales_list()

    def _create_weights_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Блок "Веса ответов для каждого вопроса"
        weights_group = QGroupBox("Веса ответов для каждого вопроса")
        weights_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                color: #212529;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #3390EC;
                font-size: 14px;
            }
        """)
        group_layout = QVBoxLayout(weights_group)
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(12)

        # Контейнер для строк весов (прокручиваемый, без фона)
        self.weights_container = QWidget()
        self.weights_container.setStyleSheet("background: transparent;")
        self.weights_layout = QVBoxLayout(self.weights_container)
        self.weights_layout.setContentsMargins(0, 0, 0, 0)
        self.weights_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.weights_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background-color: #F0F0F0;
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
        """)
        group_layout.addWidget(scroll)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.apply_all_btn = QPushButton("Применить ко всем вопросам")
        self.apply_all_btn.setFixedHeight(32)
        self.apply_all_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        font_metrics = self.apply_all_btn.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self.apply_all_btn.text())
        self.apply_all_btn.setFixedWidth(text_width + 40)
        self.apply_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #3390EC;
                border: 1px solid #3390EC;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
            QPushButton:disabled {
                background-color: #F5F5F5;
                color: #ADB5BD;
                border-color: #ADB5BD;
            }
        """)
        self.apply_all_btn.clicked.connect(self._apply_weights_to_all)
        btn_layout.addWidget(self.apply_all_btn)

        self.cancel_unify_btn = QPushButton("Отмена")
        self.cancel_unify_btn.setFixedHeight(32)
        self.cancel_unify_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        text_width = font_metrics.horizontalAdvance(self.cancel_unify_btn.text())
        self.cancel_unify_btn.setFixedWidth(text_width + 40)
        self.cancel_unify_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #3390EC;
                border: 1px solid #3390EC;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        self.cancel_unify_btn.clicked.connect(self._cancel_unify_weights)
        self.cancel_unify_btn.setVisible(False)  # изначально скрыта
        btn_layout.addWidget(self.cancel_unify_btn)

        group_layout.addLayout(btn_layout)

        layout.addWidget(weights_group)

        # Инициализируем вкладку
        self._refresh_weights_tab()

        return tab

    def _refresh_weights_tab(self):
        """Обновляет отображение весов (создаёт строки для всех вопросов или одну строку)"""
        if hasattr(self, '_weights_unified') and self._weights_unified:
            return

        q_count = self.questions_spin.value()
        a_count = self.answers_spin.value()

        while self.weights_layout.count():
            item = self.weights_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.weight_spins = []  # список списков спинбоксов
        for i in range(1, q_count + 1):
            row, spins = self._create_question_row(i, a_count)
            self.weights_layout.addWidget(row)
            self.weight_spins.append(spins)

        self.apply_all_btn.setEnabled(True)
        self.cancel_unify_btn.setVisible(False)

    def _create_question_row(self, question_num, answer_count):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        label = QLabel(f"Вопрос {question_num}")
        label.setStyleSheet("font-size: 14px; font-weight: 500; color: #000000; min-width: 80px; margin-left: 8px;")
        row_layout.addWidget(label)

        spins = []
        for j in range(1, answer_count + 1):
            spin = QSpinBox()
            spin.setRange(1, 100)
            spin.setValue(j)
            spin.setFixedHeight(32)
            spin.setStyleSheet("""
                QSpinBox {
                    border: 1px solid #DFE1E5;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 14px;
                    background-color: white;
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
            row_layout.addWidget(spin)
            spins.append(spin)

        row_layout.addStretch()
        return row_widget, spins

    def _create_unified_weights_row(self, question_count, answer_count):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        label = QLabel("Вопрос")
        label.setStyleSheet("font-size: 14px; font-weight: 500; color: #000000; min-width: 80px; margin-left: 8px;")
        row_layout.addWidget(label)

        spins = []
        for j in range(1, answer_count + 1):
            spin = QSpinBox()
            spin.setRange(1, 100)
            spin.setValue(j)
            spin.setFixedHeight(32)
            spin.setStyleSheet("""
                QSpinBox {
                    border: 1px solid #DFE1E5;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 14px;
                    background-color: white;
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
            row_layout.addWidget(spin)
            spins.append(spin)

        row_layout.addStretch()
        self.weight_spins = spins
        self.weights_layout.addWidget(row_widget)

    def _apply_weights_to_all(self):
        if self.weights_layout.count() <= 1:
            return

        # Получаем значения из первой строки
        first_row = self.weights_layout.itemAt(0).widget()
        first_row_spins = []
        for child in first_row.findChildren(QSpinBox):
            first_row_spins.append(child.value())

        # Удаляем все строки, кроме первой
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
        self.weight_spins = first_row_spins

    def _cancel_unify_weights(self):
        """Отменяет режим единых весов, возвращает исходное состояние"""
        self._weights_unified = False
        if hasattr(self, '_weights_unified'):
            del self._weights_unified
        self._refresh_weights_tab()

    def on_questions_changed(self, value):
        if hasattr(self, 'weights_layout'):
            self._refresh_weights_tab()

    # В методе on_answers_changed
    def on_answers_changed(self, value):
        if hasattr(self, 'weights_layout'):
            self._refresh_weights_tab()

    def save_config(self):
        if self.questions_spin.value() < 1:
            self._show_error_message("Ошибка", "Количество вопросов должно быть больше 0")
            self.tabs.setCurrentIndex(0)
            return
        if self.answers_spin.value() < 2:
            self._show_error_message("Ошибка", "Количество ответов должно быть минимум 2")
            self.tabs.setCurrentIndex(0)
            return
        if len(self.levels_data) < 1:
            self._show_error_message("Ошибка", "Добавьте хотя бы один уровень показателей")
            self.tabs.setCurrentIndex(1)
            return
        for i, level_data in enumerate(self.levels_data):
            name = level_data['name'].strip()
            if not name:
                self._show_error_message("Ошибка", f"Уровень {i + 1} не имеет названия")
                self.tabs.setCurrentIndex(1)
                return
        if len(self.scales) < 1:
            self._show_error_message("Ошибка", "Добавьте хотя бы одну шкалу")
            self.tabs.setCurrentIndex(2)
            return

        level_order = []
        level_ru = {}
        for i, lvl in enumerate(self.levels_data):
            if i == 0:
                key = "low"
            elif i == 1:
                key = "mid_low"
            elif i == 2:
                key = "mid_high"
            elif i == 3:
                key = "high"
            else:
                key = f"level{i+1}"
            level_order.append(key)
            level_ru[key] = lvl['name']

        scales_config = {}
        for scale_data in self.scales:
            scale_name = scale_data["name"]
            questions = sorted(scale_data["questions"])
            bounds = {}
            levels = sorted(scale_data["levels"], key=lambda x: x['boundary'])
            for i, lvl in enumerate(levels):
                if i == 0:
                    bounds[f"{level_order[i]}_max"] = lvl['boundary']
                else:
                    bounds[f"{level_order[i]}_min"] = levels[i-1]['boundary'] + 1
                    bounds[f"{level_order[i]}_max"] = lvl['boundary']
            scales_config[scale_name] = {
                "title_ru": scale_name,
                "qnums": questions,
                "bounds": bounds
            }

        # === Веса ответов ===
        answer_weights = {}
        a_count = self.answers_spin.value()
        q_count = self.questions_spin.value()

        # Проверяем, установлен ли режим единых весов (нажата кнопка «Применить»)
        if hasattr(self, '_weights_unified') and self._weights_unified:
            # Единые веса для всех вопросов
            if hasattr(self, 'weight_spins') and self.weight_spins:
                # self.weight_spins — список значений для ответов (длина = a_count)
                for i, val in enumerate(self.weight_spins):
                    answer_weights[i+1] = val
            else:
                # Если self.weight_spins не существует, используем значения по умолчанию
                for i in range(1, a_count + 1):
                    answer_weights[i] = i
        else:
            # Разные веса для каждого вопроса
            if hasattr(self, 'weight_spins') and self.weight_spins and isinstance(self.weight_spins[0], list):
                # self.weight_spins — список списков спинбоксов (по вопросам)
                for q_idx, row_spins in enumerate(self.weight_spins):
                    for a_idx, spin in enumerate(row_spins):
                        answer_weights[q_idx * a_count + a_idx + 1] = spin.value()
            else:
                # Если вкладка не была открыта или структура не та, используем значения по умолчанию
                for q in range(q_count):
                    for a in range(1, a_count + 1):
                        answer_weights[q * a_count + a] = a

        # === Проверка повторяющихся вопросов ===
        if not self.shared_checkbox.isChecked():
            all_questions = {}
            for scale_data in self.scales:
                scale_name = scale_data["name"]
                for q in scale_data["questions"]:
                    if q not in all_questions:
                        all_questions[q] = []
                    all_questions[q].append(scale_name)
            duplicate = {q: names for q, names in all_questions.items() if len(names) > 1}
            if duplicate:
                error_messages = []
                for q, names in sorted(duplicate.items()):
                    error_messages.append(f"Вопрос {q}: {', '.join(names)}")
                error_text = (
                    "Вопросы не должны повторяться между шкалами!\n\n"
                    "Повторяющиеся вопросы:\n" + "\n".join(error_messages)
                )
                self._show_error_message("Ошибка валидации", error_text)
                self.tabs.setCurrentIndex(2)
                return

        self._save_debug_config(scales_config, level_order, level_ru, answer_weights)
        self.config_saved.emit(scales_config, level_order, level_ru, answer_weights)
        self.accept()

    def open_profile_dialog(self):
        self.current_config = self._get_current_config()
        dialog = ProfileDialog(self, self.current_config)
        dialog.profile_loaded.connect(self.on_profile_loaded)
        dialog.exec()

    def _get_current_config(self):
        scales = {}
        for scale_data in self.scales:
            name = scale_data["name"]
            if name:
                scales[name] = {
                    "title_ru": name,
                    "qnums": sorted(scale_data["questions"]),
                    "bounds": {}
                }
                levels = sorted(scale_data["levels"], key=lambda x: x['boundary'])
                for i, lvl in enumerate(levels):
                    if i == 0:
                        scales[name]["bounds"][f"{self.level_order[i]}_max"] = lvl['boundary']
                    else:
                        scales[name]["bounds"][f"{self.level_order[i]}_min"] = levels[i-1]['boundary'] + 1
                        scales[name]["bounds"][f"{self.level_order[i]}_max"] = lvl['boundary']

        levels = {}
        level_boundaries = {}
        for i, lvl in enumerate(self.levels_data):
            key = self.level_order[i] if i < len(self.level_order) else f"level{i+1}"
            levels[key] = lvl['name']
            level_boundaries[key] = lvl['boundary']

        answer_weights = {}
        if hasattr(self, 'same_weights_checkbox'):
            if self.same_weights_checkbox.isChecked():
                weight = getattr(self, 'single_weight_spin', None)
                if weight:
                    for i in range(1, self.answers_spin.value() + 1):
                        answer_weights[i] = weight.value()
            else:
                for i, spin in getattr(self, 'weight_spins', {}).items():
                    answer_weights[i] = spin.value()

        return {
            "scales": scales,
            "levels": levels,
            "level_boundaries": level_boundaries,
            "level_order": self.level_order,
            "answer_weights": answer_weights,
            "questions_count": self.questions_spin.value(),
            "answers_count": self.answers_spin.value(),
            "shared_questions": self.shared_checkbox.isChecked(),
        }

    def on_profile_loaded(self, config):
        if "questions_count" in config:
            self.questions_spin.setValue(config["questions_count"])
        if "answers_count" in config:
            self.answers_spin.setValue(config["answers_count"])
        if "shared_questions" in config:
            self.shared_checkbox.setChecked(config["shared_questions"])

        self.levels_data = []
        if "levels" in config:
            level_boundaries = config.get("level_boundaries", {})
            for key, name in config["levels"].items():
                boundary = level_boundaries.get(key, 0)
                if boundary > 0:
                    self.levels_data.append({'name': name, 'boundary': boundary})
        self._refresh_levels_display()

        self.scales = []
        if "scales" in config:
            for name, scale_config in config["scales"].items():
                questions = scale_config.get("qnums", [])
                levels = []
                bounds = scale_config.get("bounds", {})
                order = config.get("level_order", [])
                for i, key in enumerate(order):
                    max_key = f"{key}_max"
                    if max_key in bounds:
                        boundary = bounds[max_key]
                        prev = 0
                        for lvl in self.levels_data:
                            if lvl['boundary'] == boundary:
                                start = (levels[-1]['boundary'] + 1) if levels else 1
                                levels.append({
                                    'name': lvl['name'],
                                    'boundary': boundary,
                                    'range_start': start,
                                    'range_end': boundary
                                })
                                break
                if not levels:
                    prev = 0
                    for lvl in self.levels_data:
                        start = prev + 1
                        end = lvl['boundary']
                        levels.append({
                            'name': lvl['name'],
                            'boundary': lvl['boundary'],
                            'range_start': start,
                            'range_end': end
                        })
                        prev = lvl['boundary']
                self.scales.append({
                    "name": name,
                    "questions": questions,
                    "levels": levels
                })
        self._refresh_scales_list()

        if "answer_weights" in config:
            weights = config["answer_weights"]
            if weights and len(set(weights.values())) == 1:
                self.same_weights_checkbox.setChecked(True)
                if hasattr(self, 'single_weight_spin'):
                    self.single_weight_spin.setValue(list(weights.values())[0])
                self.on_weights_checkbox_changed()
            elif weights:
                self.same_weights_checkbox.setChecked(False)
                self.on_weights_checkbox_changed()
                for i, spin in getattr(self, 'weight_spins', {}).items():
                    if i in weights:
                        spin.setValue(weights[i])

        QMessageBox.information(self, "Успех", "Профиль загружен!")

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
            display_data = {
                'name': level['name'],
                'boundary': boundary,
                'range_start': start,
                'range_end': end
            }
            badge = LevelBadge(display_data, i, len(self.levels_data))
            badge.edited.connect(lambda lvl=level, idx=i: self._edit_level(lvl, idx))
            badge.deleted.connect(lambda lvl=level: self._delete_level(lvl))
            self.levels_layout.addWidget(badge)
            prev_boundary = boundary
        self._sync_levels_with_old_format()
        self._refresh_scales_list()
        QtCore.QTimer.singleShot(100, self.adjustSize)

    def _show_error_message(self, title, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        icon_label = QLabel()
        icon_pixmap = QPixmap("resources/icons/alert-triangle.svg")
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(48, 48,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            icon_label.setPixmap(self.style().standardIcon(
                QMessageBox.Style.Warning).pixmap(48, 48))
        layout = msg_box.layout()
        layout.addWidget(icon_label, 0, 0, 1, 1,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        msg_box.exec()

    def _save_debug_config(self, scales_config, level_order, level_ru, answer_weights):
        import json
        from datetime import datetime
        from pathlib import Path
        debug_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scales_config": scales_config,
            "level_order": level_order,
            "level_ru": level_ru,
            "answer_weights": answer_weights
        }
        output_path = Path("debug_config.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        print("\n" + "="*60)
        print("✅ КОНФИГУРАЦИЯ СОХРАНЕНА В debug_config.json")
        print("="*60)
        print("\n📈 SCALES_CONFIG:")
        print(json.dumps(scales_config, indent=2, ensure_ascii=False))
        print("\n📋 LEVEL_ORDER:")
        print(level_order)
        print("\n📝 LEVEL_RU:")
        print(json.dumps(level_ru, indent=2, ensure_ascii=False))
        print("\n⚖️ ANSWER_WEIGHTS:")
        print(answer_weights)
        print("="*60 + "\n")
        return output_path

    def set_config(self, config):
        self.config = config