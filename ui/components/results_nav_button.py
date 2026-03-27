# ui/components/results_nav_button.py
"""Кнопка вертикальной навигации для вкладки Результаты с пружинистой анимацией."""
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QPropertyAnimation, QSize, QEasingCurve
from PyQt6.QtGui import QIcon, QColor, QPainter, QBrush, QPainterPath, QPixmap, QImage, qRgba, qAlpha


# Параметры для кнопок результатов
RESULTS_NAV_PARAMS = {
    # Размеры
    'button_min_width': 100,
    'button_min_height': 80,
    'icon_size': 32,
    'font_size': 12,
    # Выделение (фон)
    'highlight_final_width': 80,
    'highlight_final_height': 93,
    'highlight_initial_width': 35,
    'highlight_initial_height': 30,
    'highlight_radius_h': '47%',
    'highlight_radius_v': 35,
    # Анимация
    'animation_duration': 300,
    # Цвета
    'color_highlight_bg': '#b4d1ee',
    'color_hover_bg': '#F4F4F5',
    'color_highlight_text': '#0678ea',
    'color_text_default': '#000000',
}


class ResultsNavButton(QWidget):
    """Кнопка вертикальной навигации с пружинистой анимацией."""
    clicked = pyqtSignal()

    def __init__(self, icon_path: str, text: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(RESULTS_NAV_PARAMS['button_min_width'], RESULTS_NAV_PARAMS['button_min_height'])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = False
        self._hover = False

        # Анимация размера фона
        self._bg_size = QSize(
            RESULTS_NAV_PARAMS['highlight_initial_width'],
            RESULTS_NAV_PARAMS['highlight_initial_height']
        )

        # Анимация с пружинистым easing
        self.bg_animation = QPropertyAnimation(self, b"bg_size")
        self.bg_animation.setDuration(RESULTS_NAV_PARAMS['animation_duration'])
        self.bg_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Анимация прозрачности
        self._bg_opacity = 0.0
        self.opacity_animation = QPropertyAnimation(self, b"bg_opacity")
        self.opacity_animation.setDuration(RESULTS_NAV_PARAMS['animation_duration'])
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.Linear)

        # Иконка
        self.icon_path = str(Path(icon_path).absolute()) if not Path(icon_path).is_absolute() else icon_path
        self.icon_size = RESULTS_NAV_PARAMS['icon_size']

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Иконка
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(self.icon_size, self.icon_size)
        self.icon_label.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Текст
        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setObjectName("nav_text")
        from PyQt6.QtGui import QFont
        font = QFont("Genzsch Antiqua", RESULTS_NAV_PARAMS['font_size'])
        font.setWeight(QFont.Weight.Medium)
        self.text_label.setFont(font)
        self.text_label.setStyleSheet("color: #000000; background-color: transparent;")
        layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Загружаем иконку
        self._update_icon()
        self._update_colors()

    def _create_colored_icon(self, color: QColor) -> QPixmap:
        """Создает QPixmap из SVG с указанным цветом."""
        icon = QIcon(self.icon_path)
        pixmap = icon.pixmap(self.icon_size, self.icon_size)

        if pixmap.isNull():
            pixmap = QPixmap(self.icon_size, self.icon_size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(0, 0, self.icon_size, self.icon_size)
            painter.end()
            return pixmap

        image = pixmap.toImage()
        image = image.convertToFormat(QImage.Format.Format_ARGB32)

        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixel(x, y)
                alpha = qAlpha(pixel)
                if alpha > 0:
                    new_pixel = qRgba(color.red(), color.green(), color.blue(), alpha)
                    image.setPixel(x, y, new_pixel)

        return QPixmap.fromImage(image)

    def _update_icon(self):
        """Обновляет иконку с текущим цветом."""
        if self._checked:
            color = QColor(RESULTS_NAV_PARAMS['color_highlight_text'])
        else:
            color = QColor(RESULTS_NAV_PARAMS['color_text_default'])

        pixmap = self._create_colored_icon(color)
        self.icon_label.setPixmap(pixmap)
        self.icon_label.update()

    def _update_colors(self):
        """Обновление цветов текста."""
        if self._checked:
            color = RESULTS_NAV_PARAMS['color_highlight_text']
        else:
            color = RESULTS_NAV_PARAMS['color_text_default']

        self.text_label.setStyleSheet(f"color: {color};")
        self._update_icon()
        self.update()

    def paintEvent(self, event):
        """Отрисовка фона с анимацией."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Определяем размер и позицию для отрисовки
        if self._checked:
            bg_width = self._bg_size.width()
            bg_height = self._bg_size.height()
            bg_color = QColor(RESULTS_NAV_PARAMS['color_highlight_bg'])
            bg_color.setAlphaF(self._bg_opacity)
        elif self._hover:
            bg_width = RESULTS_NAV_PARAMS['highlight_final_width']
            bg_height = RESULTS_NAV_PARAMS['highlight_final_height']
            bg_color = QColor(RESULTS_NAV_PARAMS['color_hover_bg'])
        else:
            return

        path = QPainterPath()
        x = (self.width() - bg_width) / 2
        y = (self.height() - bg_height) / 2
        
        # Скругление
        radius_h = RESULTS_NAV_PARAMS['highlight_radius_v']
        radius_v = RESULTS_NAV_PARAMS['highlight_radius_v']
        path.addRoundedRect(x, y, bg_width, bg_height, radius_h, radius_v)

        painter.fillPath(path, QBrush(bg_color))

    def enterEvent(self, event):
        self._hover = True
        if not self._checked:
            self._animate_to_hover()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        if not self._checked:
            self._animate_to_default()
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _animate_to_active(self):
        """Анимация к активному состоянию."""
        self.bg_animation.stop()
        self.bg_animation.setStartValue(QSize(
            RESULTS_NAV_PARAMS['highlight_initial_width'],
            RESULTS_NAV_PARAMS['highlight_initial_height']
        ))
        self.bg_animation.setEndValue(QSize(
            RESULTS_NAV_PARAMS['highlight_final_width'],
            RESULTS_NAV_PARAMS['highlight_final_height']
        ))
        self.bg_animation.start()

        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

    def _animate_to_default(self):
        """Анимация к состоянию по умолчанию."""
        self.bg_animation.stop()
        self.bg_animation.setStartValue(self._bg_size)
        self.bg_animation.setEndValue(QSize(
            RESULTS_NAV_PARAMS['highlight_initial_width'],
            RESULTS_NAV_PARAMS['highlight_initial_height']
        ))
        self.bg_animation.start()

        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(self._bg_opacity)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.start()

    def _animate_to_hover(self):
        """Анимация к состоянию наведения."""
        self.bg_animation.stop()
        self.bg_animation.setStartValue(self._bg_size)
        self.bg_animation.setEndValue(QSize(
            RESULTS_NAV_PARAMS['highlight_final_width'],
            RESULTS_NAV_PARAMS['highlight_final_height']
        ))
        self.bg_animation.start()

        self.opacity_animation.stop()
        self.opacity_animation.setStartValue(self._bg_opacity)
        self.opacity_animation.setEndValue(1.0)
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
