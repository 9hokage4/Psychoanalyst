# ui/components/analyze_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel


class AnalyzeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_df = None
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Анализ данных"))
        self.process_button = QPushButton("⚙️ Обработать данные")
        self.process_button.setEnabled(False)
        layout.addWidget(self.process_button)
        layout.addStretch()
        self.setLayout(layout)
    
    def set_data(self, df):
        self.current_df = df
        self.process_button.setEnabled(True)