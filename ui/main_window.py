# ui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QStackedWidget, QLabel, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QIcon, QColor

from ui.components.upload_widget import UploadWidget
from ui.components.results_widget import ResultsWidget
from ui.components.history_widget import HistoryWidget


class NavButton(QWidget):
    """Кастомная кнопка для горизонтальной навигации (иконка + текст).
       Стилизация полностью через QSS с использованием свойства 'checked'."""
    clicked = pyqtSignal()

    def __init__(self, icon_path: str, text: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(112, 70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = False

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Иконка
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QIcon(icon_path).pixmap(30, 30))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        # Текст
        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setObjectName("nav_text")
        layout.addWidget(self.text_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    # --- Свойство checked для QSS ---
    def get_checked(self) -> bool:
        return self._checked

    def set_checked(self, value: bool):
        if self._checked != value:
            self._checked = value
            # Обновляем динамическое свойство для QSS
            self.setProperty("checked", value)
            # Переприменяем стиль
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()  # гарантируем перерисовку

    checked = pyqtProperty(bool, get_checked, set_checked)

    # Для удобства можно оставить методы setChecked/isChecked
    def setChecked(self, checked: bool):
        self.checked = checked

    def isChecked(self):
        return self.checked


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

        # === ГОРИЗОНТАЛЬНАЯ НАВИГАЦИОННАЯ ПАНЕЛЬ (ОВАЛЬНАЯ) ===
        nav_container = QWidget()
        nav_container.setFixedHeight(88)
        nav_container.setObjectName("nav_container")  # важно для QSS

        # Тень (QSS не умеет, добавляем в коде)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 20))  # rgba(0,0,0,0.08)
        nav_container.setGraphicsEffect(shadow)

        # Вертикальный layout: растяжка сверху прижимает кнопки к низу
        nav_vertical_layout = QVBoxLayout(nav_container)
        nav_vertical_layout.setContentsMargins(0, 0, 0, 0)
        nav_vertical_layout.addStretch()

        # Горизонтальный layout для кнопок
        nav_horizontal_layout = QHBoxLayout()
        nav_horizontal_layout.setContentsMargins(32, 0, 32, 8)   # снизу 8px
        nav_horizontal_layout.setSpacing(20)
        nav_horizontal_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Кнопки
        self.nav_buttons = []
        btn_data = [
            ("resources/icons/upload.svg", "Загрузка"),
            ("resources/icons/chart-line.svg", "Результаты"),
            ("resources/icons/history.svg", "История")
        ]
        for icon, text in btn_data:
            btn = NavButton(icon, text)
            # Даём каждой кнопке уникальный objectName на всякий случай (поможет в отладке)
            btn.setObjectName(f"nav_{text}")
            btn.clicked.connect(lambda b=btn, t=text: self.switch_to_tab(b, t))
            nav_horizontal_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # Устанавливаем активной первую кнопку
        self.nav_buttons[0].setChecked(True)

        nav_vertical_layout.addLayout(nav_horizontal_layout)
        main_layout.addWidget(nav_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        # === СТЕК ВИДЖЕТОВ ===
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Создаём страницы
        self.upload_tab = UploadWidget()
        self.results_tab = ResultsWidget()
        self.history_tab = HistoryWidget()

        self.stacked_widget.addWidget(self.upload_tab)
        self.stacked_widget.addWidget(self.results_tab)
        self.stacked_widget.addWidget(self.history_tab)

        # Подключаем сигналы
        self.upload_tab.file_loaded.connect(self.on_file_loaded)
        self.upload_tab.settings_requested.connect(self.open_settings_dialog)

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

    def on_config_saved(self, scales, level_order, level_ru, answer_weights):
        print("Конфигурация сохранена")
        # TODO: передать конфиг в upload_tab для отображения