# ui/main_window.py
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QStackedWidget, QLabel, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.components.nav_button import NavButton
from ui.components.upload_widget import UploadWidget
from ui.components.results_widget import ResultsWidget
from ui.components.history_widget import HistoryWidget


# Параметры навигационной панели
NAV_PANEL_PARAMS = {
    'sidebar_width': 550,
    'sidebar_height': 88,
    'sidebar_padding_left': 32,
    'sidebar_padding_right': 32,
    'btn_spacing': 20,
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Psychoanalyst")
        self.setMinimumSize(1200, 800)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        central_widget.setStyleSheet("background-color: #F5F5F5;")

        # === ГОРИЗОНТАЛЬНАЯ НАВИГАЦИОННАЯ ПАНЕЛЬ ===
        nav_container = QWidget()
        nav_container.setFixedSize(NAV_PANEL_PARAMS['sidebar_width'], NAV_PANEL_PARAMS['sidebar_height'])
        nav_container.setObjectName("nav_container")

        # Стиль панели: белый фон, скругленные углы
        nav_container.setStyleSheet("""
            #nav_container {
                background-color: #FFFFFF;
                border-radius: 44px;
            }
        """)

        # Тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 30))
        nav_container.setGraphicsEffect(shadow)

        # Горизонтальный layout для кнопок
        nav_horizontal_layout = QHBoxLayout()
        nav_horizontal_layout.setContentsMargins(
            NAV_PANEL_PARAMS['sidebar_padding_left'],
            0,
            NAV_PANEL_PARAMS['sidebar_padding_right'],
            0
        )
        nav_horizontal_layout.setSpacing(NAV_PANEL_PARAMS['btn_spacing'])
        nav_horizontal_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_container.setLayout(nav_horizontal_layout)

        # Кнопки
        self.nav_buttons = []
        btn_data = [
            ("resources/icons/upload.svg", "Загрузка"),
            ("resources/icons/chart-line.svg", "Результаты"),
            ("resources/icons/history.svg", "История")
        ]
        for icon, text in btn_data:
            btn = NavButton(icon, text)
            btn.setStyleSheet("background-color: transparent")
            btn.setObjectName(f"nav_{text}")
            btn.clicked.connect(lambda b=btn, t=text: self.switch_to_tab(b, t))
            nav_horizontal_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # Устанавливаем активной первую кнопку
        self.nav_buttons[0].setChecked(True)

        main_layout.addWidget(nav_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        # === СТЕК ВИДЖЕТОВ ===
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Создаём страницы
        self.upload_tab = UploadWidget()
        self.results_tab = ResultsWidget()
        self.history_tab = HistoryWidget()

        # Настройка размера шрифта и иконок кнопок навигации
        self.results_tab.set_nav_font_size(14)
        self.results_tab.set_nav_icon_size(40)

        self.stacked_widget.addWidget(self.upload_tab)
        self.stacked_widget.addWidget(self.results_tab)
        self.stacked_widget.addWidget(self.history_tab)

        # Подключаем сигналы
        self.upload_tab.file_loaded.connect(self.on_file_loaded)
        self.upload_tab.settings_requested.connect(self.open_settings_dialog)
        
        print("Nav buttons created:", len(self.nav_buttons))
        print("Nav container size:", nav_container.size())
        print("Nav container layout:", nav_container.layout())
        print("First button visible:", self.nav_buttons[0].isVisible())
        
        self.current_config = None

    def switch_to_tab(self, button: NavButton, tab_name: str):
        """Переключает вкладку по нажатию на кнопку навигации."""
        for btn in self.nav_buttons:
            btn.setChecked(False)
        button.setChecked(True)

        if tab_name == "Загрузка":
            self.stacked_widget.setCurrentWidget(self.upload_tab)
        elif tab_name == "Результаты":
            self.stacked_widget.setCurrentWidget(self.results_tab)
        elif tab_name == "История":
            self.stacked_widget.setCurrentWidget(self.history_tab)

    def on_file_loaded(self, df):
        """Обработчик загрузки файла."""
        pass

    def open_settings_dialog(self):
        from ui.components.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.config_saved.connect(self.on_config_saved)
        dialog.exec()

    def on_config_saved(self, scales_config, level_order, level_ru, answer_weights):
        # Сохраняем конфигурацию
        self.current_config = {
            "scales_config": scales_config,
            "level_order": level_order,
            "level_ru": level_ru,
            "answer_weights": answer_weights
        }
        # Передаём в upload_widget
        self.upload_tab.set_config(self.current_config)