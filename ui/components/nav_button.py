# ui/components/nav_button.py
"""Кастомная кнопка для горизонтальной навигации с анимацией выделения."""
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QPropertyAnimation, QEasingCurve, QSize, QSequentialAnimationGroup
from PyQt6.QtGui import QIcon, QColor, QFont, QPainter, QBrush, QPainterPath, QPixmap, QImage, qRgba, qAlpha


# Параметры навигации
NAV_BUTTON_PARAMS = {
    # Размеры кнопки
    'highlight_width': 150,
    'highlight_height': 70,
    'highlight_radius_h': 34,
    'highlight_radius_v': 35,
    # Иконка
    'icon_size': 30,
    # Шрифт
    'font_size': 14,
    # Анимация - размеры по этапам (в пикселях)
    'anim_stage1_width': 15,
    'anim_stage1_height': 15,
    'anim_stage2_width': 10,
    'anim_stage2_height': 10,
    'anim_stage3_width': 25,
    'anim_stage3_height': 25,
    'anim_stage4_width': 150,
    'anim_stage4_height': 70,
    # Длительность каждого этапа анимации (мс)
    'anim_stage1_duration': 80,  # 15x15 -> 10x10
    'anim_stage2_duration': 80,  # 10x10 -> 25x25
    'anim_stage3_duration': 130,  # 25x25 -> 112x70
    # Цвета
    'color_highlight_bg': '#b4d1ee',      # фон активной кнопки
    'color_hover_bg': '#e6e6e6',          # фон при наведении
    'color_highlight_text': '#0678ea',    # текст/иконка активной кнопки
    'color_text_default': '#000000',      # текст/иконка по умолчанию
}


