# ui/components/settings_dialog.py
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QDialog, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QCheckBox, QGroupBox, QScrollArea, QWidget,
    QLineEdit, QMessageBox, QTabWidget, QFrame, QGridLayout,
    QSizePolicy
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
        
        # Название
        name_label = QLabel("Название уровня:")
        name_label.setStyleSheet("color: #000000; font-size: 14px; font-weight: 500;")
        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Например, Низкий")
        self.name_edit.setFixedHeight(40)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3390EC;
            }
        """)
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)
        
        # Граница (верхняя)
        bound_label = QLabel("Верхняя граница (баллов):")
        bound_label.setStyleSheet("color: #000000; font-size: 14px; font-weight: 500;")
        self.boundary_spin = QSpinBox()
        self.boundary_spin.setRange(1, 10000)
        self.boundary_spin.setValue(boundary)
        self.boundary_spin.setFixedHeight(40)
        self.boundary_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 24px 8px 12px;
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
        layout.addWidget(bound_label)
        layout.addWidget(self.boundary_spin)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(40)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
        """)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #3390EC;
                border: 1px solid #3390EC;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
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


class LevelBadge(QWidget):
    """Badge для уровня с фиксированными цветами."""
    edited = pyqtSignal()
    deleted = pyqtSignal()
    
    def __init__(self, level_data, index, total, parent=None):
        super().__init__(parent)
        self.level_data = level_data
        self.index = index
        self.total = total

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
        self.delete_btn.clicked.connect(self.deleted.emit)
        layout.addWidget(self.delete_btn)

        # Фиксированные цвета (Telegram-стиль)
        self.bg_color = QColor(232, 245, 233)   # #E8F5E9
        self.text_color = QColor(46, 125, 50)   # #2E7D32

        self.label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 13px;
                font-weight: 500;
                background: transparent;
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
        self.all_selected_questions = set()
        self.profile_manager = ProfileManager()
        self.current_config = None
        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setIconSize(QSize(20, 20))
        
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #FFFFFF;
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
        self.profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
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
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6BBF8A;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
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
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #3390EC;
                border: 1px solid #3390EC;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
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
        QtCore.QTimer.singleShot(100, self.adjustSize)

    def _create_basic_tab(self):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # Название теста
        name_group = QVBoxLayout()
        name_group.setSpacing(6)
        name_label = QLabel("Название теста")
        name_label.setStyleSheet("color: #707579; font-size: 13px; font-weight: 500;")
        name_group.addWidget(name_label)
        
        self.test_name_edit = QLineEdit()
        self.test_name_edit.setPlaceholderText("Введите название")
        self.test_name_edit.setText("Опросник агрессивности")
        self.test_name_edit.setFixedHeight(40)
        self.test_name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
                color: #000000;
            }
            QLineEdit:focus {
                border-color: #3390EC;
            }
        """)
        name_group.addWidget(self.test_name_edit)
        
        # Количество вопросов
        questions_group = QVBoxLayout()
        questions_group.setSpacing(6)
        questions_label = QLabel("Количество вопросов")
        questions_label.setStyleSheet("color: #707579; font-size: 13px; font-weight: 500;")
        questions_group.addWidget(questions_label)
        
        self.questions_spin = QSpinBox()
        self.questions_spin.setRange(1, 1000)
        self.questions_spin.setValue(10)
        self.questions_spin.setFixedHeight(40)
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
        
        # Количество вариантов ответов
        answers_group = QVBoxLayout()
        answers_group.setSpacing(6)
        answers_label = QLabel("Количество вариантов ответов")
        answers_label.setStyleSheet("color: #707579; font-size: 13px; font-weight: 500;")
        answers_group.addWidget(answers_label)
        
        self.answers_spin = QSpinBox()
        self.answers_spin.setRange(2, 10)
        self.answers_spin.setValue(5)
        self.answers_spin.setFixedHeight(40)
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
        
        # Описание теста
        desc_group = QVBoxLayout()
        desc_group.setSpacing(6)
        desc_label = QLabel("Описание теста")
        desc_label.setStyleSheet("color: #707579; font-size: 13px; font-weight: 500;")
        desc_group.addWidget(desc_label)
        
        self.test_description_edit = QTextEdit()
        self.test_description_edit.setPlaceholderText("Введите описание теста...")
        self.test_description_edit.setFixedHeight(100)
        self.test_description_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: white;
                color: #000000;
            }
            QTextEdit:focus {
                border-color: #3390EC;
            }
        """)
        desc_group.addWidget(self.test_description_edit)
        main_layout.addLayout(desc_group)
        
        # Чекбокс с пояснением
        checkbox_group = QVBoxLayout()
        checkbox_group.setSpacing(4)
        
        self.shared_checkbox = AnimatedCheckBox("Вопросы для различных шкал одинаковы")
        self.shared_checkbox.setChecked(False)
        self.shared_checkbox.setToolTip("Если активно - один вопрос может относиться к нескольким шкалам")
        checkbox_group.addWidget(self.shared_checkbox)
        
        hint_label = QLabel("Если активно — один вопрос может относиться к нескольким шкалам")
        hint_label.setStyleSheet("color: #707579; font-size: 12px;")
        hint_label.setContentsMargins(32, 0, 0, 0)
        checkbox_group.addWidget(hint_label)
        
        main_layout.addLayout(checkbox_group)
        main_layout.addStretch()
        
        return tab

    def _create_levels_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #DFE1E5; max-height: 1px; margin-top: 2px; margin-bottom: 4px;")
        layout.addWidget(line)

        title_label = QLabel("Активные уровни")
        title_label.setStyleSheet("color: #000000; font-size: 14px; font-weight: 600; margin-bottom: 4px;")
        layout.addWidget(title_label)

        self.levels_container = QWidget()
        self.levels_layout = QFlowLayout(self.levels_container)
        self.levels_layout.setContentsMargins(6, 2, 6, 2)
        self.levels_layout.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.levels_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumHeight(80)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
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
        """)
        layout.addWidget(scroll, 1)

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
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #DFE1E5; max-height: 1px; margin-top: 2px; margin-bottom: 4px;")
        layout.addWidget(line)

        title_label = QLabel("Активные шкалы")
        title_label.setStyleSheet("color: #000000; font-size: 14px; font-weight: 600; margin-bottom: 4px;")
        layout.addWidget(title_label)

        # Контейнер для badge шкал
        self.scales_badges_container = QWidget()
        self.scales_badges_layout = QFlowLayout(self.scales_badges_container)
        self.scales_badges_layout.setContentsMargins(6, 2, 6, 2)
        self.scales_badges_layout.setSpacing(6)

        scales_scroll = QScrollArea()
        scales_scroll.setWidgetResizable(True)
        scales_scroll.setWidget(self.scales_badges_container)
        scales_scroll.setFrameShape(QFrame.Shape.NoFrame)
        scales_scroll.setMinimumHeight(40)
        scales_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        scales_scroll.setStyleSheet("""
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
        """)
        layout.addWidget(scales_scroll)

        # Временный layout для совместимости со старым кодом
        self.scales_layout = QVBoxLayout()
        self.scales_layout.setSpacing(15)

        # Форма настройки шкалы
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: none;
                border-radius: 0px;
                padding: 8px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(8)

        form_title = QLabel("Настройка шкалы")
        form_title.setStyleSheet("""
            color: #000000;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 4px;
        """)
        form_layout.addWidget(form_title)

        self.scale_name_edit = QLineEdit()
        self.scale_name_edit.setPlaceholderText("Название шкалы")
        self.scale_name_edit.setFixedHeight(36)
        self.scale_name_edit.setStyleSheet("""
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
        form_layout.addWidget(self.scale_name_edit)

        self.scale_questions_edit = QLineEdit()
        self.scale_questions_edit.setPlaceholderText("Вопросы (например: 1-20, 25, 30-40)")
        self.scale_questions_edit.setFixedHeight(36)
        self.scale_questions_edit.setStyleSheet("""
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
        form_layout.addWidget(self.scale_questions_edit)

        levels_title = QLabel("Уровни")
        levels_title.setStyleSheet("""
            color: #000000;
            font-size: 14px;
            font-weight: 600;
            margin-top: 8px;
            margin-bottom: 4px;
        """)
        form_layout.addWidget(levels_title)

        self.scale_levels_container = QWidget()
        self.scale_levels_layout = QFlowLayout(self.scale_levels_container)
        self.scale_levels_layout.setContentsMargins(4, 0, 4, 0)
        self.scale_levels_layout.setSpacing(4)
        form_layout.addWidget(self.scale_levels_container)
        self._refresh_scale_levels_badges()

        form_layout.addSpacing(12)

        add_btn = QPushButton("+ Добавить шкалу")
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
        add_btn.clicked.connect(self._add_scale_from_form)
        form_layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(form_frame)

        self.scales = []
        self._refresh_scale_levels_badges()

        tab.setLayout(layout)
        return tab

    def _refresh_scales_badges(self):
        if not hasattr(self, 'scales_badges_layout') or self.scales_badges_layout is None:
            return
        while self.scales_badges_layout.count():
            item = self.scales_badges_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for scale_data in self.scales:
            name = scale_data["name_input"].text().strip()
            questions_text = scale_data["questions_input"].text().strip()
            badge = QPushButton(f"{name} ({questions_text})")
            badge.setCursor(Qt.CursorShape.PointingHandCursor)
            badge.setStyleSheet("""
                QPushButton {
                    background-color: #E8F5E9;
                    color: #2E7D32;
                    border: none;
                    border-radius: 20px;
                    padding: 6px 12px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #D0E8D1;
                }
            """)
            badge.setFixedHeight(36)
            badge.clicked.connect(lambda checked, data=scale_data: self._edit_scale(data))
            self.scales_badges_layout.addWidget(badge)
        
    def _refresh_scale_levels_badges(self):
        if not hasattr(self, 'scale_levels_layout') or self.scale_levels_layout is None:
            return
        while self.scale_levels_layout.count():
            item = self.scale_levels_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, level in enumerate(self.levels_data):
            boundary = level['boundary']
            if i == 0:
                start = 1
            else:
                start = self.levels_data[i-1]['boundary'] + 1
            end = boundary
            display_data = {
                'name': level['name'],
                'boundary': boundary,
                'range_start': start,
                'range_end': end
            }
            badge = LevelBadge(display_data, i, len(self.levels_data))
            badge.delete_btn.setVisible(False)
            self.scale_levels_layout.addWidget(badge)

    def _add_scale_from_form(self):
        name = self.scale_name_edit.text().strip()
        questions = self.scale_questions_edit.text().strip()
        
        if not name:
            self._show_error_message("Ошибка", "Введите название шкалы.")
            return
        if not questions:
            self._show_error_message("Ошибка", "Укажите вопросы для шкалы.")
            return
        
        if not hasattr(self, 'scales_layout') or self.scales_layout is None:
            self._show_error_message("Ошибка", "Вкладка 'Шкалы' не инициализирована.")
            return
        
        # Проверяем, есть ли уже шкала с таким названием
        for scale_data in self.scales:
            if scale_data["name_input"].text().strip() == name:
                # Заменяем существующую
                scale_data["name_input"].setText(name)
                scale_data["questions_input"].setText(questions)
                selected, _ = self._parse_questions_input(questions, validate=False)
                scale_data["selected_questions"] = set(selected)
                self._refresh_scales_badges()
                self.scale_name_edit.clear()
                self.scale_questions_edit.clear()
                return
        
        # Создаём новую шкалу напрямую (без вызова add_scale, чтобы не создавать фрейм)
        name_input = QLineEdit()
        name_input.setText(name)
        questions_input = QLineEdit()
        questions_input.setText(questions)
        
        scale_data = {
            "name_input": name_input,
            "questions_input": questions_input,
            "bounds_inputs": {},
            "bounds_labels": {},
            "widget": None,
            "selected_questions": set()
        }
        self.scales.append(scale_data)
        self._refresh_scales_badges()
        self.scale_name_edit.clear()
        self.scale_questions_edit.clear()
            
    def _edit_scale(self, scale_data):
        self.scale_name_edit.setText(scale_data["name_input"].text())
        self.scale_questions_edit.setText(scale_data["questions_input"].text())
        self.scales.remove(scale_data)
        self._refresh_scales_badges()

    def _delete_scale(self, scale_data):
        if len(self.scales) <= 1:
            self._show_error_message("Ошибка", "Должна быть хотя бы одна шкала.")
            return
        self.scales.remove(scale_data)
        self._refresh_scales_badges()

    def _create_weights_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        title = QLabel("Веса ответов")
        title.setObjectName("title_label")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #000000;")
        layout.addWidget(title)
        
        self.same_weights_checkbox = QCheckBox("Одинаковые веса для всех ответов")
        self.same_weights_checkbox.setChecked(False)
        self.same_weights_checkbox.setObjectName("same_weights_checkbox")
        self.same_weights_checkbox.stateChanged.connect(self.on_weights_checkbox_changed)
        self.same_weights_checkbox.setStyleSheet("""
            QCheckBox {
                color: #212529;
                font-size: 14px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #DFE1E5;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3390EC;
                border-color: #3390EC;
            }
            QCheckBox::indicator:hover {
                border-color: #3390EC;
            }
        """)
        layout.addWidget(self.same_weights_checkbox)
        
        self.weights_container = QFrame()
        self.weights_container.setObjectName("weights_container")
        self.weights_container.setStyleSheet("""
            QFrame#weights_container {
                background-color: white;
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        self.weights_layout = QGridLayout()
        self.weights_layout.setSpacing(15)
        self.weights_container.setLayout(self.weights_layout)
        layout.addWidget(self.weights_container)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.on_weights_checkbox_changed()
        return tab

    def _parse_questions_input(self, text, validate=True):
        questions = set()
        parts = text.split(',')
        errors = []
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    if start > end:
                        errors.append(f"Неверный диапазон: {start}-{end}")
                        continue
                    questions.update(range(start, end + 1))
                except ValueError:
                    errors.append(f"Неверный формат: {part}")
                    continue
            else:
                try:
                    questions.add(int(part))
                except ValueError:
                    errors.append(f"Неверное число: {part}")
                    continue
        
        max_questions = self.questions_spin.value()
        if validate:
            invalid_questions = {q for q in questions if q < 1 or q > max_questions}
            if invalid_questions:
                errors.append(f"Вопросы вне диапазона (1-{max_questions}): {sorted(invalid_questions)}")
            questions = {q for q in questions if 1 <= q <= max_questions}
        
        return sorted(list(questions)), errors

    def _on_questions_input_changed(self, scale_data):
        selected, errors = self._parse_questions_input(scale_data["questions_input"].text(), validate=True)
        scale_data["selected_questions"] = set(selected)
        
        if errors:
            scale_data["questions_input"].setObjectName("error_input")
        else:
            scale_data["questions_input"].setObjectName("level_name_input")
        
        scale_data["questions_input"].style().unpolish(scale_data["questions_input"])
        scale_data["questions_input"].style().polish(scale_data["questions_input"])

    def add_scale(self):
        """Используется только для внутреннего перестроения шкал, не из формы."""
        if len(self.levels_data) == 0:
            self._show_error_message("Ошибка", "Сначала добавьте уровни показателей на вкладке 'Уровни'")
            self.tabs.setCurrentIndex(1)
            return
        
        scale_index = len(self.scales) + 1
        scale_frame = QFrame()
        scale_frame.setObjectName("scale_frame")
        scale_layout = QVBoxLayout()
        scale_layout.setContentsMargins(15, 15, 15, 15)
        scale_layout.setSpacing(15)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Название шкалы:"))
        name_input = QLineEdit()
        name_input.setPlaceholderText("например, 'Тревожность'")
        name_input.setObjectName("level_name_input")
        name_layout.addWidget(name_input)
        name_layout.addStretch()
        scale_layout.addLayout(name_layout)
        
        questions_group = QGroupBox("Вопросы для этой шкалы:")
        questions_group.setObjectName("questions_group")
        questions_layout = QVBoxLayout()
        questions_layout.setSpacing(10)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Введите номера вопросов:"))
        self.questions_input = QLineEdit()
        self.questions_input.setPlaceholderText("Пример: 1-20, 25, 30-40")
        self.questions_input.setObjectName("level_name_input")
        self.questions_input.textChanged.connect(lambda: self._on_questions_input_changed(scale_data))
        input_layout.addWidget(self.questions_input)
        questions_layout.addLayout(input_layout)
        
        hint_label = QLabel("💡 Формат: отдельные числа (1, 5, 10) или диапазоны (1-20, 30-40)")
        hint_label.setObjectName("hint_label")
        questions_layout.addWidget(hint_label)
        
        questions_group.setLayout(questions_layout)
        scale_layout.addWidget(questions_group)
        
        levels_title = QLabel("Уровни")
        levels_title.setStyleSheet("""
            color: #000000;
            font-size: 14px;
            font-weight: 600;
            margin-top: 8px;
            margin-bottom: 4px;
        """)
        scale_layout.addWidget(levels_title)
        
        scale_levels_container = QWidget()
        scale_levels_layout = QFlowLayout(scale_levels_container)
        scale_levels_layout.setContentsMargins(4, 0, 4, 0)
        scale_levels_layout.setSpacing(4)
        
        for i, level in enumerate(self.levels_data):
            boundary = level['boundary']
            if i == 0:
                start = 1
            else:
                start = self.levels_data[i-1]['boundary'] + 1
            end = boundary
            display_data = {
                'name': level['name'],
                'boundary': boundary,
                'range_start': start,
                'range_end': end
            }
            badge = LevelBadge(display_data, i, len(self.levels_data))
            badge.delete_btn.setVisible(False)
            scale_levels_layout.addWidget(badge)
        
        scale_layout.addWidget(scale_levels_container)
        
        bounds_group = QGroupBox("Границы уровней для шкалы:")
        bounds_group.setObjectName("bounds_group")
        bounds_layout = QGridLayout()
        bounds_layout.setSpacing(15)
        
        bounds_inputs = {}
        bounds_labels = {}
        
        for i, level_key in enumerate(self.level_order):
            if i < len(self.levels_data):
                level_name = self.levels_data[i]['name']
            else:
                level_name = f"Уровень {i+1}"
            
            row = i // 5
            col = i % 5
            
            if i == 0:
                range_text = f"{level_name} (0-25):"
            else:
                range_text = f"{level_name} (26-50):"
            
            range_label = QLabel(range_text)
            range_label.setObjectName(f"range_label_{level_key}")
            bounds_layout.addWidget(range_label, row, col * 2)
            bounds_labels[level_key] = range_label
            
            bound_spin = QSpinBox()
            bound_spin.setRange(0, 1000)
            bound_spin.setValue((i + 1) * 25)
            bound_spin.setObjectName("level_boundary_spin")
            
            bound_spin.valueChanged.connect(lambda: self._update_bounds_labels(scale_data, bounds_labels))
            bounds_layout.addWidget(bound_spin, row, col * 2 + 1)
            bounds_inputs[level_key] = bound_spin
        
        bounds_group.setLayout(bounds_layout)
        scale_layout.addWidget(bounds_group)
        
        remove_layout = QHBoxLayout()
        remove_layout.addStretch()
        remove_btn = QPushButton("Удалить шкалу")
        remove_btn.setObjectName("btn_delete_scale")
        remove_btn.setIcon(QIcon("resources/icons/trash.svg"))
        remove_btn.clicked.connect(lambda: self.remove_scale(scale_frame))
        remove_layout.addWidget(remove_btn)
        scale_layout.addLayout(remove_layout)
        
        scale_frame.setLayout(scale_layout)
        self.scales_layout.addWidget(scale_frame)
        
        scale_data = {
            "name_input": name_input,
            "questions_input": self.questions_input,
            "bounds_inputs": bounds_inputs,
            "bounds_labels": bounds_labels,
            "widget": scale_frame,
            "selected_questions": set()
        }
        self.scales.append(scale_data)
        self._update_bounds_labels(scale_data, bounds_labels)
        self._refresh_scales_badges()

    def _update_bounds_labels(self, scale_data, bounds_labels):
        previous_boundary = 0
        for i, level_key in enumerate(self.level_order):
            if i < len(self.levels_data):
                level_name = self.levels_data[i]['name']
            else:
                level_name = f"Уровень {i+1}"
            
            if level_key not in scale_data["bounds_inputs"]:
                continue
            
            bound_spin = scale_data["bounds_inputs"][level_key]
            current_boundary = bound_spin.value()
            
            if i == 0:
                range_text = f"{level_name} (0-{current_boundary}):"
            else:
                range_text = f"{level_name} ({previous_boundary + 1}-{current_boundary}):"
            
            if level_key in bounds_labels:
                bounds_labels[level_key].setText(range_text)
            
            previous_boundary = current_boundary

    def remove_scale(self, widget):
        if len(self.scales) <= 1:
            self._show_error_message("Ошибка", "Должна быть хотя бы одна шкала")
            return
        
        for scale_data in self.scales:
            if scale_data["widget"] == widget:
                self.all_selected_questions -= scale_data["selected_questions"]
                break
        
        self.scales = [s for s in self.scales if s["widget"] != widget]
        widget.deleteLater()

    def _update_scales_levels(self):
        if not hasattr(self, 'scales_layout') or self.scales_layout is None:
            return
        if not self.scales:
            return
        
        saved_scales = []
        for scale_data in self.scales:
            saved_scales.append({
                "name": scale_data["name_input"].text(),
                "questions_text": scale_data["questions_input"].text(),
                "bounds": {k: v.value() for k, v in scale_data["bounds_inputs"].items()},
                "selected_questions": scale_data["selected_questions"]
            })
        
        while self.scales_layout.count():
            item = self.scales_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.scales = []
        self.all_selected_questions = set()
        
        for saved in saved_scales:
            self.add_scale()
            if self.scales:
                new_scale = self.scales[-1]
                new_scale["name_input"].setText(saved["name"])
                new_scale["questions_input"].setText(saved["questions_text"])
                new_scale["selected_questions"] = saved["selected_questions"]
                self.all_selected_questions.update(saved["selected_questions"])
                
                for key, value in saved["bounds"].items():
                    if key in new_scale["bounds_inputs"]:
                        new_scale["bounds_inputs"][key].setValue(value)
                
                self._update_bounds_labels(new_scale, new_scale["bounds_labels"])

    def on_questions_changed(self, value):
        self._recreate_scales()
        self._update_scales_levels()

    def on_answers_changed(self, value):
        self.on_weights_checkbox_changed()

    def _recreate_scales(self):
        saved_scales = []
        for scale_data in self.scales:
            saved_scales.append({
                "name": scale_data["name_input"].text(),
                "questions_text": scale_data["questions_input"].text(),
                "bounds": {k: v.value() for k, v in scale_data["bounds_inputs"].items()}
            })
        
        while self.scales_layout.count():
            item = self.scales_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.scales = []
        self.all_selected_questions = set()
        
        for saved in saved_scales:
            self.add_scale()
            if self.scales:
                new_scale = self.scales[-1]
                new_scale["name_input"].setText(saved["name"])
                new_scale["questions_input"].setText(saved["questions_text"])
                selected, _ = self._parse_questions_input(saved["questions_text"])
                new_scale["selected_questions"] = set(selected)
                self.all_selected_questions.update(selected)

    def on_weights_checkbox_changed(self):
        while self.weights_layout.count():
            item = self.weights_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self.same_weights_checkbox.isChecked():
            label = QLabel("Вес для всех ответов:")
            label.setObjectName("weight_label")
            self.weights_layout.addWidget(label, 0, 0)
            self.single_weight_spin = QSpinBox()
            self.single_weight_spin.setRange(1, 100)
            self.single_weight_spin.setValue(1)
            self.single_weight_spin.setObjectName("single_weight_spin")
            self.weights_layout.addWidget(self.single_weight_spin, 0, 1)
        else:
            num_answers = self.answers_spin.value()
            self.weight_spins = {}
            for i in range(1, num_answers + 1):
                row = (i - 1) // 5
                col = (i - 1) % 5
                label = QLabel(f"Ответ {i}:")
                label.setObjectName("weight_label")
                self.weights_layout.addWidget(label, row, col * 2)
                
                weight_spin = QSpinBox()
                weight_spin.setRange(1, 100)
                weight_spin.setValue(i)
                weight_spin.setObjectName("level_boundary_spin")
                self.weights_layout.addWidget(weight_spin, row, col * 2 + 1)
                self.weight_spins[i] = weight_spin
            
            for row in range((self.answers_spin.value() - 1) // 5 + 1):
                self.weights_layout.setColumnStretch(row * 2 + 10, 1)

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
        
        for i, scale_data in enumerate(self.scales):
            name = scale_data["name_input"].text().strip()
            if not name:
                self._show_error_message("Ошибка", f"Шкала {i + 1} не имеет названия")
                self.tabs.setCurrentIndex(2)
                scale_data["name_input"].setFocus()
                return
            
            selected_questions, errors = self._parse_questions_input(
                scale_data["questions_input"].text(),
                validate=True
            )
            if errors:
                self._show_error_message(
                    "Ошибка",
                    f"Шкала '{name}':\n" + "\n".join(errors)
                )
                self.tabs.setCurrentIndex(2)
                scale_data["questions_input"].setFocus()
                return
            
            if not selected_questions:
                self._show_error_message("Ошибка", f"Шкала '{name}': не выбраны вопросы")
                self.tabs.setCurrentIndex(2)
                return
            
            scale_data["selected_questions"] = set(selected_questions)
        
        scales_config = {}
        for scale_data in self.scales:
            scale_name = scale_data["name_input"].text().strip()
            selected_questions = sorted(list(scale_data["selected_questions"]))
            
            bounds = {}
            level_values = []
            for level_key in self.level_order:
                if level_key in scale_data["bounds_inputs"]:
                    level_values.append(scale_data["bounds_inputs"][level_key].value())
            
            for i, level_key in enumerate(self.level_order):
                if i < len(level_values):
                    if i == 0:
                        bounds[f"{level_key}_max"] = level_values[i]
                    else:
                        bounds[f"{level_key}_min"] = level_values[i-1] + 1
                        bounds[f"{level_key}_max"] = level_values[i]
            
            scales_config[scale_name] = {
                "title_ru": scale_name,
                "qnums": selected_questions,
                "bounds": bounds
            }
        
        level_order = self.level_order.copy()
        
        level_ru = {}
        for i, level_data in enumerate(self.levels_data):
            level_name = level_data['name'].strip()
            if i < len(self.level_order):
                level_ru[self.level_order[i]] = level_name
            else:
                level_ru[f"level{i+1}"] = level_name
        
        answer_weights = {}
        if self.same_weights_checkbox.isChecked():
            weight = self.single_weight_spin.value()
            for i in range(1, self.answers_spin.value() + 1):
                answer_weights[i] = weight
        else:
            for i, spin in self.weight_spins.items():
                answer_weights[i] = spin.value()
        
        if not self.shared_checkbox.isChecked():
            all_questions = {}
            for scale_data in self.scales:
                scale_name = scale_data["name_input"].text().strip()
                selected_questions = sorted(list(scale_data["selected_questions"]))
                for question in selected_questions:
                    if question not in all_questions:
                        all_questions[question] = []
                    all_questions[question].append(scale_name)
            
            duplicate_questions = {q: scales for q, scales in all_questions.items() if len(scales) > 1}
            if duplicate_questions:
                error_messages = []
                for question, scales in sorted(duplicate_questions.items()):
                    error_messages.append(f"Вопрос {question}: {', '.join(scales)}")
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
            name = scale_data["name_input"].text().strip()
            if name:
                selected = list(scale_data["selected_questions"])
                scales[name] = {
                    "title_ru": name,
                    "qnums": sorted(selected),
                    "bounds": {k: v.value() for k, v in scale_data["bounds_inputs"].items()}
                }
        
        levels = {}
        level_boundaries = {}
        for i, level_data in enumerate(self.levels_data):
            key = self.level_order[i] if i < len(self.level_order) else f"level{i+1}"
            levels[key] = level_data['name']
            level_boundaries[key] = level_data['boundary']
        
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
        if "same_bounds" in config:
            self.same_bounds_checkbox.setChecked(config["same_bounds"])
        
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
        
        while self.scales_layout.count():
            item = self.scales_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.scales = []
        if "scales" in config:
            for name, scale_config in config["scales"].items():
                self.add_scale()
                if self.scales:
                    new_scale = self.scales[-1]
                    new_scale["name_input"].setText(name)
                    
                    if "qnums" in scale_config:
                        questions_text = ", ".join(map(str, scale_config["qnums"]))
                        new_scale["questions_input"].setText(questions_text)
                        new_scale["selected_questions"] = set(scale_config["qnums"])
                    
                    if "bounds" in scale_config:
                        for key, value in scale_config["bounds"].items():
                            if key in new_scale["bounds_inputs"]:
                                new_scale["bounds_inputs"][key].setValue(value)
        
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
        
        for scale_data in self.scales:
            if "bounds_labels" in scale_data:
                self._update_bounds_labels(scale_data, scale_data["bounds_labels"])
        
        QMessageBox.information(self, "Успех", "Профиль загружен!")

    def _update_level_names_in_scales(self):
        for scale_data in self.scales:
            self._update_bounds_labels(scale_data, scale_data["bounds_labels"])

    def _update_bounds_in_scales(self):
        if hasattr(self, 'same_bounds_checkbox') and self.same_bounds_checkbox.isChecked():
            for scale_data in self.scales:
                for i, level_key in enumerate(self.level_order):
                    if level_key in scale_data["bounds_inputs"]:
                        if i < len(self.levels_data):
                            scale_data["bounds_inputs"][level_key].setValue(
                                self.levels_data[i]['boundary']
                            )
                        if "bounds_labels" in scale_data:
                            self._update_bounds_labels(scale_data, scale_data["bounds_labels"])
    
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
        self._refresh_scale_levels_badges()
        
        if hasattr(self, 'scales_layout') and self.scales_layout is not None:
            self._update_scales_levels()
        
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