# ui/components/chart_widget.py
from PyQt6.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from ui.components.pie_chart import PieChartWidget
from ui.components.bar_chart import BarChartWidget
from ui.components.line_chart import LineChartWidget


class ChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QTabWidget()
        
        self.pie_tab = PieChartWidget()
        self.bar_tab = BarChartWidget()
        self.line_tab = LineChartWidget()
        
        layout.addTab(self.pie_tab, "Круговая диаграмма")
        layout.addTab(self.bar_tab, "Линейчатая диаграмма")
        layout.addTab(self.line_tab, "График")
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(layout)
        self.setLayout(main_layout)
    
    def set_data(self, df):
        """Обновляет все графики"""
        self.pie_tab.set_data(df)
        self.bar_tab.set_data(df)
        self.line_tab.set_data(df)