class NavButton(QWidget):
    """Кастомная кнопка для горизонтальной навигации с анимацией выделения."""
    clicked = pyqtSignal()

    def __init__(self, icon_path: str, text: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(NAV_BUTTON_PARAMS['highlight_width'], NAV_BUTTON_PARAMS['highlight_height'])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = False
        self._hover = False

        # Анимация размера фона - последовательная анимация
        self._bg_size = QSize(NAV_BUTTON_PARAMS['anim_stage1_width'], NAV_BUTTON_PARAMS['anim_stage1_height'])

        # Создаем группу последовательных анимаций
        self.bg_animation_group = QSequentialAnimationGroup(self)

        # Этап 1: 15x15 -> 10x10 (сжатие)
        self.anim_stage1 = QPropertyAnimation(self, b"bg_size")
        self.anim_stage1.setDuration(NAV_BUTTON_PARAMS['anim_stage1_duration'])
        self.anim_stage1.setStartValue(QSize(NAV_BUTTON_PARAMS['anim_stage1_width'], NAV_BUTTON_PARAMS['anim_stage1_height']))
        self.anim_stage1.setEndValue(QSize(NAV_BUTTON_PARAMS['anim_stage2_width'], NAV_BUTTON_PARAMS['anim_stage2_height']))
        self.anim_stage1.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.bg_animation_group.addAnimation(self.anim_stage1)

        # Этап 2: 10x10 -> 25x25 (расширение)
        self.anim_stage2 = QPropertyAnimation(self, b"bg_size")
        self.anim_stage2.setDuration(NAV_BUTTON_PARAMS['anim_stage2_duration'])
        self.anim_stage2.setStartValue(QSize(NAV_BUTTON_PARAMS['anim_stage2_width'], NAV_BUTTON_PARAMS['anim_stage2_height']))
        self.anim_stage2.setEndValue(QSize(NAV_BUTTON_PARAMS['anim_stage3_width'], NAV_BUTTON_PARAMS['anim_stage3_height']))
        self.anim_stage2.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.bg_animation_group.addAnimation(self.anim_stage2)

        # Этап 3: 25x25 -> 112x70 (финальный размер)
        self.anim_stage3 = QPropertyAnimation(self, b"bg_size")
        self.anim_stage3.setDuration(NAV_BUTTON_PARAMS['anim_stage3_duration'])
        self.anim_stage3.setStartValue(QSize(NAV_BUTTON_PARAMS['anim_stage3_width'], NAV_BUTTON_PARAMS['anim_stage3_height']))
        self.anim_stage3.setEndValue(QSize(NAV_BUTTON_PARAMS['anim_stage4_width'], NAV_BUTTON_PARAMS['anim_stage4_height']))
        self.anim_stage3.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.bg_animation_group.addAnimation(self.anim_stage3)

        # Анимация прозрачности (появление фона)
        self._bg_opacity = 0.0
        self.opacity_animation = QPropertyAnimation(self, b"bg_opacity")
        self.opacity_animation.setDuration(
            NAV_BUTTON_PARAMS['anim_stage1_duration'] +
            NAV_BUTTON_PARAMS['anim_stage2_duration'] +
            NAV_BUTTON_PARAMS['anim_stage3_duration']
        )
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.Linear)

        # Сохраняем путь к иконке (преобразуем в абсолютный)
        self.icon_path = str(Path(icon_path).absolute()) if not Path(icon_path).is_absolute() else icon_path
        self.icon_size = NAV_BUTTON_PARAMS['icon_size']

        # Layout - вертикальный, центрирование по горизонтали
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

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
        font = QFont("Genzsch Antiqua", NAV_BUTTON_PARAMS['font_size'])
        font.setWeight(QFont.Weight.Medium)
        self.text_label.setFont(font)
        self.text_label.setStyleSheet("color: #000000; background-color: transparent;")
        layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Загружаем иконку с цветом по умолчанию
        self._update_icon()
        self._update_colors()

    def _create_colored_icon(self, color: QColor) -> QPixmap:
        """Создает QPixmap из SVG с указанным цветом через QIcon."""
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
            color = QColor(NAV_BUTTON_PARAMS['color_highlight_text'])
        else:
            color = QColor(NAV_BUTTON_PARAMS['color_text_default'])

        pixmap = self._create_colored_icon(color)
        self.icon_label.setPixmap(pixmap)
        self.icon_label.update()

    def _update_colors(self):
        """Обновление цветов текста."""
        if self._checked:
            color = NAV_BUTTON_PARAMS['color_highlight_text']
        else:
            color = NAV_BUTTON_PARAMS['color_text_default']

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
            bg_color = QColor(NAV_BUTTON_PARAMS['color_highlight_bg'])
            bg_color.setAlphaF(self._bg_opacity)
        elif self._hover:
            bg_width = NAV_BUTTON_PARAMS['highlight_width']
            bg_height = NAV_BUTTON_PARAMS['highlight_height']
            bg_color = QColor(NAV_BUTTON_PARAMS['color_hover_bg'])
        else:
            return

        path = QPainterPath()
        x = (self.width() - bg_width) / 2
        y = (self.height() - bg_height) / 2
        path.addRoundedRect(
            x, y,
            bg_width,
            bg_height,
            NAV_BUTTON_PARAMS['highlight_radius_h'],
            NAV_BUTTON_PARAMS['highlight_radius_v']
        )

        painter.fillPath(path, QBrush(bg_color))

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _animate_to_active(self):
        """Анимация к активному состоянию (последовательная)."""
        self._bg_size = QSize(NAV_BUTTON_PARAMS['anim_stage1_width'], NAV_BUTTON_PARAMS['anim_stage1_height'])
        self.bg_animation_group.start()
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

    def _animate_to_default_reverse(self):
        """Анимация к состоянию по умолчанию (обратная последовательность)."""
        reverse_group = QSequentialAnimationGroup(self)

        anim1 = QPropertyAnimation(self, b"bg_size")
        anim1.setDuration(NAV_BUTTON_PARAMS['anim_stage3_duration'])
        anim1.setStartValue(QSize(NAV_BUTTON_PARAMS['anim_stage4_width'], NAV_BUTTON_PARAMS['anim_stage4_height']))
        anim1.setEndValue(QSize(NAV_BUTTON_PARAMS['anim_stage3_width'], NAV_BUTTON_PARAMS['anim_stage3_height']))
        anim1.setEasingCurve(QEasingCurve.Type.InCubic)
        reverse_group.addAnimation(anim1)

        anim2 = QPropertyAnimation(self, b"bg_size")
        anim2.setDuration(NAV_BUTTON_PARAMS['anim_stage2_duration'])
        anim2.setStartValue(QSize(NAV_BUTTON_PARAMS['anim_stage3_width'], NAV_BUTTON_PARAMS['anim_stage3_height']))
        anim2.setEndValue(QSize(NAV_BUTTON_PARAMS['anim_stage2_width'], NAV_BUTTON_PARAMS['anim_stage2_height']))
        anim2.setEasingCurve(QEasingCurve.Type.InQuad)
        reverse_group.addAnimation(anim2)

        anim3 = QPropertyAnimation(self, b"bg_size")
        anim3.setDuration(NAV_BUTTON_PARAMS['anim_stage1_duration'])
        anim3.setStartValue(QSize(NAV_BUTTON_PARAMS['anim_stage2_width'], NAV_BUTTON_PARAMS['anim_stage2_height']))
        anim3.setEndValue(QSize(NAV_BUTTON_PARAMS['anim_stage1_width'], NAV_BUTTON_PARAMS['anim_stage1_height']))
        anim3.setEasingCurve(QEasingCurve.Type.OutQuad)
        reverse_group.addAnimation(anim3)

        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.start()
        reverse_group.start()

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
                self._animate_to_default_reverse()
            self._update_colors()

    checked = pyqtProperty(bool, get_checked, set_checked)

    def setChecked(self, checked: bool):
        self.checked = checked

    def isChecked(self):
        return self.checked
