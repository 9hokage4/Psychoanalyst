# ui/main_window.py
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QStackedWidget, QLabel, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve, QSize, QPoint
from PyQt6.QtGui import QIcon, QColor, QFont, QPainter, QBrush, QPen, QPainterPath, QPixmap, QImage, qRgba, qAlpha

from ui.components.upload_widget import UploadWidget
from ui.components.results_widget import ResultsWidget
from ui.components.history_widget import HistoryWidget
from utils.fonts import get_font, FontWeights


# Параметры навигации из ТЗ
NAV_PARAMS = {
    # Шрифты
    'font_family': "'Segoe UI', 'Roboto', sans-serif",
    'font_size': 14,
    # Панель
    'sidebar_width': 569,
    'sidebar_height': 88,
    'sidebar_padding_left': 32,
    'sidebar_padding_right': 32,
    'btn_spacing': 20,
    # Иконки
    'icon_size': 30,
    # Выделение
    'highlight_width': 112,
    'highlight_height': 70,
    'highlight_radius_h': 34,
    'highlight_radius_v': 35,
    # Анимация
    'anim_initial_width': 30,
    'anim_initial_height': 25,
    'anim_final_width': 112,
    'anim_final_height': 70,
    'anim_duration_ms': 300,
    # Цвета
    'color_highlight_bg': '#b4d1ee',
    'color_highlight_text': '#0678ea',
    'color_hover_bg': '#F4F4F5',
    'color_hover_text': '#0678ea',
    'color_text_default': '#000000',
    'color_primary': '#3390EC',
    'color_white': '#FFFFFF',
    'color_bg': '#F5F5F5',
}


