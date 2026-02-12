# ui/components/analyze_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QProgressBar, QHBoxLayout, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont
import pandas as pd
from core.processor import process_data
from ui.components.table_widget import ExcelTable


class ProcessWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, df):
        super().__init__()
        self.df = df

    def run(self):
        try:
            processed_df = process_data(self.df)
            self.finished.emit(processed_df)
        except Exception as e:
            self.error.emit(str(e))


class AnalyzeWidget(QWidget):
    file_saved = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_df = None
        self.processed_df = None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)
        
        # === Кнопки и прогресс ===
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.process_button = QPushButton("⚙️ Обработать данные")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.start_processing)
        button_layout.addWidget(self.process_button)
        
        self.save_button = QPushButton("💾 Сохранить файл")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_file)
        button_layout.addWidget(self.save_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # === Прогресс-бар ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        main_layout.addWidget(self.progress_bar)
        
        # === Таблица результатов (в том же контейнере, что и в Загрузке) ===
        self.result_container = QWidget()
        self.result_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 16px;
                margin: 0px;
                padding: 0px;
            }
        """)
        table_layout = QVBoxLayout(self.result_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.result_table = ExcelTable()
        table_layout.addWidget(self.result_table)
        main_layout.addWidget(self.result_container)
        self.original_filename = None

    
    def set_data(self, df):
        self.current_df = df
        self.process_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.result_table.setModel(None)
    def set_original_filename(self, filename):
        self.original_filename = filename
    
    def start_processing(self):
        if self.current_df is None:
            return
        
        self.process_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.worker = ProcessWorker(self.current_df)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.worker.start()
    
    def on_processing_finished(self, processed_df):
        self.processed_df = processed_df
        self.result_table.set_data_frame(processed_df)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
    
    def on_processing_error(self, error_msg):
        print(f"Ошибка обработки: {error_msg}")
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
    
    def save_file(self):
        if self.processed_df is None:
            return
            
        # Генерируем имя: "Обработанный исходное_имя.xlsx"
        default_name = "Обработанный processed_data.xlsx"
            
        # Если есть исходный файл из UploadWidget, используем его имя
        if hasattr(self, 'original_filename') and self.original_filename:
            base_name = self.original_filename
            if base_name.endswith('.xlsx'):
                base_name = base_name[:-5]  # Убираем .xlsx
            elif base_name.endswith('.xls'):
                base_name = base_name[:-4]  # Убираем .xls
            default_name = f"Обработанный {base_name}.xlsx"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить обработанный файл",
            default_name,
            "Excel Files (*.xlsx)"
        )
            
        if file_path:
            try:
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                    
                self.processed_df.to_excel(file_path, index=False)
                self.file_saved.emit(file_path)
                print(f"Файл сохранён: {file_path}")
                    
            except Exception as e:
                print(f"Ошибка сохранения: {e}")