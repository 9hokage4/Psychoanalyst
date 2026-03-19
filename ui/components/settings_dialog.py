# ui/components/settings_dialog.py
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QDialog, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QCheckBox, QGroupBox, QScrollArea, QWidget,
    QLineEdit, QMessageBox, QTabWidget, QFrame, QGridLayout,
    QSizePolicy
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from pathlib import Path
from utils.profile_manager import ProfileManager
from ui.components.profile_dialog import ProfileDialog
from PyQt6.QtCore import Qt, QPropertyAnimation, QRectF, QPointF, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtWidgets import QAbstractButton, QSizePolicy
from PyQt6.QtSvg import QSvgRenderer


class AnimatedCheckBox(QAbstractButton):
    """Кастомный чекбокс с анимацией заливки фона и SVG-галочкой."""
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        # Параметры
        self.indicator_size = 22
        self.border_radius = 4
        self.spacing = 10
        self.color_unchecked = QColor("#FFFFFF")        # белый фон
        self.color_checked = QColor("#3390EC")          # синий Telegram
        self.border_color = QColor("#DFE1E5")
        self.border_color_hover = QColor("#3390EC")
        self.text_color = QColor("#000000")

        # Анимация
        self._color_factor = 0.0  # обязательно инициализируем!
        self._animation = QPropertyAnimation(self, b"colorFactor")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hovered = False

        # Загружаем SVG-галочку
        self.check_renderer = QSvgRenderer("resources/icons/check.svg")
        if not self.check_renderer.isValid():
            print("Warning: check.svg not found, checkmark will not be drawn")
            self.check_renderer = None

        self.toggled.connect(self._on_toggled)

    def sizeHint(self):
        text_width = self.fontMetrics().horizontalAdvance(self.text())
        return QSize(self.indicator_size + self.spacing + text_width,
                     self.indicator_size + 8)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        y = (self.height() - self.indicator_size) // 2
        indicator_rect = QRectF(0, y, self.indicator_size, self.indicator_size)

        # Интерполируем цвет фона
        current_color = self._interpolate_color(self.color_unchecked, self.color_checked, self._color_factor)

        # Рисуем фон
        painter.setBrush(QBrush(current_color))
        pen_color = self.border_color_hover if self._hovered else self.border_color
        painter.setPen(QPen(pen_color, 2))
        painter.drawRoundedRect(indicator_rect, self.border_radius, self.border_radius)

        # Рисуем галочку, если checked
        if self.isChecked() and self.check_renderer:
            painter.save()
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(Qt.PenStyle.NoPen)
            size = self.indicator_size * 0.6
            viewBox = self.check_renderer.viewBox()
            if viewBox.isValid():
                scale = size / max(viewBox.width(), viewBox.height())
                painter.translate(indicator_rect.center() - QPointF(viewBox.width() * scale / 2,
                                                                   viewBox.height() * scale / 2))
                self.check_renderer.render(painter, QRectF(0, 0,
                                                          viewBox.width() * scale,
                                                          viewBox.height() * scale))
            painter.restore()

        # Рисуем текст
        text_x = self.indicator_size + self.spacing
        text_rect = QRectF(text_x, 0, self.width() - text_x, self.height())
        painter.setPen(QPen(self.text_color))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def _on_toggled(self, checked):
        self._animation.stop()
        self._animation.setStartValue(0.0 if not checked else 1.0)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def _interpolate_color(self, color1, color2, factor):
        r = color1.red() + (color2.red() - color1.red()) * factor
        g = color1.green() + (color2.green() - color1.green()) * factor
        b = color1.blue() + (color2.blue() - color1.blue()) * factor
        a = color1.alpha() + (color2.alpha() - color1.alpha()) * factor
        return QColor(int(r), int(g), int(b), int(a))

    # Свойства для анимации
    def get_color_factor(self):
        return self._color_factor

    def set_color_factor(self, value):
        self._color_factor = value
        self.update()

    colorFactor = pyqtProperty(float, get_color_factor, set_color_factor)


