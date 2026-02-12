# ui/components/line_chart.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd


class LineChartWidget(QWidget):
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
        self.plot_line()
    
    def plot_line(self):
        if self.df is None or self.df.empty:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Пример: линейный график по двум первым числовым колонкам
        numeric_cols = self.df.select_dtypes(include='number').columns
        if len(numeric_cols) < 2:
            ax.text(0.5, 0.5, 'Нужно минимум 2 числовые колонки', ha='center', va='center')
            self.canvas.draw()
            return
        
        x_col, y_col = numeric_cols[:2]
        ax.plot(self.df[x_col], self.df[y_col], marker='o', linestyle='-')
        ax.set_title(f'График: {y_col} vs {x_col}')
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.grid(True)
        
        self.canvas.draw()