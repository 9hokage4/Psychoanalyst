# -*- coding: utf-8 -*-
# ui/components/results_widget.py
import pandas as pd
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
from PyQt6.QtGui import QColor, QFont, QBrush
from utils.fonts import get_font, FontWeights
from ui.components.results_nav_button import ResultsNavButton
from utils.excel_export import ExcelExporter


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
        self.setup_ui()
        self._load_processed_data()

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
        
        # Кнопка "Открыть в Excel"
        open_excel_btn = QPushButton("📊 Открыть в Excel")
        open_excel_btn.setFixedHeight(44)
        open_excel_btn.setFont(get_font("button", size=16, weight=FontWeights.SEMIBOLD))
        open_excel_btn.setStyleSheet("""
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
        open_excel_btn.clicked.connect(self.open_in_excel)
        button_row.addWidget(open_excel_btn)
        
        # Кнопка "Экспорт в Excel"
        export_btn = QPushButton("💾 Экспорт в Excel")
        export_btn.setFixedHeight(44)
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
        self.selector_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 14px;
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
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
        """Обработчик смены типа таблицы"""
        self.current_table_type = table_type
        self.table_type_changed.emit(table_type)
        self._update_table_view()

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
        
        # Улучшенные стили
        table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: none;
                gridline-color: #E0E0E0;
                gridline-width: 1px;
                show-decoration-selected: 0;
                font-size: 13px;
                font-family: 'Segoe UI', Arial;
                alternate-background-color: #FAFAFA;
            }
            
            QTableWidget::item {
                padding: 10px 12px;
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
        if index == 0:
            # Таблица - показываем selector только если есть группы/курсы
            self.selector_label.setText("📊 Тип таблицы:")
            self.selector_widget.setVisible(self.has_group or self.has_course)
        else:
            # Графики - всегда показываем selector для выбора шкалы
            self.selector_label.setText("📊 Выберите шкалу:")
            self.selector_widget.setVisible(True)

        # Обновляем данные в графиках
        if index == 1:
            self.pie_view.set_data(self.charts_data, self.level_order, self.level_ru)
        elif index == 2:
            self.bar_view.set_data(self.charts_data, self.level_order, self.level_ru)
        elif index == 3:
            self.line_view.set_data(self.charts_data, self.level_order, self.level_ru)

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

        # Динамически заполняем selector в зависимости от наличия данных
        self.selector_combo.clear()
        self.selector_combo.addItem("Все респонденты")
        if self.has_course:
            self.selector_combo.addItem("Курс")
        if self.has_group:
            self.selector_combo.addItem("Группа")
        
        # Если нет ни групп ни курсов, скрываем selector
        self.selector_widget.setVisible(self.has_group or self.has_course)

        # Обновляем таблицу
        self._update_table_view()

    def open_in_excel(self):
        """Открывает данные в Microsoft Excel"""
        if self.table_df is None or self.table_df.empty:
            QMessageBox.warning(self, "Ошибка", "Нет данных для открытия")
            return
        
        # Экспортируем и открываем в Excel
        if self.excel_exporter.export_and_open(self.table_df):
            QMessageBox.information(
                self,
                "Успех",
                "Данные открыты в Excel.\n\n"
                "Примечание: Файл сохранён во временной папке.\n"
                "Не забудьте сохранить его в нужном месте!"
            )
        else:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось открыть данные в Excel.\n\n"
                "Убедитесь, что Microsoft Excel установлен."
            )

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

    def export_to_excel(self):
        """Экспортирует результаты в Excel файл с группировкой и сводными таблицами."""
        if self.table_df is None or self.table_df.empty:
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта")
            return

        # Диалог сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты",
            "",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            export_to_excel_with_summary(
                table_df=self.table_df,
                summary_data=self.summary_data,
                charts_data=self.charts_data,
                output_path=file_path
            )

            QMessageBox.information(
                self,
                "Успех",
                f"Результаты успешно сохранены в:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Не удалось сохранить файл:\n{str(e)}"
            )


def export_to_excel_with_summary(
    table_df: pd.DataFrame,
    summary_data: Dict,
    charts_data: Dict,
    output_path: str
):
    """
    Создаёт Excel с динамическим количеством листов:
    1. Все респонденты + общая сводная таблица (всегда)
    2. Курс (сгруппировано) + сводные таблицы - если есть колонка "Курс"
    3. Группа (сгруппировано) + сводные таблицы - если есть колонка "Группа"
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

    # === ЛИСТ 1: Все респонденты (всегда) ===
    ws_all = wb.create_sheet("Все респонденты")
    _write_all_respondents_sheet(ws_all, table_df, summary_data, level_order, level_ru, scales_config)

    # === ЛИСТ 2: Курс (если есть колонка "Курс") ===
    if has_course and summary_data.get("course_summary"):
        ws_course = wb.create_sheet("Курс")
        _write_grouped_sheet(
            ws_course,
            table_df,
            summary_data.get("course_summary", {}),
            group_by="Курс",
            level_order=level_order,
            level_ru=level_ru,
            scales_config=scales_config
        )

    # === ЛИСТ 3: Группа (если есть колонка "Группа") ===
    if has_group and summary_data.get("group_summary"):
        ws_group = wb.create_sheet("Группа")
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
    """Записывает лист 'Все респонденты' с общей сводной таблицей"""
    
    # Определяем колонки
    base_cols = ["Дата", "ФИО", "Группа", "Курс"]
    question_cols = [col for col in table_df.columns if col not in base_cols and not col.startswith("Шкала_")]
    scale_cols = [col for col in table_df.columns if col.startswith("Шкала_")]
    
    all_cols = base_cols + question_cols + scale_cols
    existing_cols = [col for col in all_cols if col in table_df.columns]
    
    # Заголовки
    for col_idx, col_name in enumerate(existing_cols, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.fill = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")
    
    # Данные
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    
    for row_idx, (_, row) in enumerate(table_df.iterrows(), 2):
        for col_idx, col_name in enumerate(existing_cols, 1):
            value = row.get(col_name, "")
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left", vertical="center")
    
    # Сводная таблица справа вверху
    summary_table = _build_overall_summary(table_df, level_order, level_ru, scales_config)
    _write_summary_table(ws, summary_table, start_row=1, start_column=len(existing_cols) + 2)


def _write_grouped_sheet(ws, table_df, summary_dict, group_by, level_order, level_ru, scales_config):
    """Записывает сгруппированный лист (Курс или Группа)"""
    
    current_row = 1
    
    # Определяем колонки
    base_cols = ["Дата", "ФИО", group_by, "Курс" if group_by == "Группа" else "Группа"]
    scale_cols = [col for col in table_df.columns if col.startswith("Шкала_")]
    
    all_cols = base_cols + scale_cols
    existing_cols = [col for col in all_cols if col in table_df.columns]
    
    # Общая сводная таблица для всех групп/курсов
    overall_summary = _build_overall_summary(table_df, level_order, level_ru, scales_config)
    _write_summary_table(ws, overall_summary, start_row=1, start_column=len(existing_cols) + 2)
    
    # Заголовки
    for col_idx, col_name in enumerate(existing_cols, 1):
        cell = ws.cell(row=3, column=col_idx, value=col_name)
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.fill = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")
    
    current_row = 4
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    
    # Группируем данные
    grouped = table_df.groupby(group_by, dropna=False)
    
    for group_idx, (group_name, group_df) in enumerate(grouped):
        # Объединённая ячейка с названием группы/курса
        merge_start = current_row
        merge_end = current_row + len(group_df)
        
        # Записываем объединённую ячейку
        ws.merge_cells(start_row=merge_start, start_column=1, end_row=merge_start, end_column=len(existing_cols))
        group_cell = ws.cell(row=merge_start, column=1, value=str(group_name) if pd.notna(group_name) else "Без группы")
        group_cell.font = Font(bold=True, size=12)
        group_cell.alignment = Alignment(horizontal="center", vertical="center")
        group_cell.fill = PatternFill(start_color="BBDEFB", end_color="BBDEFB", fill_type="solid")
        group_cell.border = thin_border
        
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


def _build_overall_summary(table_df, level_order, level_ru, scales_config):
    """Строит общую сводную таблицу распределения"""
    rows = []
    total_respondents = len(table_df)
    
    for scale_name, scale_config in scales_config.items():
        scale_title = scale_config.get("title_ru", scale_name)
        
        # Находим колонку уровня для этой шкалы
        level_col = f"Шкала_{scale_title}"
        if level_col not in table_df.columns:
            continue
        
        level_counts = table_df[level_col].value_counts(dropna=False).to_dict()
        
        row = {"Шкала": scale_title}
        for level_key in level_order:
            count = int(level_counts.get(level_key, 0))
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
