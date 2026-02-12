# ui/components/bar_chart.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd


class BarChartWidget(QWidget):
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
        self.plot_bar()
    
    def plot_bar(self):
        if self.df is None or self.df.empty:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Пример: гистограмма по первой числовой колонке
        numeric_cols = self.df.select_dtypes(include='number').columns
        if len(numeric_cols) == 0:
            ax.text(0.5, 0.5, 'Нет числовых данных', ha='center', va='center')
            self.canvas.draw()
            return
        
        col = numeric_cols[0]
        ax.hist(self.df[col].dropna(), bins=10, edgecolor='black')
        ax.set_title(f'Линейчатая диаграмма: {col}')
        ax.set_xlabel(col)
        ax.set_ylabel('Частота')
        
        self.canvas.draw()