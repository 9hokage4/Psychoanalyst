# ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon
from ui.components.upload_widget import UploadWidget
from ui.components.analyze_widget import AnalyzeWidget
from ui.components.chart_widget import ChartWidget
from ui.components.history_widget import HistoryWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Psychoanalyst")
        self.setMinimumSize(1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Вкладки
        self.tabs = QTabWidget()
        
        # Создаём вкладки
        self.upload_tab = UploadWidget()
        self.analyze_tab = AnalyzeWidget()
        self.chart_tab = ChartWidget()
        self.history_tab = HistoryWidget()
        
        # Добавляем вкладки с иконками
        self.tabs.addTab(self.upload_tab, QIcon("resources/icons/upload.svg"), "Загрузка")
        self.tabs.addTab(self.analyze_tab, QIcon("resources/icons/analysis.svg"), "Анализ")
        self.tabs.addTab(self.chart_tab, QIcon("resources/icons/chart-line.svg"), "Графики")
        self.tabs.addTab(self.history_tab, QIcon("resources/icons/history.svg"), "История")
        
        main_layout.addWidget(self.tabs)
        
        # Подключаем сигналы
        self.upload_tab.file_loaded.connect(self.on_file_loaded)
        self.upload_tab.filename_updated.connect(self.analyze_tab.set_original_filename)
        self.upload_tab.settings_requested.connect(self.open_settings_dialog)
        self.analyze_tab.file_saved.connect(self.history_tab.add_saved_file)
        
        # Загружаем стили
        self.load_styles()
    
    def on_file_loaded(self, df):
        self.analyze_tab.set_data(df)
        self.chart_tab.set_data(df)
        self.history_tab.add_to_history(df)
    
    def open_settings_dialog(self):
        from ui.components.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.config_saved.connect(self.on_config_saved)
        dialog.exec()
    
    def on_config_saved(self, scales, levels, level_order, answer_weights):
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
    
    def load_styles(self):
        """Загружает стили из style.qss"""
        try:
            with open("ui/style.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Ошибка загрузки стилей: {e}")