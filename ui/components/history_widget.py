# ui/components/history_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class HistoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("История обработок"))
        layout.addStretch()
        self.setLayout(layout)
    
    def add_to_history(self, df):
        # Пока просто заглушка
        print(f"Добавлено в историю: {len(df)} строк")
    
    def add_saved_file(self, file_path):
        # Заглушка для сохранённых файлов
        print(f"Сохранён файл: {file_path}")