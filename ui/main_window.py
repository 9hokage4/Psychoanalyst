# ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from ui.components.upload_widget import UploadWidget
from ui.components.analyze_widget import AnalyzeWidget
from ui.components.chart_widget import ChartWidget
from ui.components.history_widget import HistoryWidget
from ui.components.settings_dialog import SettingsDialog


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
        self.analyze_tab.file_saved.connect(self.history_tab.add_saved_file)
        
        # Подключаем сигнал загрузки файла
        self.upload_tab.file_loaded.connect(self.on_file_loaded)
        self.upload_tab.filename_updated.connect(self.analyze_tab.set_original_filename)
        self.upload_tab.settings_requested.connect(self.open_settings_dialog)
        self.upload_tab.file_loaded.connect(self.on_file_loaded)
        
        # Размещение
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.tab_widget)
    
    def open_settings_dialog(self):
        print("Открыть диалог настроек")
    
    def on_file_loaded(self, df):
        """Передаём данные во все вкладки"""
        self.analyze_tab.set_data(df)
        self.chart_tab.set_data(df)
        self.history_tab.add_to_history(df)
    
    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.config_saved.connect(self.on_config_saved)
        dialog.exec()

    def on_config_saved(self, scales, levels, level_order, answer_weights):
        """Обработка сохранённой конфигурации"""
        print(f"Конфигурация сохранена:")
        print(f"Шкалы: {scales}")
        print(f"Уровни: {levels}")
        print(f"Порядок: {level_order}")
        print(f"Веса: {answer_weights}")
        
        self.current_config = {
            "scales": scales,
            "levels": levels,
            "level_order": level_order,
            "answer_weights": answer_weights
        }