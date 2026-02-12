# ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from ui.components.upload_widget import UploadWidget
from ui.components.analyze_widget import AnalyzeWidget
from ui.components.chart_widget import ChartWidget
from ui.components.history_widget import HistoryWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализатор психологических тестов")
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        self.upload_tab = UploadWidget()
        self.analyze_tab = AnalyzeWidget()
        self.chart_tab = ChartWidget()
        self.history_tab = HistoryWidget()
        
        self.tab_widget.addTab(self.upload_tab, "Загрузка")
        self.tab_widget.addTab(self.analyze_tab, "Анализ")
        self.tab_widget.addTab(self.chart_tab, "Графики")
        self.tab_widget.addTab(self.history_tab, "История")
        
        # Подключаем сигнал загрузки файла
        self.upload_tab.file_loaded.connect(self.on_file_loaded)
        
        # Размещение
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.tab_widget)
    
    def on_file_loaded(self, df):
        """Передаём данные во все вкладки"""
        self.analyze_tab.set_data(df)
        self.chart_tab.set_data(df)
        self.history_tab.add_to_history(df)