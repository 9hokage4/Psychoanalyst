# -*- coding: utf-8 -*-
# ui/main_window.py
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QStackedWidget, QLabel, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon
import pandas as pd

from ui.components.nav_button import NavButton
from ui.components.upload_widget import UploadWidget
from ui.components.results_widget import ResultsWidget
from ui.components.settings_widget import SettingsWidget  # исправлен импорт
from utils.resources import get_icon_path

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
        self.setWindowIcon(QIcon(get_icon_path("app_icon")))

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
        nav_container.setStyleSheet("""
            #nav_container {
                background-color: #FFFFFF;
                border-radius: 44px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 30))
        nav_container.setGraphicsEffect(shadow)

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
    (get_icon_path("upload.svg"), "Загрузка"),
    (get_icon_path("settings.svg"), "Настройки"),
    (get_icon_path("result.svg"), "Результаты")
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
        self.settings_tab = SettingsWidget()
        self.results_tab = ResultsWidget()

        # Настройка результатов
        self.results_tab.set_nav_font_size(14)
        self.results_tab.set_nav_icon_size(40)

        self.stacked_widget.addWidget(self.upload_tab)
        self.stacked_widget.addWidget(self.settings_tab)
        self.stacked_widget.addWidget(self.results_tab)

        # Подключаем сигналы
        self.upload_tab.file_loaded.connect(self.on_file_loaded)
        self.upload_tab.settings_requested.connect(self.open_settings_tab)  # теперь переключает на вкладку
        self.upload_tab.processing_finished.connect(self.on_processing_finished)
        self.upload_tab.data_cleared.connect(self.on_data_cleared)

        self.settings_tab.config_saved.connect(self.on_config_saved)

        self.current_config = None

    def switch_to_tab(self, button: NavButton, tab_name: str):
        """Переключает вкладку по нажатию на кнопку навигации."""
        for btn in self.nav_buttons:
            btn.setChecked(False)
        button.setChecked(True)

        if tab_name == "Загрузка":
            self.stacked_widget.setCurrentWidget(self.upload_tab)
        elif tab_name == "Настройки":
            self.stacked_widget.setCurrentWidget(self.settings_tab)
        elif tab_name == "Результаты":
            self.stacked_widget.setCurrentWidget(self.results_tab)

    def open_settings_tab(self):
        """Переключает на вкладку Настройки."""
        self.switch_to_tab(self.nav_buttons[1], "Настройки")

    def on_file_loaded(self, df):
        pass

    def on_processing_finished(self, table_df, charts_data, summary_data, success, message):
        if success:
            self.switch_to_tab(self.nav_buttons[2], "Результаты")
            self.results_tab.set_data(table_df, charts_data, summary_data)
        else:
            # Обработка ошибки
            pass

    def on_data_cleared(self):
        self.results_tab.clear_data()

    def on_config_saved(self, full_config, profile_name):
        """Сохраняет конфигурацию, полученную из SettingsWidget."""
        self.current_config = full_config
        self.upload_tab.set_config(full_config)
        # Опционально: переключиться на вкладку Загрузка после сохранения
        self.switch_to_tab(self.nav_buttons[0], "Загрузка")