# -*- coding: utf-8 -*-
# ui/components/results_widget.py
import pandas as pd
import tempfile
from pathlib import Path
from typing import Dict, Any
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, Color
from openpyxl.utils import get_column_letter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QFileDialog, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QBrush, QPixmap
from utils.fonts import get_font, FontWeights
from ui.components.results_nav_button import ResultsNavButton
from utils.excel_export import ExcelExporter, open_excel_file
from utils.folder_manager import FolderManager
import tempfile
import os


# Цвета для шкал
SCALE_COLORS = [
    "E3F2FD",  # Голубой
    "E8F5E9",  # Зелёный
    "FFF3E0",  # Оранжевый
    "F3E5F5",  # Фиолетовый
    "FFEBEE",  # Красный
    "E0F7FA",  # Бирюзовый
    "FFF8E1",  # Янтарный
    "F1F8E9",  # Лайм
    "FCE4EC",  # Розовый
    "F9FBE7",  # Лайм светлый
]


class ResultsWidget(QWidget):
    sheet_changed = pyqtSignal(str)
    table_type_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_sheet = "Все листы"
        self.current_table_type = "Все респонденты"
        self.table_df = None
        self.charts_data = {}
        self.summary_data = {}
        self.scales_config = {}
        self.level_order = []
        self.level_ru = {}
        self.has_group = False
        self.has_course = False
        self.processed_file_path = Path("processed_data.xlsx")
        self.excel_exporter = ExcelExporter()  # Экспортёр Excel
        self.output_folder_path = ""  # Путь к папке вывода (из настроек)
        self.folder_manager = FolderManager()  # Менеджер папок
        self._last_error_message = ""  # Для отслеживания дубликатов ошибок
        self.setup_ui()
        self._load_processed_data()
        self._load_output_folder()  # Загружаем путь к папке

    def setup_ui(self):
        # Основной layout с отступами
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Контейнер для результатов (горизонтальное расположение)
        results_container = QWidget()
        results_layout = QHBoxLayout(results_container)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(20)

        # ===== ЛЕВАЯ ВЕРТИКАЛЬНАЯ ПАНЕЛЬ =====
        self.sidebar = QWidget()
        self.sidebar.setObjectName("results_sidebar")
        self.sidebar.setFixedSize(140, 550)  # Увеличили высоту для новой кнопки

        # Тень для sidebar
        sidebar_shadow = QGraphicsDropShadowEffect()
        sidebar_shadow.setBlurRadius(20)
        sidebar_shadow.setOffset(0, 4)
        sidebar_shadow.setColor(QColor(0, 0, 0, 20))
        self.sidebar.setGraphicsEffect(sidebar_shadow)

        # Стиль sidebar
        self.sidebar.setStyleSheet("""
            QWidget#results_sidebar {
                background-color: #FFFFFF;
                border-radius: 70px;
            }
        """)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 40)
        sidebar_layout.setSpacing(16)

        # Пружина сверху для центрирования
        sidebar_layout.addStretch()

        self.nav_buttons = []

        # Кнопки навигации
        btn_table = ResultsNavButton("resources/icons/table.svg", "")
        btn_table.setChecked(True)
        btn_table.clicked.connect(lambda: self._switch_view(0))
        self.nav_buttons.append(btn_table)

        btn_pie = ResultsNavButton("resources/icons/pie.svg", "")
        btn_pie.clicked.connect(lambda: self._switch_view(1))
        self.nav_buttons.append(btn_pie)

        btn_bar = ResultsNavButton("resources/icons/bar.svg", "")
        btn_bar.clicked.connect(lambda: self._switch_view(2))
        self.nav_buttons.append(btn_bar)

        btn_line = ResultsNavButton("resources/icons/line.svg", "")
        btn_line.clicked.connect(lambda: self._switch_view(3))
        self.nav_buttons.append(btn_line)

        # Добавляем кнопки в панель
        for btn in self.nav_buttons:
            sidebar_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Пружина снизу для равного отступа
        sidebar_layout.addStretch()

        results_layout.addWidget(self.sidebar)

        # ===== ОСНОВНАЯ ОБЛАСТЬ =====
        content_widget = QWidget()
        content_widget.setObjectName("results_content")
        content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Тень для content
        content_shadow = QGraphicsDropShadowEffect()
        content_shadow.setBlurRadius(20)
        content_shadow.setOffset(0, 4)
        content_shadow.setColor(QColor(0, 0, 0, 20))
        content_widget.setGraphicsEffect(content_shadow)

        # Стиль content
        content_widget.setStyleSheet("""
            QWidget#results_content {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
        """)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # Выбор типа таблицы / графика
        self.selector_widget = self._create_selector()
        content_layout.addWidget(self.selector_widget)

        # Стек видов (растягивается на всю доступную высоту)
        self.views_stack = QStackedWidget()
        self.views_stack.setObjectName("views_stack")
        self.views_stack.setStyleSheet("background-color: transparent;")
        self.views_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Таблица
        self.table_view = self._create_table_view()
        self.views_stack.addWidget(self.table_view)

        # Круговая диаграмма
        self.pie_view = self._create_pie_chart_view()
        self.views_stack.addWidget(self.pie_view)

        # Столбчатая диаграмма
        self.bar_view = self._create_bar_chart_view()
        self.views_stack.addWidget(self.bar_view)

        # Линейный график
        self.line_view = self._create_line_chart_view()
        self.views_stack.addWidget(self.line_view)

        content_layout.addWidget(self.views_stack)
        results_layout.addWidget(content_widget)

        main_layout.addWidget(results_container)

        # ===== КНОПКИ ЭКСПОРТА =====
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        button_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Кнопка "Открыть в Excel" (только для таблицы)
        self.open_excel_btn = QPushButton("Открыть в Excel")
        self.open_excel_btn.setFixedHeight(56)
        self.open_excel_btn.setFont(get_font("button", size=16, weight=FontWeights.SEMIBOLD))
        self.open_excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 48px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.open_excel_btn.clicked.connect(self.open_in_excel)
        button_row.addWidget(self.open_excel_btn)
        
        # Кнопка "Сохранить график" (только для графиков)
        self.download_chart_btn = QPushButton("Сохранить график")
        self.download_chart_btn.setFixedHeight(56)
        self.download_chart_btn.setFont(get_font("button", size=16, weight=FontWeights.SEMIBOLD))
        self.download_chart_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 48px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        self.download_chart_btn.clicked.connect(self.download_chart)
        self.download_chart_btn.setVisible(False)  # Скрыта по умолчанию
        button_row.addWidget(self.download_chart_btn)
        
        # Кнопка "Экспорт в Excel"
        export_btn = QPushButton("Экспорт в Excel")
        export_btn.setFixedHeight(56)
        export_btn.setFont(get_font("button", size=16, weight=FontWeights.SEMIBOLD))
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #6BBF8A;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 48px;
            }
            QPushButton:hover {
                background-color: #5AA878;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        export_btn.clicked.connect(self.export_to_excel)
        button_row.addWidget(export_btn)
        
        main_layout.addLayout(button_row)
        self.export_excel_btn = export_btn

        # ===== СТИЛИ ДЛЯ КНОПОК НАВИГАЦИИ =====
        self._nav_font_size = 12
        self._nav_icon_size = 32
        self.setStyleSheet(f"""
            ResultsNavButton {{
                background-color: transparent;
                border: none;
                min-width: 80px;
                max-width: 80px;
                min-height: 90px;
                max-height: 90px;
                border-radius: 70px;
                padding: 8px;
                font-size: {self._nav_font_size}px;
            }}
            ResultsNavButton:hover {{
                background-color: #F4F4F5;
            }}
            ResultsNavButton:checked {{
                background-color: #b4d1ee;
            }}
            ResultsNavButton QLabel {{
                background-color: transparent;
            }}
            ResultsNavButton #nav_text {{
                font-size: {self._nav_font_size}px;
            }}
        """)

    def _create_selector(self) -> QWidget:
        """Создаёт выпадающий список выбора типа таблицы/графика"""
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.selector_label = QLabel("📊 Тип таблицы:")
        self.selector_label.setFont(get_font("form_label"))
        self.selector_label.setStyleSheet("color: #707579; background-color: transparent;")

        self.selector_combo = QComboBox()
        self.selector_combo.setObjectName("selector_combo")
        self.selector_combo.setFont(get_font("form_input"))
        # Элементы будут добавлены динамически в set_data
        self.selector_combo.currentTextChanged.connect(self._on_table_type_changed)
        # Фиксированная минимальная ширина, будет обновляться динамически
        self.selector_combo.setMinimumWidth(250)
        self.selector_combo.setStyleSheet("""
            QComboBox {
                padding: 12px 14px;
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                min-height: 40px;
            }
            QComboBox:focus {
                border: 1px solid #3390EC;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 12px;
                height: 12px;
            }
        """)

        layout.addWidget(self.selector_label)
        layout.addWidget(self.selector_combo)
        layout.addStretch()

        return widget

    def _on_table_type_changed(self, table_type: str):
        """Обработчик смены листа"""
        self.current_table_type = table_type
        self.table_type_changed.emit(table_type)
        self._load_current_sheet()
        self._update_current_chart() 

    def _create_table_view(self) -> QTableWidget:
        """Создаёт таблицу результатов с улучшенными стилями"""
        table = QTableWidget()
        table.setObjectName("results_table")
        table.setRowCount(0)
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "Респондент", "Дата", "Уровень", "Баллы"])

        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setDragEnabled(False)
        table.setAlternatingRowColors(True)  # Чередование цветов строк

        # Плавная прокрутка (как в Excel)
        table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # Высота строк
        table.verticalHeader().setDefaultSectionSize(42)
        
        # Улучшенные стили
        table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: none;
                gridline-color: #E0E0E0;
                show-decoration-selected: 0;
                font-size: 15px;
                font-family: 'Segoe UI', Arial;
                alternate-background-color: #FAFAFA;
            }
            
            QTableWidget::item {
                padding: 12px 14px;
                border: none;
                background-color: transparent;
            }
            
            QTableWidget::item:hover {
                background-color: #E3F2FD;
            }
            
            QTableWidget::item:focus {
                background-color: #E3F2FD;
            }
            
            QTableWidget::item:selected {
                background-color: #B3D9F5;
                color: #000000;
            }
            
            QHeaderView::section {
                background-color: #E3F2FD;
                color: #1976D2;
                font-size: 13px;
                font-weight: 600;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #BBDEFB;
                text-transform: uppercase;
            }
            
            QScrollBar:vertical {
                background-color: #F5F5F5;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #BDBDBD;
                border-radius: 6px;
                min-height: 40px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #9E9E9E;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #F5F5F5;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #BDBDBD;
                border-radius: 6px;
                min-width: 40px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #9E9E9E;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        return table

    def _create_pie_chart_view(self) -> QWidget:
        """Создаёт виджет для круговой диаграммы"""
        from ui.components.pie_chart import PieChartWidget
        widget = PieChartWidget()
        widget.setObjectName("pie_chart_widget")
        return widget

    def _create_bar_chart_view(self) -> QWidget:
        """Создаёт виджет для столбчатой диаграммы"""
        from ui.components.bar_chart import BarChartWidget
        widget = BarChartWidget()
        widget.setObjectName("bar_chart_widget")
        return widget

    def _create_line_chart_view(self) -> QWidget:
        """Создаёт виджет для линейного графика"""
        from ui.components.line_chart import LineChartWidget
        widget = LineChartWidget()
        widget.setObjectName("line_chart_widget")
        return widget

    def _switch_view(self, index: int):
        """Переключает вид (таблица/графики)"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.views_stack.setCurrentIndex(index)

        # Обновляем label селектора и видимость
        if index == 0:  # Таблица
            self.selector_label.setText("Выберите лист:")
            self.selector_widget.setVisible(True)
            self.open_excel_btn.setVisible(True)
            self.download_chart_btn.setVisible(False)
            self.export_excel_btn.setVisible(True) 
            # Перезагружаем текущий лист
            self._load_current_sheet()
        else:  # Графики
            self.selector_label.setText("Выберите лист:")
            self.selector_widget.setVisible(True)
            self.open_excel_btn.setVisible(False)
            self.download_chart_btn.setVisible(True)
            self.export_excel_btn.setVisible(False) 
            self._update_current_chart()

        # Обновляем данные в графиках
        if index == 1:
            self.pie_view.set_data(self.summary_data, self.charts_data, self.level_order, self.level_ru, self.scales_config, self.current_table_type)
        elif index == 2:
            self.bar_view.set_data(self.summary_data, self.charts_data, self.level_order, self.level_ru, self.scales_config, self.current_table_type)
        elif index == 3:
            self.line_view.set_data(self.summary_data, self.charts_data, self.level_order, self.level_ru, self.scales_config, self.current_table_type)

    def set_data(self, table_df, charts_data, summary_data):
        """Устанавливает данные из процессора"""
        if table_df is None or table_df.empty:
            return

        self.table_df = table_df
        self.charts_data = charts_data
        self.summary_data = summary_data
        self.scales_config = summary_data.get("scales_config", {})
        self.level_order = summary_data.get("level_order", [])
        self.level_ru = summary_data.get("level_ru", {})
        self.has_group = summary_data.get("has_group", False)
        self.has_course = summary_data.get("has_course", False)

        # Сохраняем полный Excel файл во временное хранилище
        self.temp_excel_path = None
        self._save_full_excel()

        # Динамически заполняем selector в зависимости от наличия данных
        self.selector_combo.blockSignals(True)
        self.selector_combo.clear()
        
        # Определяем, какие листы доступны
        self.available_sheets = ["Результат по всем респондентам"]
        if self.has_course:
            self.available_sheets.append("Результат по курсам")
        if self.has_group:
            self.available_sheets.append("Результат по группам")
        
        self.selector_combo.addItems(self.available_sheets)
        self.current_table_type = "Результат по всем респондентам"
        
        # Обновляем ширину selector под самый длинный текст
        self._update_selector_width()
        self.selector_combo.blockSignals(False)

        # Если нет ни групп ни курсов, скрываем selector
        self.selector_widget.setVisible(len(self.available_sheets) > 1)

        # Загружаем первый лист
        self._load_current_sheet()

    def _save_full_excel(self):
        """Сохраняет полный Excel файл со всеми листами"""
        if self.table_df is None or self.table_df.empty:
            return
        
        try:
            # Создаём временный файл
            self.temp_excel_path = tempfile.NamedTemporaryFile(
                suffix='.xlsx',
                delete=False
            ).name
            
            # Экспортируем полный файл
            export_to_excel_with_summary(
                table_df=self.table_df,
                summary_data=self.summary_data,
                charts_data=self.charts_data,
                output_path=self.temp_excel_path
            )
        except Exception as e:
            print(f"Ошибка сохранения временного Excel файла: {e}")
            self.temp_excel_path = None

    def _load_current_sheet(self):
        """Загружает текущий лист из Excel файла"""
        if not hasattr(self, 'temp_excel_path') or not self.temp_excel_path:
            # Если нет файла, показываем table_df
            self._update_table_view()
            return
        
        try:
            # Маппинг названий листов
            sheet_name = self.current_table_type
            df = pd.read_excel(self.temp_excel_path, sheet_name=sheet_name)
            
            self._update_table_view_from_df(df)
        except Exception as e:
            print(f"Ошибка загрузки листа {self.current_table_type}: {e}")
            self._update_table_view()

    def _update_table_view_from_df(self, df):
        """Обновляет таблицу из DataFrame (Excel листа)"""
        if df is None or df.empty:
            return

        self.table_view.setRowCount(0)
        self.table_view.setColumnCount(len(df.columns))
        self.table_view.setHorizontalHeaderLabels([str(col) for col in df.columns])

        for row_idx, (_, row) in enumerate(df.iterrows()):
            self.table_view.insertRow(row_idx)
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table_view.setItem(row_idx, col_idx, item)

        # Автоподбор ширины
        self.table_view.resizeColumnsToContents()
        for col in range(self.table_view.columnCount()):
            if self.table_view.columnWidth(col) < 100:
                self.table_view.setColumnWidth(col, 100)

    def _update_selector_width(self):
        """Обновляет ширину selector под самый длинный текст"""
        max_width = 0
        for i in range(self.selector_combo.count()):
            text = self.selector_combo.itemText(i)
            # Примерная ширина текста (14px шрифт ~ 8px на символ)
            width = len(text) * 9 + 60  # + отступы и стрелка
            if width > max_width:
                max_width = width
        
        # Минимальная ширина 250px, максимальная 500px
        final_width = max(250, min(max_width, 500))
        self.selector_combo.setFixedWidth(final_width)

    def _update_table_view(self):
        """Обновляет таблицу с полными данными (как в Excel)"""
        if self.table_df is None or self.table_df.empty:
            return

        self.table_view.setRowCount(0)
        self.table_view.setColumnCount(len(self.table_df.columns))
        self.table_view.setHorizontalHeaderLabels([str(col) for col in self.table_df.columns])

        for row_idx, (_, row) in enumerate(self.table_df.iterrows()):
            self.table_view.insertRow(row_idx)
            for col_idx, (col_name, value) in enumerate(row.items()):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                
                # Условное форматирование для шкал
                if col_name.startswith('Шкала_'):
                    value_str = str(value) if pd.notna(value) else ""
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if 'Низкий' in value_str:
                        item.setBackground(QBrush(QColor('#E8F5E9')))
                        item.setForeground(QBrush(QColor('#2E7D32')))
                    elif 'Средний' in value_str:
                        item.setBackground(QBrush(QColor('#FFF3E0')))
                        item.setForeground(QBrush(QColor('#EF6C00')))
                    elif 'Высокий' in value_str:
                        item.setBackground(QBrush(QColor('#FFEBEE')))
                        item.setForeground(QBrush(QColor('#C62828')))
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                self.table_view.setItem(row_idx, col_idx, item)

        # Автоподбор ширины
        self.table_view.resizeColumnsToContents()
        for col in range(self.table_view.columnCount()):
            if self.table_view.columnWidth(col) < 100:
                self.table_view.setColumnWidth(col, 100)

    def open_in_excel(self):
        """Открывает данные в Microsoft Excel (полный файл как при экспорте)"""
        if self.table_df is None or self.table_df.empty:
            self._show_error_message("Ошибка", "Нет данных для открытия")
            return
        
        try:
            # Создаём временный файл с полными данными (как при экспорте)
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.xlsx',
                delete=False,
                mode='w+b'
            )
            temp_path = temp_file.name
            temp_file.close()
            
            # Экспортируем полный файл
            export_to_excel_with_summary(
                table_df=self.table_df,
                summary_data=self.summary_data,
                charts_data=self.charts_data,
                output_path=temp_path
            )
            
            # Открываем в Excel
            if open_excel_file(temp_path):
                self._show_success_message("Успех", "Данные открыты в Excel.\n\nФайл сохранён во временной папке.\nНе забудьте сохранить его в нужном месте!")
            else:
                self._show_error_message("Ошибка", "Не удалось открыть данные в Excel.\n\nУбедитесь, что Microsoft Excel установлен.")
        except Exception as e:
            self._show_error_message("Ошибка", f"Не удалось открыть данные в Excel:\n{str(e)}")

    def download_chart(self):
        """Скачивает текущий график в PNG"""
        # Определяем какой график активен
        current_index = self.views_stack.currentIndex()
        
        if current_index == 1:
            chart_widget = self.pie_view
            file_name = "Круговая диаграмма.png"
        elif current_index == 2:
            chart_widget = self.bar_view
            file_name = "Столбчатая диаграмма.png"
        elif current_index == 3:
            chart_widget = self.line_view
            file_name = "Линейный график.png"
        else:
            return
        
        # Получаем папку для сохранения
        test_folder = self.folder_manager.get_test_folder()
        
        if not test_folder:
            # Если папка не выбрана — открываем диалог сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить график",
                file_name,
                "PNG Files (*.png)"
            )
            if not file_path:
                return
            output_path = file_path
        else:
            # Сохраняем в папку теста
            output_path = Path(test_folder) / file_name
        
        try:
            if chart_widget.save_to_png(str(output_path)):
                self._show_success_message("Успех", f"График сохранён в:\n{output_path}")
            else:
                self._show_error_message("Ошибка", "Нет данных для сохранения.\nВыберите шкалу для отображения.")
        except Exception as e:
            self._show_error_message("Ошибка", f"Не удалось сохранить график:\n{str(e)}")

    def _show_success_message(self, title, message):
        """Показывает сообщение об успехе"""
        self._show_message_box(title, message, "success")

    def _show_error_message(self, title, message):
        """Показывает сообщение об ошибке"""
        # Проверяем на дубликат
        if message == self._last_error_message:
            return  # Не показываем одинаковые ошибки подряд
        self._last_error_message = message
        self._show_message_box(title, message, "error")

    def _show_message_box(self, title, message, msg_type):
        """Показывает шаблонное сообщение"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
            QMessageBox QLabel {
                color: #000000;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
            QPushButton:pressed {
                background-color: #1E6BC5;
            }
        """)

        icon_label = QLabel()
        icon_label.setStyleSheet("background-color: transparent;")
        if msg_type == "success":
            icon_pixmap = QPixmap("resources/icons/attention-circle.svg")
        else:
            icon_pixmap = QPixmap("resources/icons/alert-triangle.svg")

        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(48, 48,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            icon_label.setPixmap(self.style().standardIcon(
                QMessageBox.Icon.Warning).pixmap(48, 48))
        layout = msg_box.layout()
        layout.addWidget(icon_label, 0, 0, 1, 1,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        msg_box.exec()

    def _update_table_view(self):
        """Обновляет таблицу с условным форматированием"""
        if self.table_df is None or self.table_df.empty:
            return

        self.table_view.setRowCount(0)
        self.table_view.setColumnCount(len(self.table_df.columns))
        self.table_view.setHorizontalHeaderLabels([str(col) for col in self.table_df.columns])

        for row_idx, (_, row) in enumerate(self.table_df.iterrows()):
            self.table_view.insertRow(row_idx)
            for col_idx, (col_name, value) in enumerate(row.items()):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                
                # Условное форматирование для шкал
                if col_name.startswith('Шкала_'):
                    value_str = str(value) if pd.notna(value) else ""
                    
                    # Выравнивание по центру
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Цвет фона в зависимости от уровня
                    if 'Низкий' in value_str:
                        item.setBackground(QBrush(QColor('#E8F5E9')))
                        item.setForeground(QBrush(QColor('#2E7D32')))
                    elif 'Средний' in value_str:
                        item.setBackground(QBrush(QColor('#FFF3E0')))
                        item.setForeground(QBrush(QColor('#EF6C00')))
                    elif 'Высокий' in value_str:
                        item.setBackground(QBrush(QColor('#FFEBEE')))
                        item.setForeground(QBrush(QColor('#C62828')))
                
                self.table_view.setItem(row_idx, col_idx, item)

        # Автоподбор ширины колонок
        self.table_view.resizeColumnsToContents()
        for col in range(self.table_view.columnCount()):
            current_width = self.table_view.columnWidth(col)
            if current_width < 100:
                self.table_view.setColumnWidth(col, 100)

    def clear_data(self):
        """Очищает данные из таблицы результатов."""
        self.table_df = None
        self.charts_data = {}
        self.summary_data = {}
        self.table_view.setRowCount(0)
        self.table_view.setColumnCount(5)
        self.table_view.setHorizontalHeaderLabels(["ID", "Респондент", "Дата", "Уровень", "Баллы"])

    def _load_processed_data(self):
        """Загружает данные из processed_data.xlsx"""
        if self.processed_file_path.exists():
            try:
                self.current_df = pd.read_excel(self.processed_file_path)
            except Exception as e:
                print(f"Ошибка загрузки данных: {e}")

    def _load_output_folder(self):
        """Загружает путь к папке вывода из настроек"""
        self.output_folder_path = self.folder_manager.get_base_folder()

    def set_filename(self, filename: str):
        """Обновляет название файла (для отображения)"""
        pass

    def get_current_sheet(self) -> str:
        """Возвращает текущий выбранный лист"""
        return self.current_sheet

    def set_nav_font_size(self, size: int):
        """Установить размер шрифта текста кнопок."""
        self._nav_font_size = size
        self.setStyleSheet(f"""
            ResultsNavButton {{
                background-color: transparent;
                border: none;
                min-width: 80px;
                max-width: 80px;
                min-height: 90px;
                max-height: 90px;
                border-radius: 70px;
                padding: 8px;
                font-size: {size}px;
            }}
            ResultsNavButton:hover {{
                background-color: #F4F4F5;
            }}
            ResultsNavButton:checked {{
                background-color: #b4d1ee;
            }}
            ResultsNavButton QLabel {{
                background-color: transparent;
            }}
            ResultsNavButton #nav_text {{
                font-size: {size}px;
            }}
        """)

    def set_nav_icon_size(self, size: int):
        """Установить размер иконок кнопок."""
        self._nav_icon_size = size
        for btn in self.nav_buttons:
            btn.icon_size = size
            btn._update_icon()
            btn.icon_label.setFixedSize(size, size)
            
    def _update_current_chart(self):
        """Обновляет данные в текущем активном графике."""
        index = self.views_stack.currentIndex()
        if index == 1:  # Pie chart
            self.pie_view.set_data(self.summary_data, self.charts_data, self.level_order, self.level_ru, self.scales_config, self.current_table_type)
        elif index == 2:  # Bar chart
            self.bar_view.set_data(self.summary_data, self.charts_data, self.level_order, self.level_ru, self.scales_config, self.current_table_type)
        elif index == 3:  # Line chart
            self.line_view.set_data(self.summary_data, self.charts_data, self.level_order, self.level_ru, self.scales_config, self.current_table_type)

    def export_to_excel(self):
        """Экспортирует результаты в Excel файл с группировкой и сводными таблицами."""
        if self.table_df is None or self.table_df.empty:
            self._show_error_message("Ошибка", "Нет данных для экспорта")
            return

        # Получаем папку для сохранения
        test_folder = self.folder_manager.get_test_folder()
        
        if not test_folder:
            # Если папка не выбрана — открываем диалог сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить результаты",
                "",
                "Excel Files (*.xlsx)"
            )
            if not file_path:
                return
            output_path = file_path
        else:
            # Сохраняем в папку теста
            test_name = self.folder_manager.get_test_name() or "Результаты"
            output_path = Path(test_folder) / f"{test_name}.xlsx"

        try:
            export_to_excel_with_summary(
                table_df=self.table_df,
                summary_data=self.summary_data,
                charts_data=self.charts_data,
                output_path=str(output_path)
            )

            self._show_success_message("Успех", f"Файл сохранён в:\n{output_path}")

        except Exception as e:
            self._show_error_message("Ошибка экспорта", f"Не удалось сохранить файл:\n{str(e)}")


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ТАБЛИЦЫ-АНАЛИЗ
# ============================================================================

def _create_diagonal_header(ws, row, col, level_order, level_ru, scales_config):
    """
    Создаёт ячейку "Шкала/Уровень" с диагональной границей.
    
    Структура:
    - Текст: 25 пробелов + "Уровень" + перенос + 2 пробела + "Шкалы"
    - Диагональ от левого верхнего до правого нижнего
    - Выравнивание: по левому краю (отступ)
    - Фиксированная ширина: 20.00 (145px)
    - Фиксированная высота: 37.50 (50px)
    """
    # Цвет фона ячейки (зелёный оттенок как у заголовков уровней)
    header_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
    black_color = "000000"  # Чёрный цвет для текста
    
    # Диагональная граница
    diagonal_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
        diagonal=Side(style="thin"),
        diagonalDown=True
    )
    
    # Создаём ячейку
    cell = ws.cell(row=row, column=col)
    
    # Текст: 25 пробелов + "Уровень" + перенос + 2 пробела + "Шкалы"
    cell.value = "                         Уровень\n  Шкалы"
    
    # Форматирование
    cell.fill = header_fill
    cell.border = diagonal_border
    cell.alignment = Alignment(
        horizontal="left",  # По левому краю (отступ)
        vertical="center",
        wrap_text=True
    )
    cell.font = Font(bold=True, size=11, color=black_color)
    
    # Фиксированная ширина колонки: 20.00
    ws.column_dimensions[get_column_letter(col)].width = 20.00
    
    # Фиксированная высота строки: 37.50
    ws.row_dimensions[row].height = 37.50
    
    return cell


def _write_analysis_table(ws, start_row, start_col, summary_data, total_respondents, 
                          level_order, level_ru, scales_config, group_name=None):
    """
    Записывает таблицу-анализ "Шкала/Уровни".
    
    Args:
        ws: Worksheet
        start_row: Начальная строка
        start_col: Начальная колонка
        summary_data: Данные сводной таблицы
        total_respondents: Общее количество респондентов
        level_order: Порядок уровней
        level_ru: Русские названия уровней
        scales_config: Конфигурация шкал
        group_name: Название группы/курса (если есть)
    """
    # Количество колонок = количество уровней + 1 (первая колонка "Шкала/Уровень")
    num_levels = len(level_order)
    num_cols = num_levels + 1
    
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    
    header_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
    group_fill = PatternFill(start_color="BBDEFB", end_color="BBDEFB", fill_type="solid")
    count_fill = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")
    
    current_row = start_row
    
    # Строка 1: Название группы/курса (объединённая ячейка)
    if group_name:
        end_col = start_col + num_cols - 1
        
        # Сначала объединяем ячейки
        ws.merge_cells(start_row=current_row, start_column=start_col, 
                      end_row=current_row, end_column=end_col)
        
        # Заполняем первую ячейку
        group_cell = ws.cell(row=current_row, column=start_col, value=str(group_name))
        group_cell.font = Font(bold=True, size=12)
        group_cell.alignment = Alignment(horizontal="center", vertical="center")
        group_cell.fill = group_fill
        
        # Применяем границу ко ВСЕМ ячейкам в объединённом диапазоне
        for c in range(start_col, end_col + 1):
            cell = ws.cell(row=current_row, column=c)
            cell.border = thin_border
        
        current_row += 1
    
    # Строка 2: Количество человек (объединённая ячейка)
    end_col = start_col + num_cols - 1
    
    # Сначала объединяем ячейки
    ws.merge_cells(start_row=current_row, start_column=start_col, 
                  end_row=current_row, end_column=end_col)
    
    # Заполняем первую ячейку
    count_text = f"Количество человек: {total_respondents}"
    count_cell = ws.cell(row=current_row, column=start_col, value=count_text)
    count_cell.font = Font(bold=True, size=11)
    count_cell.alignment = Alignment(horizontal="center", vertical="center")
    count_cell.fill = count_fill
    
    # Применяем границу ко ВСЕМ ячейкам в объединённом диапазоне
    for c in range(start_col, end_col + 1):
        cell = ws.cell(row=current_row, column=c)
        cell.border = thin_border
    
    current_row += 1
    
    # Строка 3: Заголовок "Шкала/Уровень" с диагональю + названия уровней
    _create_diagonal_header(ws, current_row, start_col, level_order, level_ru, scales_config)
    
    # Заголовки уровней
    for level_idx, level_key in enumerate(level_order):
        level_name = level_ru.get(level_key, level_key)
        cell = ws.cell(row=current_row, column=start_col + 1 + level_idx, value=level_name)
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.fill = header_fill
        cell.border = thin_border
    
    current_row += 1
    
    # Строки 4+: Данные по шкалам
    for scale_name, scale_config in scales_config.items():
        scale_title = scale_config.get("title_ru", scale_name)
        
        # Получаем данные из summary_data
        if scale_name in summary_data:
            scale_summary = summary_data[scale_name]
        else:
            # Если нет данных, создаём пустую строку
            scale_summary = {level_key: "0 чел./0%" for level_key in level_order}
        
        # Название шкалы
        cell = ws.cell(row=current_row, column=start_col, value=scale_title)
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border = thin_border
        
        # Значения по уровням
        for level_idx, level_key in enumerate(level_order):
            value = scale_summary.get(level_key, "0 чел./0%")
            cell = ws.cell(row=current_row, column=start_col + 1 + level_idx, value=value)
            cell.font = Font(size=11)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
        
        current_row += 1
    
    return current_row


def _build_analysis_summary(table_df, level_order, level_ru, scales_config):
    """
    Строит данные для таблицы-анализ из DataFrame.
    
    Returns:
        dict: {scale_name: {level_key: "N чел./X%", ...}, ...}
    """
    summary = {}
    total_respondents = len(table_df)
    
    # Обратный маппинг: русское название -> технический ключ
    ru_to_key = {v: k for k, v in level_ru.items()}
    
    for scale_name, scale_config in scales_config.items():
        scale_title = scale_config.get("title_ru", scale_name)
        level_col = f"Шкала_{scale_title}"
        
        if level_col not in table_df.columns:
            summary[scale_name] = {key: "0 чел./0%" for key in level_order}
            continue
        
        # Подсчитываем уровни
        level_counts = {key: 0 for key in level_order}
        
        for value in table_df[level_col].dropna():
            value_str = str(value)
            if " (" in value_str:
                level_name = value_str.split(" (")[0]
                level_key = ru_to_key.get(level_name)
                if level_key and level_key in level_counts:
                    level_counts[level_key] += 1
        
        # Форматируем
        summary[scale_name] = {}
        for level_key in level_order:
            count = level_counts.get(level_key, 0)
            percent = 0 if total_respondents == 0 else int(round(count / total_respondents * 100))
            summary[scale_name][level_key] = f"{count} чел./{percent}%"
    
    return summary


# ============================================================================
# ОСНОВНЫЕ ФУНКЦИИ ЭКСПОРТА
# ============================================================================


def export_to_excel_with_summary(
    table_df: pd.DataFrame,
    summary_data: Dict,
    charts_data: Dict,
    output_path: str
):
    """
    Создаёт Excel с динамическим количеством листов:
    1. Результат по всем респондентам + общая сводная таблица (всегда)
    2. Результат по курсам (сгруппировано) + сводные таблицы - если есть колонка "Курс"
    3. Результат по группам (сгруппировано) + сводные таблицы - если есть колонка "Группа"
    """
    wb = Workbook()

    # Удаляем стандартный лист
    if wb.active:
        wb.remove(wb.active)

    level_order = summary_data.get("level_order", [])
    level_ru = summary_data.get("level_ru", {})
    scales_config = summary_data.get("scales_config", {})
    has_group = summary_data.get("has_group", False)
    has_course = summary_data.get("has_course", False)

    # === ЛИСТ 1: Результат по всем респондентам (всегда) ===
    ws_all = wb.create_sheet("Результат по всем респондентам")
    _write_all_respondents_sheet(ws_all, table_df, summary_data, level_order, level_ru, scales_config)

    # === ЛИСТ 2: Результат по курсам (если есть колонка "Курс") ===
    if has_course and summary_data.get("course_summary"):
        ws_course = wb.create_sheet("Результат по курсам")
        _write_grouped_sheet(
            ws_course,
            table_df,
            summary_data.get("course_summary", {}),
            group_by="Курс",
            level_order=level_order,
            level_ru=level_ru,
            scales_config=scales_config
        )

    # === ЛИСТ 3: Результат по группам (если есть колонка "Группа") ===
    if has_group and summary_data.get("group_summary"):
        ws_group = wb.create_sheet("Результат по группам")
        _write_grouped_sheet(
            ws_group,
            table_df,
            summary_data.get("group_summary", {}),
            group_by="Группа",
            level_order=level_order,
            level_ru=level_ru,
            scales_config=scales_config
        )

    wb.save(output_path)


def _write_all_respondents_sheet(ws, table_df, summary_data, level_order, level_ru, scales_config):
    """Записывает лист 'Результат по всем респондентам'"""

    # Определяем колонки
    base_cols = ["Дата", "ФИО", "Группа", "Курс"]
    question_cols = [col for col in table_df.columns if col not in base_cols and not col.startswith("Шкала_")]
    scale_cols = [col for col in table_df.columns if col.startswith("Шкала_")]

    all_cols = base_cols + question_cols + scale_cols
    existing_cols = [col for col in all_cols if col in table_df.columns]

    # Создаём маппинг для переименования вопросов
    question_rename_map = {}
    for col in question_cols:
        if col.isdigit():
            question_rename_map[col] = f"Вопрос {col}"
        else:
            question_rename_map[col] = col

    # Заголовки с переименованием вопросов
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    for col_idx, col_name in enumerate(existing_cols, 1):
        display_name = question_rename_map.get(col_name, col_name)
        cell = ws.cell(row=1, column=col_idx, value=display_name)
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.fill = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")

    # Данные респондентов
    for row_idx, (_, row) in enumerate(table_df.iterrows(), 2):
        for col_idx, col_name in enumerate(existing_cols, 1):
            value = row.get(col_name, "")
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left", vertical="center")

    # Отступ 4 колонки между таблицами
    summary_start_col = len(existing_cols) + 5  # 4 пустые колонки + 1 для начала сводной

    # Строим данные для таблицы-анализ
    analysis_summary = _build_analysis_summary(table_df, level_order, level_ru, scales_config)
    total_respondents = len(table_df)

    # Записываем таблицу-анализ
    _write_analysis_table(
        ws=ws,
        start_row=1,
        start_col=summary_start_col,
        summary_data=analysis_summary,
        total_respondents=total_respondents,
        level_order=level_order,
        level_ru=level_ru,
        scales_config=scales_config,
        group_name=None  # По всем респондентам - без названия группы
    )


def _write_grouped_sheet(ws, table_df, summary_dict, group_by, level_order, level_ru, scales_config):
    """Записывает сгруппированный лист (Курс или Группа)"""

    # Определяем колонки
    base_cols = ["Дата", "ФИО", group_by, "Курс" if group_by == "Группа" else "Группа"]
    question_cols = [col for col in table_df.columns if col not in base_cols and not col.startswith("Шкала_")]
    scale_cols = [col for col in table_df.columns if col.startswith("Шкала_")]

    all_cols = base_cols + question_cols + scale_cols
    existing_cols = [col for col in all_cols if col in table_df.columns]

    # Создаём маппинг для переименования вопросов
    question_rename_map = {}
    for col in question_cols:
        if col.isdigit():
            question_rename_map[col] = f"Вопрос {col}"
        else:
            question_rename_map[col] = col

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    # Заголовки
    for col_idx, col_name in enumerate(existing_cols, 1):
        display_name = question_rename_map.get(col_name, col_name)
        cell = ws.cell(row=1, column=col_idx, value=display_name)
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.fill = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")

    current_row = 2
    
    # Группируем данные
    grouped = table_df.groupby(group_by, dropna=False)
    group_names = list(grouped.groups.keys())
    
    # Записываем данные по каждой группе
    for group_idx, group_name in enumerate(group_names):
        group_df = grouped.get_group(group_name)
        
        end_col = len(existing_cols)
        
        # Сначала объединяем ячейки
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=end_col)
        
        # Заполняем первую ячейку
        group_cell = ws.cell(row=current_row, column=1, value=str(group_name) if pd.notna(group_name) else "Без группы")
        group_cell.font = Font(bold=True, size=12)
        group_cell.alignment = Alignment(horizontal="center", vertical="center")
        group_cell.fill = PatternFill(start_color="BBDEFB", end_color="BBDEFB", fill_type="solid")
        
        # Применяем границу ко ВСЕМ ячейкам в объединённом диапазоне
        for c in range(1, end_col + 1):
            cell = ws.cell(row=current_row, column=c)
            cell.border = thin_border

        current_row += 1

        # Данные респондентов
        for _, row in group_df.iterrows():
            for col_idx, col_name in enumerate(existing_cols, 1):
                value = row.get(col_name, "")
                cell = ws.cell(row=current_row, column=col_idx, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="left", vertical="center")
            current_row += 1

        # Отступ 4 строки перед следующей группой
        current_row += 4
    
    # Теперь записываем таблицы-анализ ВЕРТИКАЛЬНО (друг под другом) с отступом 4 строки
    # Начинаем с первой строки, колонка после основной таблицы
    summary_start_col = len(existing_cols) + 5  # 4 пустые колонки + 1
    current_summary_row = 1
    
    for group_name in group_names:
        group_df = grouped.get_group(group_name)
        total_in_group = len(group_df)
        
        # Строим данные для таблицы-анализ этой группы
        analysis_summary = _build_analysis_summary(group_df, level_order, level_ru, scales_config)
        
        # Записываем таблицу-анализ
        end_row = _write_analysis_table(
            ws=ws,
            start_row=current_summary_row,
            start_col=summary_start_col,
            summary_data=analysis_summary,
            total_respondents=total_in_group,
            level_order=level_order,
            level_ru=level_ru,
            scales_config=scales_config,
            group_name=str(group_name) if pd.notna(group_name) else "Без группы"
        )
        
        # Отступ 4 строки перед следующей таблицей-анализ
        current_summary_row = end_row + 4


def _build_overall_summary(table_df, level_order, level_ru, scales_config):
    """Строит общую сводную таблицу распределения"""
    rows = []
    total_respondents = len(table_df)
    
    # Обратный маппинг: русское название -> технический ключ
    ru_to_key = {v: k for k, v in level_ru.items()}

    for scale_name, scale_config in scales_config.items():
        scale_title = scale_config.get("title_ru", scale_name)

        # Находим колонку уровня для этой шкалы
        level_col = f"Шкала_{scale_title}"
        if level_col not in table_df.columns:
            continue

        # Подсчитываем уровни, извлекая их из строки вида "Низкий (11 баллов)"
        level_counts = {key: 0 for key in level_order}
        
        for value in table_df[level_col].dropna():
            # Извлекаем название уровня из строки "Низкий (11 баллов)"
            # Формат: "{Уровень} ({N} баллов)"
            value_str = str(value)
            if " (" in value_str:
                level_name = value_str.split(" (")[0]
                # Сопоставляем с техническим ключом
                level_key = ru_to_key.get(level_name)
                if level_key and level_key in level_counts:
                    level_counts[level_key] += 1

        row = {"Шкала": scale_title}
        for level_key in level_order:
            count = level_counts.get(level_key, 0)
            percent = 0 if total_respondents == 0 else int(round(count / total_respondents * 100))
            row[level_ru.get(level_key, level_key)] = f"{count} чел./{percent}%"

        rows.append(row)

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _write_summary_table(ws, summary_df, start_row, start_column):
    """Записывает сводную таблицу распределения"""
    if summary_df.empty:
        return
    
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    
    # Заголовки уровней
    level_cols = [col for col in summary_df.columns if col != "Шкала"]
    
    # Заголовок "Шкала"
    cell = ws.cell(row=start_row, column=start_column, value="Шкала")
    cell.font = Font(bold=True, size=11)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
    cell.border = thin_border
    
    # Заголовки уровней
    for col_idx, level_name in enumerate(level_cols, 1):
        cell = ws.cell(row=start_row, column=start_column + col_idx, value=level_name)
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
        cell.border = thin_border
    
    # Данные
    for row_idx, (_, row) in enumerate(summary_df.iterrows(), 1):
        # Шкала
        cell = ws.cell(row=start_row + row_idx, column=start_column, value=row["Шкала"])
        cell.font = Font(bold=True, size=10)
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border = thin_border
        
        # Уровни
        for col_idx, level_name in enumerate(level_cols, 1):
            cell = ws.cell(row=start_row + row_idx, column=start_column + col_idx, value=row[level_name])
            cell.font = Font(size=10)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
            

