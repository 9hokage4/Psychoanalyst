# ui/components/settings_dialog.py
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QCheckBox, QGroupBox, QScrollArea, QWidget,
    QLineEdit, QMessageBox, QTabWidget, QFrame, QGridLayout,
    QSizePolicy
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from pathlib import Path
from utils.profile_manager import ProfileManager
from ui.components.profile_dialog import ProfileDialog


class SettingsDialog(QDialog):
    config_saved = pyqtSignal(dict, dict, list, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Настройка теста")
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
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        self.basic_tab = self._create_basic_tab()
        # ← Добавляем иконки во вкладки
        self.tabs.addTab(self.basic_tab, QIcon("resources/icons/cog.svg"), "Основные параметры")
        
        self.levels_tab = self._create_levels_tab()
        self.tabs.addTab(self.levels_tab, QIcon("resources/icons/chart-line.svg"), "Уровни показателей")
        
        self.scales_tab = self._create_scales_tab()
        self.tabs.addTab(self.scales_tab, QIcon("resources/icons/charts.svg"), "Шкалы")
        
        self.weights_tab = self._create_weights_tab()
        self.tabs.addTab(self.weights_tab, QIcon("resources/icons/scale.svg"), "Веса ответов")
        
        main_layout.addWidget(self.tabs)
        
                # === Кнопки ===
        btn_frame = QFrame()
        btn_frame.setStyleSheet("QFrame { background-color: #F8F9FA; border-top: 1px solid #DEE2E6; padding: 10px; }")
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 15, 20, 15)

        self.profile_btn = QPushButton(" Профили")
        self.profile_btn.setObjectName("btn_profile")
        self.profile_btn.setIcon(QIcon("resources/icons/folder.svg"))
        self.profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #5B8DBE;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4A7BA7;
            }
        """)
        self.profile_btn.clicked.connect(self.open_profile_dialog)
        btn_layout.addWidget(self.profile_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton(" Сохранить")
        self.save_btn.setObjectName("btn_save")
        self.save_btn.setIcon(QIcon("resources/icons/save.svg"))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6BBF8A;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 30px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5AA878;
            }
        """)
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton(" Отмена")
        self.cancel_btn.setObjectName("btn_cancel")
        self.cancel_btn.setIcon(QIcon("resources/icons/close.svg"))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F8F9FA;
                color: #212529;
                border: 2px solid #DEE2E6;
                border-radius: 6px;
                padding: 10px 30px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E9ECEF;
                border-color: #ADB5BD;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        btn_frame.setLayout(btn_layout)
        main_layout.addWidget(btn_frame)
        
        self.setLayout(main_layout)
    
    def _create_basic_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        title = QLabel("📋 Основные параметры теста")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        layout.addWidget(title)
        
        grid = QGridLayout()
        grid.setSpacing(20)
        
        grid.addWidget(QLabel("Количество вопросов в тесте:"), 0, 0)
        self.questions_spin = QSpinBox()
        self.questions_spin.setRange(1, 1000)
        self.questions_spin.setValue(10)
        self.questions_spin.setFixedWidth(150)
        self.questions_spin.setStyleSheet("""
            QSpinBox {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
            QSpinBox:focus {
                border-color: #4a90d9;
            }
        """)
        self.questions_spin.valueChanged.connect(self.on_questions_changed)
        grid.addWidget(self.questions_spin, 0, 1)
        
        grid.addWidget(QLabel("Количество вариантов ответа:"), 1, 0)
        self.answers_spin = QSpinBox()
        self.answers_spin.setRange(2, 10)
        self.answers_spin.setValue(5)
        self.answers_spin.setFixedWidth(150)
        self.answers_spin.setStyleSheet("""
            QSpinBox {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
            QSpinBox:focus {
                border-color: #4a90d9;
            }
        """)
        self.answers_spin.valueChanged.connect(self.on_answers_changed)
        grid.addWidget(self.answers_spin, 1, 1)
        
        layout.addLayout(grid)
        
        shared_frame = QFrame()
        shared_frame.setStyleSheet("QFrame { background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 15px; }")
        shared_layout = QHBoxLayout()
        
        self.shared_checkbox = QCheckBox("Вопросы для различных шкал одинаковы")
        self.shared_checkbox.setChecked(False)
        self.shared_checkbox.setStyleSheet("font-size: 13px; color: #212529;")
        self.shared_checkbox.setToolTip("Если активно - один вопрос может относиться к нескольким шкалам")
        shared_layout.addWidget(self.shared_checkbox)
        shared_layout.addStretch()
        shared_frame.setLayout(shared_layout)
        layout.addWidget(shared_frame)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_levels_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("📊 Уровни показателей")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        layout.addWidget(title)
        
        info_label = QLabel("💡 Добавьте уровни показателей (например: Низкий, Средний, Высокий)")
        info_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(info_label)
        
        # ← ЧЕКБОКС "Границы для шкал совпадают"
        self.same_bounds_checkbox = QCheckBox("Границы для шкал совпадают")
        self.same_bounds_checkbox.setChecked(True)  # ← По умолчанию активен
        self.same_bounds_checkbox.setStyleSheet("font-size: 14px; font-weight: bold; color: #212529;")
        self.same_bounds_checkbox.stateChanged.connect(self.on_same_bounds_changed)
        layout.addWidget(self.same_bounds_checkbox)
        
        add_btn = QPushButton("Добавить уровень")
        add_btn.setFixedHeight(45)
        add_btn.setObjectName("btn_add_level")
        add_btn.setIcon(QIcon("resources/icons/plus.svg"))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
        """)
        add_btn.clicked.connect(self.add_level)
        layout.addWidget(add_btn)
        
        self.levels_container = QWidget()
        self.levels_layout = QVBoxLayout()
        self.levels_layout.setSpacing(15)
        self.levels_container.setLayout(self.levels_layout)
        
        levels_scroll = QScrollArea()
        levels_scroll.setWidgetResizable(True)
        levels_scroll.setWidget(self.levels_container)
        levels_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        levels_scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout.addWidget(levels_scroll, 1)
        
        tab.setLayout(layout)
        return tab
    
    def _create_scales_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("📈 Шкалы теста")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        layout.addWidget(title)
        
        info_label = QLabel("💡 Добавьте шкалы и укажите вопросы для каждой")
        info_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(info_label)
        
        add_btn = QPushButton("Добавить шкалу")
        add_btn.setFixedHeight(45)
        add_btn.setObjectName("btn_add_scale")
        add_btn.setIcon(QIcon("resources/icons/plus.svg"))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
        """)
        add_btn.clicked.connect(self.add_scale)
        layout.addWidget(add_btn)
        
        self.scales_container = QWidget()
        self.scales_layout = QVBoxLayout()
        self.scales_layout.setSpacing(15)
        self.scales_container.setLayout(self.scales_layout)
        
        scales_scroll = QScrollArea()
        scales_scroll.setWidgetResizable(True)
        scales_scroll.setWidget(self.scales_container)
        scales_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scales_scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout.addWidget(scales_scroll, 1)
        
        tab.setLayout(layout)
        return tab
    
    def _create_weights_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        title = QLabel("⚖️ Веса ответов")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        layout.addWidget(title)
        
        self.same_weights_checkbox = QCheckBox("Одинаковые веса для всех ответов")
        self.same_weights_checkbox.setChecked(False)
        self.same_weights_checkbox.setStyleSheet("font-size: 14px; font-weight: bold; color: #212529;")
        self.same_weights_checkbox.stateChanged.connect(self.on_weights_checkbox_changed)
        layout.addWidget(self.same_weights_checkbox)
        
        self.weights_container = QFrame()
        self.weights_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 12px;
                padding: 20px;
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
        
        # === РАМКА ===
        level_frame = QFrame()
        level_frame.setFixedHeight(52)  # ← Чуть увеличил высоту
        level_frame.setObjectName("level_frame")
        
        # === LAYOUT ===
        level_layout = QHBoxLayout()
        level_layout.setContentsMargins(15, 6, 15, 6)
        level_layout.setSpacing(8)
        
        # 1. Номер уровня
        level_num = QLabel(f"{level_index}.")
        level_num.setObjectName("level_num")
        level_num.setFixedWidth(30)
        level_num.setFixedHeight(28)
        level_num.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        level_layout.addWidget(level_num)
        
        # 2. Метка "Название:"
        label_title = QLabel("Название:")
        label_title.setObjectName("level_label")
        label_title.setFixedWidth(80)
        label_title.setFixedHeight(28)
        label_title.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        level_layout.addWidget(label_title)
        
        # 3. Поле ввода названия
        name_input = QLineEdit()
        name_input.setObjectName("level_name_input")
        name_input.setPlaceholderText("например, 'Низкий'")
        name_input.setFixedWidth(200)
        name_input.setFixedHeight(32)
        name_input.textChanged.connect(self._update_level_names_in_scales)
        level_layout.addWidget(name_input)
        
        # 4. Метка "Граница (баллов):"
        boundary_label = QLabel("Граница (баллов):")
        boundary_label.setObjectName("level_label")
        boundary_label.setFixedWidth(110)
        boundary_label.setFixedHeight(28)
        boundary_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        level_layout.addWidget(boundary_label)
        
        # 5. SpinBox
        boundary_spin = QSpinBox()
        boundary_spin.setObjectName("level_boundary_spin")
        boundary_spin.setRange(0, 1000)
        boundary_spin.setValue(level_index * 25)
        boundary_spin.setFixedWidth(55)
        boundary_spin.setFixedHeight(32)
        boundary_spin.valueChanged.connect(self._update_bounds_in_scales)
        level_layout.addWidget(boundary_spin)
        
        # 6. Подсказка (иконка) - ИСПРАВЛЕНО
        hint_icon = QLabel()
        hint_icon.setObjectName("hint_icon")
        hint_icon.setText("")
        hint_icon.setToolTip("Верхняя граница уровня")
        hint_icon.setMinimumSize(28, 28)
        hint_icon.setMaximumSize(28, 28)
        hint_icon.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # ← Загружаем иконку правильно
        icon_pixmap = QPixmap("resources/icons/lightbulb.svg")
        print(f"Pixmap загружен: {not icon_pixmap.isNull()}")
        print(f"Размер pixmap: {icon_pixmap.size()}")
        if not icon_pixmap.isNull():
            hint_icon.setPixmap(icon_pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            hint_icon.setText("💡")  # ← Фолбэк если SVG не загрузился
            hint_icon.setFixedWidth(30)
        
        hint_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_icon.setStyleSheet("background-color: transparent; padding: 0px; margin: 0px;")
        print(f"hint_icon создан: {hint_icon}")
        print(f"Размер: {hint_icon.size()}")
        level_layout.addWidget(hint_icon)
        
        # 7. Растяжка
        level_layout.addStretch()
        
        # 8. Кнопка удаления - ИСПРАВЛЕНО
        remove_btn = QPushButton(" Удалить")
        remove_btn.setObjectName("btn_delete_level")
        remove_btn.setIcon(QIcon("resources/icons/trash.svg"))
        remove_btn.setIconSize(QSize(16, 16))
        remove_btn.setFixedWidth(100)
        remove_btn.setFixedHeight(32)  # ← Увеличил высоту
        remove_btn.setStyleSheet("""
            QPushButton#btn_delete_level {
                background-color: #E07B7B;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#btn_delete_level:hover {
                background-color: #C96A6A;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_level(level_frame, level_key))
        level_layout.addWidget(remove_btn)
        
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
            "num_label": level_num
        })
        
        self.on_same_bounds_changed()
        
    def on_same_bounds_changed(self):
        """Обработчик изменения чекбокса 'Границы для шкал совпадают'"""
        show_bounds = self.same_bounds_checkbox.isChecked()
        
        # Показываем/скрываем поля границ и подсказки во всех уровнях
        for level_data in self.levels:
            level_data["boundary_label"].setVisible(show_bounds)
            level_data["boundary"].setVisible(show_bounds)
            level_data["hint_label"].setVisible(show_bounds)
        
        # ← Обновляем шкалы только если они существуют
        for scale_data in self.scales:
            for level_key, bound_spin in scale_data["bounds_inputs"].items():
                # Блокируем/разблокируем поля в шкалах
                bound_spin.setEnabled(not show_bounds)
            
            # Если чекбокс активен — копируем границы из уровней
            if show_bounds:
                for level_data in self.levels:
                    level_key = level_data["key"]
                    # ← ПРОВЕРКА: существует ли ключ в шкале
                    if level_key in scale_data["bounds_inputs"]:
                        scale_data["bounds_inputs"][level_key].setValue(
                            level_data["boundary"].value()
                        )
            
            # Обновляем label с диапазонами
            if "bounds_labels" in scale_data:
                self._update_bounds_labels(scale_data, scale_data["bounds_labels"])
    
    def _update_scales_with_common_bounds(self):
        """Обновляет все шкалы с общими границами из уровней"""
        for scale_data in self.scales:
            for i, level_data in enumerate(self.levels):
                level_key = level_data["key"]
                if level_key in scale_data["bounds_inputs"]:
                    # Копируем значение из уровня в шкалу
                    scale_data["bounds_inputs"][level_key].setValue(
                        level_data["boundary"].value()
                    )
            
            # Обновляем label с диапазонами
            self._update_bounds_labels(scale_data, scale_data["bounds_labels"])
    
    def remove_level(self, widget, level_key):
        if len(self.levels) <= 1:
            QMessageBox.warning(self, "Ошибка", "Должен быть хотя бы один уровень")
            return
        
        widget.deleteLater()
        self.level_order.remove(level_key)
        self.levels = [l for l in self.levels if l["key"] != level_key]
        
        self._update_level_numbers()
    
    def _parse_questions_input(self, text, validate=True):
        """Парсит ввод вопросов с валидацией"""
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
        """Обновляет выбранные вопросы при изменении текстового ввода"""
        selected, errors = self._parse_questions_input(scale_data["questions_input"].text(), validate=True)
        scale_data["selected_questions"] = set(selected)
        
        if errors:
            scale_data["questions_input"].setStyleSheet("""
                QLineEdit {
                    border: 2px solid #dc3545;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 13px;
                    background-color: #fff5f5;
                    color: #212529;
                }
                QLineEdit:focus {
                    border-color: #dc3545;
                }
            """)
        else:
            scale_data["questions_input"].setStyleSheet("""
                QLineEdit {
                    border: 2px solid #dee2e6;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 13px;
                    background-color: white;
                    color: #212529;
                }
                QLineEdit:focus {
                    border-color: #4a90d9;
                }
            """)
    
    def add_scale(self):
        if len(self.levels) == 0:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте уровни показателей на вкладке 'Уровни показателей'")
            self.tabs.setCurrentIndex(1)
            return
        
        scale_index = len(self.scales) + 1
        
        scale_frame = QFrame()
        scale_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        scale_layout = QVBoxLayout()
        scale_layout.setContentsMargins(15, 15, 15, 15)
        scale_layout.setSpacing(15)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("<b style='color: #4a90d9; font-size: 14px;'>Название шкалы:</b>"))
        name_input = QLineEdit()
        name_input.setPlaceholderText("например, 'Тревожность'")
        name_input.setFixedWidth(300)
        name_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                background-color: white;
                color: #212529;
            }
            QLineEdit:focus {
                border-color: #4a90d9;
            }
        """)
        name_layout.addWidget(name_input)
        name_layout.addStretch()
        scale_layout.addLayout(name_layout)
        
        questions_group = QGroupBox("Вопросы для этой шкалы:")
        questions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #4a90d9;
            }
        """)
        questions_layout = QVBoxLayout()
        questions_layout.setSpacing(10)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Введите номера вопросов:"))
        self.questions_input = QLineEdit()
        self.questions_input.setPlaceholderText("Пример: 1-20, 25, 30-40")
        self.questions_input.setFixedWidth(500)
        self.questions_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                background-color: white;
                color: #212529;
            }
            QLineEdit:focus {
                border-color: #4a90d9;
            }
        """)
        self.questions_input.textChanged.connect(lambda: self._on_questions_input_changed(scale_data))
        input_layout.addWidget(self.questions_input)
        questions_layout.addLayout(input_layout)
        
        hint_label = QLabel("💡 Формат: отдельные числа (1, 5, 10) или диапазоны (1-20, 30-40)")
        hint_label.setStyleSheet("color: #666; font-size: 12px; font-style: italic;")
        questions_layout.addWidget(hint_label)
        
        questions_group.setLayout(questions_layout)
        scale_layout.addWidget(questions_group)
        
        bounds_group = QGroupBox("Границы уровней для шкалы:")
        bounds_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #4a90d9;
            }
        """)
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
            
            range_label = QLabel(f"<b>{range_text}</b>")
            range_label.setObjectName(f"range_label_{level_data['key']}")
            bounds_layout.addWidget(range_label, row, col * 2)
            bounds_labels[level_data["key"]] = range_label
            
            bound_spin = QSpinBox()
            bound_spin.setRange(0, 1000)
            bound_spin.setValue((i + 1) * 25)
            bound_spin.setFixedWidth(80)
            bound_spin.setStyleSheet("""
                QSpinBox {
                    border: 2px solid #dee2e6;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 13px;
                    background-color: white;
                    color: #212529;
                }
                QSpinBox:focus {
                    border-color: #4a90d9;
                }
            """)
            
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
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
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
        """Динамически обновляет диапазоны в label при изменении границ"""
        previous_boundary = 0
        
        for i, level_data in enumerate(self.levels):
            level_key = level_data["key"]
            level_name = level_data["name_input"].text()
            if not level_name:
                level_name = f"Уровень {self.levels.index(level_data) + 1}"
            
            # ← ПРОВЕРКА: существует ли ключ в шкале
            if level_key not in scale_data["bounds_inputs"]:
                continue
            
            bound_spin = scale_data["bounds_inputs"][level_key]
            current_boundary = bound_spin.value()
            
            # Формируем диапазон
            if i == 0:
                range_text = f"{level_name} (0-{current_boundary}):"
            else:
                range_text = f"{level_name} ({previous_boundary + 1}-{current_boundary}):"
            
            # Обновляем label
            if level_key in bounds_labels:
                bounds_labels[level_key].setText(f"<b>{range_text}</b>")
            
            previous_boundary = current_boundary
    
    def remove_scale(self, widget):
        if len(self.scales) <= 1:
            QMessageBox.warning(self, "Ошибка", "Должна быть хотя бы одна шкала")
            return
        
        for scale_data in self.scales:
            if scale_data["widget"] == widget:
                self.all_selected_questions -= scale_data["selected_questions"]
                break
        
        self.scales = [s for s in self.scales if s["widget"] != widget]
        widget.deleteLater()
        
    def _update_level_numbers(self):
        """Обновляет номера уровней после удаления"""
        for i, level_data in enumerate(self.levels):
            if "num_label" in level_data:
                level_data["num_label"].setText(
                    f"<b style='color: #4a90d9;'>{i + 1}.</b>"
                )
    
    def on_questions_changed(self, value):
        self._recreate_scales()
    
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
            self.weights_layout.addWidget(QLabel("<b>Вес для всех ответов:</b>"), 0, 0)
            self.single_weight_spin = QSpinBox()
            self.single_weight_spin.setRange(1, 100)
            self.single_weight_spin.setValue(1)
            self.single_weight_spin.setStyleSheet("""
                QSpinBox {
                    border: 2px solid #dee2e6;
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 14px;
                    background-color: white;
                    color: #212529;
                }
                QSpinBox:focus {
                    border-color: #4a90d9;
                }
            """)
            self.weights_layout.addWidget(self.single_weight_spin, 0, 1)
        else:
            num_answers = self.answers_spin.value()
            self.weight_spins = {}
            
            for i in range(1, num_answers + 1):
                row = (i - 1) // 5
                col = (i - 1) % 5
                
                label = QLabel(f"<b>Ответ {i}:</b>")
                label.setStyleSheet("font-size: 13px; color: #212529;")
                self.weights_layout.addWidget(label, row, col * 2)
                
                weight_spin = QSpinBox()
                weight_spin.setRange(1, 100)
                weight_spin.setValue(i)
                weight_spin.setFixedWidth(80)
                weight_spin.setStyleSheet("""
                    QSpinBox {
                        border: 2px solid #dee2e6;
                        border-radius: 6px;
                        padding: 10px;
                        font-size: 14px;
                        background-color: white;
                        color: #212529;
                    }
                    QSpinBox:focus {
                        border-color: #4a90d9;
                    }
                """)
                self.weights_layout.addWidget(weight_spin, row, col * 2 + 1)
                self.weight_spins[i] = weight_spin
        
        for row in range((self.answers_spin.value() - 1) // 5 + 1):
            self.weights_layout.setColumnStretch(row * 2 + 10, 1)
    
    def save_config(self):
        if self.questions_spin.value() < 1:
            QMessageBox.warning(self, "Ошибка", "Количество вопросов должно быть больше 0")
            self.tabs.setCurrentIndex(0)
            return
        
        if self.answers_spin.value() < 2:
            QMessageBox.warning(self, "Ошибка", "Количество ответов должно быть минимум 2")
            self.tabs.setCurrentIndex(0)
            return
        
        if len(self.levels) < 1:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы один уровень показателей")
            self.tabs.setCurrentIndex(1)
            return
        
        for i, level_data in enumerate(self.levels):
            name = level_data["name_input"].text().strip()
            if not name:
                QMessageBox.warning(self, "Ошибка", f"Уровень {i + 1} не имеет названия")
                self.tabs.setCurrentIndex(1)
                level_data["name_input"].setFocus()
                return
        
        if len(self.scales) < 1:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну шкалу")
            self.tabs.setCurrentIndex(2)
            return
        
        for i, scale_data in enumerate(self.scales):
            name = scale_data["name_input"].text().strip()
            if not name:
                QMessageBox.warning(self, "Ошибка", f"Шкала {i + 1} не имеет названия")
                self.tabs.setCurrentIndex(2)
                scale_data["name_input"].setFocus()
                return
            
            selected_questions, errors = self._parse_questions_input(
                scale_data["questions_input"].text(),
                validate=True
            )
            
            if errors:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    f"Шкала '{name}':\n" + "\n".join(errors)
                )
                self.tabs.setCurrentIndex(2)
                scale_data["questions_input"].setFocus()
                return
            
            if not selected_questions:
                QMessageBox.warning(self, "Ошибка", f"Шкала '{name}': не выбраны вопросы")
                self.tabs.setCurrentIndex(2)
                return
            
            scale_data["selected_questions"] = set(selected_questions)
        
        scales_config = {}
        for scale_data in self.scales:
            name = scale_data["name_input"].text().strip()
            selected_questions = sorted(list(scale_data["selected_questions"]))
            
            scales_config[name] = {
                "title_ru": name,
                "qnums": selected_questions,
                "bounds": {k: v.value() for k, v in scale_data["bounds_inputs"].items()}
            }
        
        levels_config = {}
        for level_data in self.levels:
            name = level_data["name_input"].text().strip()
            levels_config[level_data["key"]] = name
        
        answer_weights = {}
        if self.same_weights_checkbox.isChecked():
            weight = self.single_weight_spin.value()
            for i in range(1, self.answers_spin.value() + 1):
                answer_weights[i] = weight
        else:
            for i, spin in self.weight_spins.items():
                answer_weights[i] = spin.value()
        
        self.config_saved.emit(scales_config, levels_config, self.level_order, answer_weights)
        self.accept()
    
    def open_profile_dialog(self):
        """Открывает диалог управления профилями"""
        # Собираем текущую конфигурацию для сохранения
        self.current_config = self._get_current_config()
        
        dialog = ProfileDialog(self, self.current_config)
        dialog.profile_loaded.connect(self.on_profile_loaded)
        dialog.exec()

    def _get_current_config(self):
        """Собирает текущую конфигурацию из полей диалога"""
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
        level_boundaries = {}  # ← Сохраняем границы уровней
        for level_data in self.levels:
            name = level_data["name_input"].text().strip()
            if name:
                levels[level_data["key"]] = name
                # ← Сохраняем границу если есть
                if level_data.get("boundary"):
                    level_boundaries[level_data["key"]] = level_data["boundary"].value()
        
        # Веса ответов
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
            "level_boundaries": level_boundaries,  # ← Границы уровней
            "level_order": self.level_order,
            "answer_weights": answer_weights,
            "questions_count": self.questions_spin.value(),
            "answers_count": self.answers_spin.value(),
            "shared_questions": self.shared_checkbox.isChecked(),
            "same_bounds": self.same_bounds_checkbox.isChecked() if hasattr(self, 'same_bounds_checkbox') else False
        }

    def on_profile_loaded(self, config):
        """Загружает профиль в диалог настроек"""
        # ← 1. Сначала загружаем чекбокс "Границы для шкал совпадают"
        if "same_bounds" in config:
            self.same_bounds_checkbox.setChecked(config["same_bounds"])
        
        # Основные параметры
        if "questions_count" in config:
            self.questions_spin.setValue(config["questions_count"])
        if "answers_count" in config:
            self.answers_spin.setValue(config["answers_count"])
        if "shared_questions" in config:
            self.shared_checkbox.setChecked(config["shared_questions"])
        
        # ← 2. Уровни (с границами)
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
                    # Устанавливаем границу из профиля
                    if key in level_boundaries and self.levels[-1].get("boundary"):
                        self.levels[-1]["boundary"].setValue(level_boundaries[key])
        
        # ← 3. Шкалы
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
                    
                    # Вопросы
                    if "qnums" in scale_config:
                        questions_text = ", ".join(map(str, scale_config["qnums"]))
                        new_scale["questions_input"].setText(questions_text)
                        new_scale["selected_questions"] = set(scale_config["qnums"])
                    
                    # Границы
                    if "bounds" in scale_config:
                        for key, value in scale_config["bounds"].items():
                            if key in new_scale["bounds_inputs"]:
                                new_scale["bounds_inputs"][key].setValue(value)
        
        # ← 4. Веса ответов
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
        
        # ← 5. Обновляем label с диапазонами (только после создания всех шкал)
        for scale_data in self.scales:
            if "bounds_labels" in scale_data:
                self._update_bounds_labels(scale_data, scale_data["bounds_labels"])
        
        QMessageBox.information(self, "Успех", "Профиль загружен!")
        
    def _update_level_names_in_scales(self):
        """Обновляет названия уровней во всех шкалах"""
        for scale_data in self.scales:
            self._update_bounds_labels(scale_data, scale_data["bounds_labels"])

    def _update_bounds_in_scales(self):
        """Обновляет границы во всех шкалах при изменении в уровнях"""
        # Обновляем только если чекбокс "Границы совпадают" активен
        if hasattr(self, 'same_bounds_checkbox') and self.same_bounds_checkbox.isChecked():
            for scale_data in self.scales:
                # Копируем границы из уровней в шкалы
                for level_data in self.levels:
                    level_key = level_data["key"]
                    # ← ПРОВЕРКА: существует ли ключ в шкале
                    if level_key in scale_data["bounds_inputs"]:
                        scale_data["bounds_inputs"][level_key].setValue(
                            level_data["boundary"].value()
                        )
                
                # Обновляем label с диапазонами
                if "bounds_labels" in scale_data:
                    self._update_bounds_labels(scale_data, scale_data["bounds_labels"])