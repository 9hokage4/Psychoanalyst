# ui/components/pie_chart.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd


class PieChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        self.df = None
    
    def set_data(self, df):
        self.df = df
        self.plot_pie()
    
    def plot_pie(self):
        if self.df is None or self.df.empty:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Пример: считаем количество уникальных значений в первой колонке
        first_col = self.df.columns[0]
        value_counts = self.df[first_col].value_counts()
        
        ax.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
        ax.set_title(f'Круговая диаграмма: {first_col}')
        
        self.canvas.draw()