class SettingsDialog(QDialog):
    config_saved = pyqtSignal(dict, list, dict, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Настройки теста")
        self.setWindowIcon(QIcon("resources/icons/cog.svg"))
        self.setMinimumSize(900, 700)
        self.setModal(True)
        self.scales = []
        self.levels = []
        self.level_order = []
        self.all_selected_questions = set()
        self.profile_manager = ProfileManager()
        self.current_config = None
        self.init_ui()

    def init_ui(self):
        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ===== Вкладки =====
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setIconSize(QSize(20, 20))

        # Стили для вкладок (применяются только к этому виджету)
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

        # Создаём вкладки
        self.basic_tab = self._create_basic_tab()
        self.tabs.addTab(self.basic_tab, QIcon("resources/icons/cog.svg"), "Основные")

        self.levels_tab = self._create_levels_tab()
        self.tabs.addTab(self.levels_tab, QIcon("resources/icons/chart-line.svg"), "Уровни")

        self.scales_tab = self._create_scales_tab()
        self.tabs.addTab(self.scales_tab, QIcon("resources/icons/charts.svg"), "Шкалы")

        self.weights_tab = self._create_weights_tab()
        self.tabs.addTab(self.weights_tab, QIcon("resources/icons/scale.svg"), "Веса")

        main_layout.addWidget(self.tabs)

        # ===== Панель кнопок внизу =====
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

        # Кнопка "Профили"
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

        # Кнопка "Сохранить профиль"
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

        # Кнопка "Отмена"
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

    def _create_basic_tab(self):
        tab = QWidget()
        # Основной вертикальный layout с отступами от краёв (24px)
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)  # расстояние между группами

        # --- Группа 1: Название теста и количество вопросов (две колонки) ---
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(16)

        # Название теста
        name_group = QVBoxLayout()
        name_group.setSpacing(6)
        name_label = QLabel("Название теста")
        name_label.setStyleSheet("color: #707579; font-size: 13px; font-weight: 500;")
        name_group.addWidget(name_label)

        self.test_name_edit = QLineEdit()
        self.test_name_edit.setPlaceholderText("Введите название")
        self.test_name_edit.setText("Опросник агрессивности")  # пример
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
        row1_layout.addLayout(name_group)

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
        # Стилизация спинбокса со стрелками
        self.questions_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 24px 8px 12px;  /* место для стрелок */
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
        row1_layout.addLayout(questions_group)

        main_layout.addLayout(row1_layout)

        # --- Группа 2: Количество вариантов ответов (на всю ширину) ---
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

        # --- Группа 3: Описание теста ---
        desc_group = QVBoxLayout()
        desc_group.setSpacing(6)
        desc_label = QLabel("Описание теста")
        desc_label.setStyleSheet("color: #707579; font-size: 13px; font-weight: 500;")
        desc_group.addWidget(desc_label)

        self.test_description_edit = QTextEdit()
        self.test_description_edit.setPlaceholderText("Введите описание теста...")
        self.test_description_edit.setFixedHeight(100)  # чуть больше, чем min-height, но можно регулировать
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

        # --- Группа 4: Чекбокс с пояснением ---
        checkbox_group = QVBoxLayout()
        checkbox_group.setSpacing(4)

        # Кастомный чекбокс через QCheckBox (стилизация индикатора)
        self.shared_checkbox = AnimatedCheckBox("Вопросы для различных шкал одинаковы")
        self.shared_checkbox.setChecked(False)
        self.shared_checkbox.setToolTip("Если активно - один вопрос может относиться к нескольким шкалам")
        #self.shared_checkbox.toggled.connect(self.on_shared_checkbox_toggled)

        checkbox_group.addWidget(self.shared_checkbox)

        # Пояснение под чекбоксом
        hint_label = QLabel("Если активно — один вопрос может относиться к нескольким шкалам")
        hint_label.setStyleSheet("color: #707579; font-size: 12px;")
        hint_label.setContentsMargins(32, 0, 0, 0)  # отступ слева 32px для выравнивания с текстом чекбокса
        checkbox_group.addWidget(hint_label)

        main_layout.addLayout(checkbox_group)

        # Добавляем растяжку в конце, чтобы все элементы прижимались к верху
        main_layout.addStretch()

        return tab

    def _create_levels_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Уровни показателей")
        title.setObjectName("title_label")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #000000;")
        layout.addWidget(title)

        info = QLabel("💡 Добавьте уровни показателей (например: Низкий, Средний, Высокий)")
        info.setObjectName("info_label")
        info.setStyleSheet("color: #707579; font-size: 13px; font-weight: 500; margin-bottom: 6px;")
        layout.addWidget(info)

        self.same_bounds_checkbox = QCheckBox("Границы для шкал совпадают")
        self.same_bounds_checkbox.setChecked(True)
        self.same_bounds_checkbox.stateChanged.connect(self.on_same_bounds_changed)
        self.same_bounds_checkbox.setStyleSheet("""
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
        layout.addWidget(self.same_bounds_checkbox)

        add_btn = QPushButton("+ Добавить уровень")
        add_btn.setObjectName("btn_add_level")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.add_level)
        layout.addWidget(add_btn)

        self.levels_container = QWidget()
        self.levels_container.setObjectName("levels_container")
        self.levels_layout = QVBoxLayout()
        self.levels_layout.setSpacing(15)
        self.levels_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.levels_layout.setContentsMargins(0, 0, 0, 0)
        self.levels_container.setLayout(self.levels_layout)

        levels_scroll = QScrollArea()
        levels_scroll.setWidgetResizable(True)
        levels_scroll.setWidget(self.levels_container)
        levels_scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        levels_scroll.setObjectName("levels_scroll")
        levels_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                background-color: white;
                padding: 15px;
                min-width: 800px;
                max-width: 750px;
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

        layout.addWidget(levels_scroll, alignment=Qt.AlignmentFlag.AlignHCenter)

        tab.setLayout(layout)
        return tab

    def _create_scales_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Шкалы теста")
        title.setObjectName("title_label")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #000000;")
        layout.addWidget(title)

        info_label = QLabel("💡 Добавьте шкалы и укажите вопросы для каждой")
        info_label.setObjectName("info_label")
        info_label.setStyleSheet("color: #707579; font-size: 13px; font-weight: 500; margin-bottom: 6px;")
        layout.addWidget(info_label)

        add_btn = QPushButton("+ Добавить шкалу")
        add_btn.setObjectName("btn_add_scale")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.add_scale)
        layout.addWidget(add_btn)

        self.scales_container = QWidget()
        self.scales_container.setObjectName("scales_container")
        self.scales_layout = QVBoxLayout()
        self.scales_layout.setSpacing(15)
        self.scales_container.setLayout(self.scales_layout)

        scales_scroll = QScrollArea()
        scales_scroll.setWidgetResizable(True)
        scales_scroll.setWidget(self.scales_container)
        scales_scroll.setObjectName("scales_scroll")
        scales_scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        scales_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                background-color: white;
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
        layout.addWidget(scales_scroll, 1)

        tab.setLayout(layout)
        return tab

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

    def add_level(self):
        level_index = len(self.levels) + 1
        level_key = f"level{level_index}"
        
        level_frame = QFrame()
        level_frame.setObjectName("level_frame")
        level_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        level_layout = QHBoxLayout()
        level_layout.setContentsMargins(15, 8, 15, 8)
        level_layout.setSpacing(6)
        
        level_num_title = QLabel(f"{level_index}. Название:")
        level_num_title.setObjectName("level_num_title")
        level_num_title.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        level_num_title.adjustSize()
        level_layout.addWidget(level_num_title)
        level_layout.setAlignment(level_num_title, Qt.AlignmentFlag.AlignVCenter)
        
        name_input = QLineEdit()
        name_input.setObjectName("level_name_input")
        name_input.setPlaceholderText("например, 'Низкий'")
        name_input.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        name_input.textChanged.connect(self._update_level_names_in_scales)
        level_layout.addWidget(name_input)
        level_layout.setAlignment(name_input, Qt.AlignmentFlag.AlignVCenter)
        
        level_layout.addSpacing(4)
        
        boundary_label = QLabel("Граница (баллов):")
        boundary_label.setObjectName("level_label")
        boundary_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        boundary_label.adjustSize()
        level_layout.addWidget(boundary_label)
        level_layout.setAlignment(boundary_label, Qt.AlignmentFlag.AlignVCenter)
        
        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        boundary_spin = QSpinBox()
        boundary_spin.setObjectName("level_boundary_spin")
        boundary_spin.setRange(0, 1000)
        boundary_spin.setValue(level_index * 25)
        boundary_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        boundary_spin.valueChanged.connect(self._update_bounds_in_scales)
        right_layout.addWidget(boundary_spin)
        
        hint_icon = QLabel()
        hint_icon.setObjectName("hint_icon")
        hint_icon.setText("")
        hint_icon.setToolTip("Верхняя граница уровня")
        hint_icon.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        hint_icon.setVisible(True)
        hint_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_pixmap = QPixmap("resources/icons/help.svg")
        if not icon_pixmap.isNull():
            hint_icon.setPixmap(icon_pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        right_layout.addWidget(hint_icon)
        
        remove_btn = QPushButton(" Удалить")
        remove_btn.setObjectName("btn_delete_level")
        remove_btn.setIcon(QIcon("resources/icons/trash.svg"))
        remove_btn.setIconSize(QSize(16, 16))
        remove_btn.clicked.connect(lambda: self.remove_level(level_frame, level_key))
        right_layout.addWidget(remove_btn)
        
        level_layout.addLayout(right_layout)
        
        level_frame.setLayout(level_layout)
        self.levels_layout.addWidget(level_frame)
        
        self.level_order.append(level_key)
        self.levels.append({
            "key": level_key,
            "name_input": name_input,
            "boundary": boundary_spin,
            "boundary_label": boundary_label,
            "hint_label": hint_icon,
            "widget": level_frame,
            "num_label": level_num_title
        })
        
        self.on_same_bounds_changed()
        self._update_scales_levels()
    
    def on_same_bounds_changed(self):
        show_bounds = self.same_bounds_checkbox.isChecked()
        
        for level_data in self.levels:
            level_data["boundary_label"].setVisible(show_bounds)
            level_data["boundary"].setVisible(show_bounds)
            level_data["hint_label"].setVisible(show_bounds)
        
        for scale_data in self.scales:
            for level_key, bound_spin in scale_data["bounds_inputs"].items():
                bound_spin.setEnabled(not show_bounds)
                
                if show_bounds:
                    for level_data in self.levels:
                        level_key = level_data["key"]
                        if level_key in scale_data["bounds_inputs"]:
                            scale_data["bounds_inputs"][level_key].setValue(
                                level_data["boundary"].value()
                            )
                    
                    if "bounds_labels" in scale_data:
                        self._update_bounds_labels(scale_data, scale_data["bounds_labels"])
        
        self._update_scales_levels()
    
    def _update_scales_with_common_bounds(self):
        for scale_data in self.scales:
            for i, level_data in enumerate(self.levels):
                level_key = level_data["key"]
                if level_key in scale_data["bounds_inputs"]:
                    scale_data["bounds_inputs"][level_key].setValue(
                        level_data["boundary"].value()
                    )
                    self._update_bounds_labels(scale_data, scale_data["bounds_labels"])
    
    def remove_level(self, widget, level_key):
        if len(self.levels) <= 1:
            self._show_error_message("Ошибка", "Должен быть хотя бы один уровень")
            return
        
        widget.deleteLater()
        self.level_order.remove(level_key)
        self.levels = [l for l in self.levels if l["key"] != level_key]
        self._update_level_numbers()
        self._update_scales_levels()
    
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
        if len(self.levels) == 0:
            self._show_error_message("Ошибка", "Сначала добавьте уровни показателей на вкладке 'Уровни показателей'")
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
        
        bounds_group = QGroupBox("Границы уровней для шкалы:")
        bounds_group.setObjectName("bounds_group")
        bounds_layout = QGridLayout()
        bounds_layout.setSpacing(15)
        
        bounds_inputs = {}
        bounds_labels = {}
        
        for i, level_data in enumerate(self.levels):
            level_name = level_data["name_input"].text()
            if not level_name:
                level_name = f"Уровень {self.levels.index(level_data) + 1}"
            
            row = i // 5
            col = i % 5
            
            if i == 0:
                range_text = f"{level_name} (0-25):"
            else:
                range_text = f"{level_name} (26-50):"
            
            range_label = QLabel(range_text)
            range_label.setObjectName(f"range_label_{level_data['key']}")
            bounds_layout.addWidget(range_label, row, col * 2)
            bounds_labels[level_data["key"]] = range_label
            
            bound_spin = QSpinBox()
            bound_spin.setRange(0, 1000)
            bound_spin.setValue((i + 1) * 25)
            bound_spin.setObjectName("level_boundary_spin")
            
            if self.same_bounds_checkbox.isChecked():
                bound_spin.setEnabled(False)
            
            bound_spin.valueChanged.connect(lambda: self._update_bounds_labels(scale_data, bounds_labels))
            bounds_layout.addWidget(bound_spin, row, col * 2 + 1)
            bounds_inputs[level_data["key"]] = bound_spin
        
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
    
    def _update_bounds_labels(self, scale_data, bounds_labels):
        previous_boundary = 0
        for i, level_data in enumerate(self.levels):
            level_key = level_data["key"]
            level_name = level_data["name_input"].text()
            if not level_name:
                level_name = f"Уровень {self.levels.index(level_data) + 1}"
            
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
    
    def _update_level_numbers(self):
        for i, level_data in enumerate(self.levels):
            if "num_label" in level_data:
                level_data["num_label"].setText(f"{i + 1}. Название:")
    
    def _update_scales_levels(self):
        """Обновляет уровни во всех шкалах (при добавлении/удалении уровня)"""
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
        
        if len(self.levels) < 1:
            self._show_error_message("Ошибка", "Добавьте хотя бы один уровень показателей")
            self.tabs.setCurrentIndex(1)
            return
        
        for i, level_data in enumerate(self.levels):
            name = level_data["name_input"].text().strip()
            if not name:
                self._show_error_message("Ошибка", f"Уровень {i + 1} не имеет названия")
                self.tabs.setCurrentIndex(1)
                level_data["name_input"].setFocus()
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
        
        # === 1. SCALES (ключи - русские названия шкал) ===
        scales_config = {}
        for scale_data in self.scales:
            scale_name = scale_data["name_input"].text().strip()
            selected_questions = sorted(list(scale_data["selected_questions"]))
            
            # ← Формируем bounds в правильном формате (low_max, mid_low_min, etc.)
            bounds = {}
            level_values = []
            
            # Собираем значения границ по порядку уровней
            for level_key in self.level_order:
                if level_key in scale_data["bounds_inputs"]:
                    level_values.append(scale_data["bounds_inputs"][level_key].value())
            
            # Создаём границы (low_max, mid_low_min, mid_low_max, etc.)
            for i, level_key in enumerate(self.level_order):
                if i < len(level_values):
                    if i == 0:
                        # Первый уровень: только max
                        bounds[f"{level_key}_max"] = level_values[i]
                    else:
                        # Остальные уровни: min и max
                        bounds[f"{level_key}_min"] = level_values[i-1] + 1
                        bounds[f"{level_key}_max"] = level_values[i]
            
            # ← Ключ шкалы - полное русское название!
            scales_config[scale_name] = {
                "title_ru": scale_name,
                "qnums": selected_questions,
                "bounds": bounds
            }
        
        # === 2. LEVEL_ORDER (технические ключи) ===
        level_order = self.level_order.copy()  # ["low", "mid_low", "mid_high", "high"]
        
        # === 3. LEVEL_RU (названия от пользователя) ===
        level_ru = {}
        for i, level_data in enumerate(self.levels):
            level_name = level_data["name_input"].text().strip()
            
            # Сопоставляем индекс уровня с ключом из level_order
            if i < len(self.level_order):
                level_ru[self.level_order[i]] = level_name
            else:
                level_ru[level_data["key"]] = level_name
        
        # === 4. ANSWER_WEIGHTS ===
        answer_weights = {}
        if self.same_weights_checkbox.isChecked():
            weight = self.single_weight_spin.value()
            for i in range(1, self.answers_spin.value() + 1):
                answer_weights[i] = weight
        else:
            for i, spin in self.weight_spins.items():
                answer_weights[i] = spin.value()
        
        # === ПРОВЕРКА НА ПОВТОРЯЮЩИЕСЯ ВОПРОСЫ ===
        if not self.shared_checkbox.isChecked():
            all_questions = {}  # {вопрос: [список шкал где встречается]}
            
            for scale_data in self.scales:
                scale_name = scale_data["name_input"].text().strip()
                selected_questions = sorted(list(scale_data["selected_questions"]))
                
                for question in selected_questions:
                    if question not in all_questions:
                        all_questions[question] = []
                    all_questions[question].append(scale_name)
            
            # Находим повторяющиеся вопросы
            duplicate_questions = {q: scales for q, scales in all_questions.items() if len(scales) > 1}
            
            if duplicate_questions:
                # Формируем сообщение об ошибке
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
            
        # === 🆕 СОХРАНЯЕМ В JSON ДЛЯ ПРОВЕРКИ ===
        self._save_debug_config(scales_config, level_order, level_ru, answer_weights)
        
        # === ОТПРАВЛЯЕМ В PROCESSOR.PY ===
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
        for level_data in self.levels:
            name = level_data["name_input"].text().strip()
            if name:
                levels[level_data["key"]] = name
                if level_data.get("boundary"):
                    level_boundaries[level_data["key"]] = level_data["boundary"].value()
        
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
            "same_bounds": self.same_bounds_checkbox.isChecked() if hasattr(self, 'same_bounds_checkbox') else False
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
        
        while self.levels_layout.count():
            item = self.levels_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.levels = []
        self.level_order = []
        
        if "levels" in config:
            level_boundaries = config.get("level_boundaries", {})
            for key, name in config["levels"].items():
                self.add_level()
                if self.levels:
                    self.levels[-1]["name_input"].setText(name)
                    if key in level_boundaries and self.levels[-1].get("boundary"):
                        self.levels[-1]["boundary"].setValue(level_boundaries[key])
        
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
                for level_data in self.levels:
                    level_key = level_data["key"]
                    if level_key in scale_data["bounds_inputs"]:
                        scale_data["bounds_inputs"][level_key].setValue(
                            level_data["boundary"].value()
                        )
                        if "bounds_labels" in scale_data:
                            self._update_bounds_labels(scale_data, scale_data["bounds_labels"])
                            
    def _show_error_message(self, title, message):
        """Показывает ошибку с кастомной SVG иконкой"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # ← Заменяем иконку на кастомную SVG
        icon_label = QLabel()
        icon_pixmap = QPixmap("resources/icons/alert-triangle.svg")  # ← Твоя SVG иконка
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(48, 48, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation))
        else:
            # ← Фолбэк на стандартную иконку если файл не найден
            icon_label.setPixmap(self.style().standardIcon(
                QMessageBox.Style.Warning).pixmap(48, 48))
        
        # ← Добавляем иконку в layout QMessageBox
        layout = msg_box.layout()
        layout.addWidget(icon_label, 0, 0, 1, 1, 
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        msg_box.exec()
        
    def _save_debug_config(self, scales_config, level_order, level_ru, answer_weights):
        """Сохраняет конфигурацию в JSON файл для отладки"""
        import json
        from datetime import datetime
        from pathlib import Path
        
        # Формируем полную структуру
        debug_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scales_config": scales_config,
            "level_order": level_order,
            "level_ru": level_ru,
            "answer_weights": answer_weights
        }
        
        # Сохраняем в файл
        output_path = Path("debug_config.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        
        # Выводим в консоль для быстрой проверки
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