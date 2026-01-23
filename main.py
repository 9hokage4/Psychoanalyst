import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Создаём приложение
app = QApplication(sys.argv)

# Главное окно
window = QMainWindow()
window.setWindowTitle("Минимализм")
window.setFixedSize(400, 300)  # Фиксированный размер

# Центральный виджет
central_widget = QWidget()
layout = QVBoxLayout()
layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

# Надпись
label = QLabel("Привет, PyQt6!")
label.setFont(QFont("Segoe UI", 16))
label.setStyleSheet("color: #333;")  # Тёмно-серый текст

layout.addWidget(label)
central_widget.setLayout(layout)
window.setCentralWidget(central_widget)

# Показываем окно
window.show()

# Запуск цикла обработки событий
sys.exit(app.exec())