class NavButton(QWidget):
    """Кастомная кнопка для горизонтальной навигации с анимацией выделения."""
    clicked = pyqtSignal()

    def __init__(self, icon_path: str, text: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(NAV_PARAMS['highlight_width'], NAV_PARAMS['highlight_height'])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = False
        self._hover = False

        # Анимация размера фона
        self._bg_size = QSize(NAV_PARAMS['anim_initial_width'], NAV_PARAMS['anim_initial_height'])
        self.bg_animation = QPropertyAnimation(self, b"bg_size")
        self.bg_animation.setDuration(NAV_PARAMS['anim_duration_ms'])
        self.bg_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Анимация цвета (прозрачность)
        self._bg_opacity = 0.0
        self.opacity_animation = QPropertyAnimation(self, b"bg_opacity")
        self.opacity_animation.setDuration(NAV_PARAMS['anim_duration_ms'])
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Сохраняем путь к иконке (преобразуем в абсолютный)
        self.icon_path = str(Path(icon_path).absolute()) if not Path(icon_path).is_absolute() else icon_path
        self.icon_size = NAV_PARAMS['icon_size']
        
        print(f"NavButton: icon_path={self.icon_path}, exists={Path(self.icon_path).exists()}")

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Иконка
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(self.icon_size, self.icon_size)
        layout.addWidget(self.icon_label)

        # Текст
        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setObjectName("nav_text")
        font = QFont("Genzsch Antiqua", NAV_PARAMS['font_size'])
        font.setWeight(QFont.Weight.Medium)
        self.text_label.setFont(font)
        self.text_label.setStyleSheet("color: #000000;")
        layout.addWidget(self.text_label)

        # Загружаем иконку с цветом по умолчанию
        self._update_icon()
        self._update_colors()

    def _create_colored_icon(self, color: QColor) -> QPixmap:
        """Создает QPixmap из SVG с указанным цветом через QIcon."""
        # Загружаем через QIcon
        icon = QIcon(self.icon_path)
        pixmap = icon.pixmap(self.icon_size, self.icon_size)

        if pixmap.isNull():
            print(f"_create_colored_icon: pixmap is null for {self.icon_path}")
            # Если не удалось загрузить, создаем заглушку
            pixmap = QPixmap(self.icon_size, self.icon_size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(0, 0, self.icon_size, self.icon_size)
            painter.end()
            return pixmap

        # Создаем цветную версию через QImage для попиксельной обработки
        image = pixmap.toImage()
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
        
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixel(x, y)
                alpha = qAlpha(pixel)
                if alpha > 0:
                    # Сохраняем альфа-канал, меняем цвет
                    new_pixel = qRgba(color.red(), color.green(), color.blue(), alpha)
                    image.setPixel(x, y, new_pixel)
        
        return QPixmap.fromImage(image)

    def _update_icon(self):
        """Обновляет иконку с текущим цветом."""
        if self._checked or self._hover:
            color = QColor(NAV_PARAMS['color_highlight_text'])
        else:
            color = QColor(NAV_PARAMS['color_text_default'])
        
        pixmap = self._create_colored_icon(color)
        self.icon_label.setPixmap(pixmap)
        self.icon_label.update()

    def _update_colors(self):
        """Обновление цветов текста и иконки."""
        if self._checked:
            color = NAV_PARAMS['color_highlight_text']
        elif self._hover:
            color = NAV_PARAMS['color_hover_text']
        else:
            color = NAV_PARAMS['color_text_default']

        self.text_label.setStyleSheet(f"color: {color};")
        self._update_icon()
        self.update()

    def paintEvent(self, event):
        """Отрисовка фона с анимацией."""
        if self._bg_size.width() > 0 and self._bg_size.height() > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Создаем путь для скругленного прямоугольника
            path = QPainterPath()
            x = (self.width() - self._bg_size.width()) / 2
            y = (self.height() - self._bg_size.height()) / 2
            path.addRoundedRect(
                x, y,
                self._bg_size.width(),
                self._bg_size.height(),
                NAV_PARAMS['highlight_radius_h'],
                NAV_PARAMS['highlight_radius_v']
            )

            # Цвет фона с учетом прозрачности
            if self._checked:
                # Активное состояние - полный цвет #b4d1ee
                bg_color = QColor(NAV_PARAMS['color_highlight_bg'])
                bg_color.setAlphaF(1.0)
                painter.fillPath(path, QBrush(bg_color))
            elif self._hover:
                # Наведение - полупрозрачный #b4d1ee
                bg_color = QColor(NAV_PARAMS['color_highlight_bg'])
                bg_color.setAlphaF(self._bg_opacity)
                painter.fillPath(path, QBrush(bg_color))

    def enterEvent(self, event):
        self._hover = True
        if not self._checked:
            self._animate_to_hover()
        self._update_colors()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        if not self._checked:
            self._animate_to_default()
        self._update_colors()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _animate_to_active(self):
        """Анимация к активному состоянию."""
        self.bg_animation.stop()
        self.bg_animation.setStartValue(self._bg_size)
        self.bg_animation.setEndValue(QSize(NAV_PARAMS['anim_final_width'], NAV_PARAMS['anim_final_height']))
        self.bg_animation.start()

        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(self._bg_opacity)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

    def _animate_to_default(self):
        """Анимация к состоянию по умолчанию."""
        self.bg_animation.stop()
        self.bg_animation.setStartValue(self._bg_size)
        self.bg_animation.setEndValue(QSize(NAV_PARAMS['anim_initial_width'], NAV_PARAMS['anim_initial_height']))
        self.bg_animation.start()
        
        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(self._bg_opacity)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.start()

    def _animate_to_hover(self):
        """Анимация к состоянию наведения."""
        self.bg_animation.stop()
        self.bg_animation.setStartValue(self._bg_size)
        self.bg_animation.setEndValue(QSize(NAV_PARAMS['anim_final_width'], NAV_PARAMS['anim_final_height']))
        self.bg_animation.start()
        
        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(self._bg_opacity)
        self.opacity_animation.setEndValue(0.5)
        self.opacity_animation.start()

    # --- Свойства для анимации ---
    def get_bg_size(self) -> QSize:
        return self._bg_size

    def set_bg_size(self, size: QSize):
        if self._bg_size != size:
            self._bg_size = size
            self.update()

    bg_size = pyqtProperty(QSize, get_bg_size, set_bg_size)

    def get_bg_opacity(self) -> float:
        return self._bg_opacity

    def set_bg_opacity(self, value: float):
        if self._bg_opacity != value:
            self._bg_opacity = value
            self.update()

    bg_opacity = pyqtProperty(float, get_bg_opacity, set_bg_opacity)

    # --- Свойство checked ---
    def get_checked(self) -> bool:
        return self._checked

    def set_checked(self, value: bool):
        if self._checked != value:
            self._checked = value
            self.setProperty("checked", value)
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()
            
            if value:
                self._animate_to_active()
            else:
                self._animate_to_default()
            self._update_colors()

    checked = pyqtProperty(bool, get_checked, set_checked)

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
        central_widget.setStyleSheet("background-color: #F5F5F5;")

        # === ГОРИЗОНТАЛЬНАЯ НАВИГАЦИОННАЯ ПАНЕЛЬ ===
        nav_container = QWidget()
        nav_container.setFixedSize(NAV_PARAMS['sidebar_width'], NAV_PARAMS['sidebar_height'])
        nav_container.setObjectName("nav_container")

        # Стиль панели: белый фон, скругленные углы
        nav_container.setStyleSheet("""
            #nav_container {
                background-color: #FFFFFF;
                border-radius: 20px;
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
            NAV_PARAMS['sidebar_padding_left'], 
            0, 
            NAV_PARAMS['sidebar_padding_right'], 
            0
        )
        nav_horizontal_layout.setSpacing(NAV_PARAMS['btn_spacing'])
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

        self.stacked_widget.addWidget(self.upload_tab)
        self.stacked_widget.addWidget(self.results_tab)
        self.stacked_widget.addWidget(self.history_tab)

        # Подключаем сигналы
        self.upload_tab.file_loaded.connect(self.on_file_loaded)
        self.upload_tab.settings_requested.connect(self.open_settings_dialog)
        
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