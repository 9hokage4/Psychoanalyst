# -*- coding: utf-8 -*-
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
        self.upload_tab.processing_finished.connect(self.on_processing_finished)
        self.upload_tab.data_cleared.connect(self.on_data_cleared)

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

    def on_processing_finished(self, result_df, success, message):
        """Обработчик завершения обработки данных."""
        if success:
            # Переключаемся на вкладку результатов
            self.switch_to_tab(self.nav_buttons[1], "Результаты")
            # Передаём данные в results_tab
            self.results_tab.set_data(result_df)

    def on_data_cleared(self):
        """Обработчик очистки данных (при нажатии 'Отмена')."""
        # Очищаем таблицу результатов
        self.results_tab.clear_data()

    def open_settings_dialog(self):
        from ui.components.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self, self.current_config)
        dialog.config_saved.connect(self.on_config_saved)
        dialog.profile_loaded_with_name.connect(self.on_profile_loaded)
        dialog.exec()

    def on_profile_loaded(self, profile_name, config):
        """Обработчик загрузки профиля с именем."""
        self.current_config = config
        self.upload_tab.set_config(config)
        self.upload_tab.config_summary.set_profile_name(profile_name)
        self.upload_tab.config_summary.update_config_from_dict(config)

    def on_config_saved(self, full_config, profile_name):
        """Обработчик сохранения конфигурации."""
        # Сохраняем полную конфигурацию (всегда, даже без профиля)
        self.current_config = full_config
        # Передаём в upload_widget
        self.upload_tab.set_config(full_config)
        # Обновляем имя профиля
        self.upload_tab.config_summary.set_profile_name(profile_name if profile_name else "Настройки")