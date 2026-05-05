# utils/message_box.py
from PyQt6.QtWidgets import QMessageBox, QLabel
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt

class MessageHelper:
    @staticmethod
    def show_error(parent, title, message):
        MessageHelper._show(parent, title, message, "error")

    @staticmethod
    def show_success(parent, title, message):
        MessageHelper._show(parent, title, message, "success")

    @staticmethod
    def show_warning(parent, title, message):
        MessageHelper._show(parent, title, message, "warning")

    @staticmethod
    def _show(parent, title, message, msg_type="error"):
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Устанавливаем иконку в заголовке окна
        if msg_type == "success":
            msg_box.setWindowIcon(QIcon("resources/icons/success.svg"))
        elif msg_type == "error":
            msg_box.setWindowIcon(QIcon("resources/icons/error.svg"))
        else:
            # можно использовать любую дефолтную иконку
            msg_box.setWindowIcon(QIcon())

        msg_box.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; border-radius: 12px; }
            QMessageBox QLabel { color: #000000; font-size: 14px; background-color: #FFFFFF; }
            QPushButton { background-color: #3390EC; color: white; border: none; border-radius: 8px; padding: 8px 16px; font-size: 14px; font-weight: 500; }
            QPushButton:hover { background-color: #2B80D9; }
        """)

        # Иконка рядом с текстом (оставляем как было)
        icon_label = QLabel()
        if msg_type == "success":
            pixmap = QPixmap("resources/icons/attention-circle.svg")
        else:
            pixmap = QPixmap("resources/icons/alert-triangle.svg")
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            icon_label.setPixmap(msg_box.style().standardIcon(QMessageBox.Icon.Warning).pixmap(48, 48))
        icon_label.setStyleSheet("background-color: white;")

        layout = msg_box.layout()
        layout.addWidget(icon_label, 0, 0, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        msg_box.exec()