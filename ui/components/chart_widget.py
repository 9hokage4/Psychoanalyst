# ui/components/chart_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class ChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_df = None
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Графики"))
        layout.addStretch()
        self.setLayout(layout)
    
    def set_data(self, df):
        self.current_df = df