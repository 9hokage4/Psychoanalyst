# -*- coding: utf-8 -*-
# ui/components/results_widget.py
import pandas as pd
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QFileDialog, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from utils.fonts import get_font, FontWeights
from ui.components.results_nav_button import ResultsNavButton


class ResultsWidget(QWidget):
    sheet_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_sheet = "Все листы"
        self.current_df = None
        self.processed_file_path = Path("processed_data.xlsx")
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
        self.sidebar.setFixedSize(140, 450)  # Фиксированный размер как было изначально

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

        # Выбор листа Excel
        self.sheet_selector_widget = self._create_sheet_selector()
        content_layout.addWidget(self.sheet_selector_widget)

        # Стек видов (растягивается на всю доступную высоту)
        self.views_stack = QStackedWidget()
        self.views_stack.setObjectName("views_stack")
        self.views_stack.setStyleSheet("background-color: transparent;")
        self.views_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Таблица
        self.table_view = self._create_table_view()
        self.views_stack.addWidget(self.table_view)

        # Круговая диаграмма (заглушка)
        self.pie_view = self._create_chart_placeholder(
            "🥧",
            "Круговая диаграмма",
            ["Распределение уровней", "По шкалам"]
        )
        self.views_stack.addWidget(self.pie_view)

        # Столбчатая диаграмма (заглушка)
        self.bar_view = self._create_chart_placeholder(
            "📊",
            "Столбчатая диаграмма",
            ["Сравнение показателей", "По респондентам"]
        )
        self.views_stack.addWidget(self.bar_view)

        # Линейный график (заглушка)
        self.line_view = self._create_chart_placeholder(
            "📈",
            "Линейный график",
            ["Динамика показателей"]
        )
        self.views_stack.addWidget(self.line_view)

        content_layout.addWidget(self.views_stack)
        results_layout.addWidget(content_widget)

        main_layout.addWidget(results_container)

        # ===== КНОПКА ЭКСПОРТА =====
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
        main_layout.addWidget(export_btn)

        # ===== СТИЛИ ДЛЯ КНОПОК НАВИГАЦИИ =====
        # Задаём глобальные стили для кастомных кнопок
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

    def _create_sheet_selector(self) -> QWidget:
        """Создаёт выпадающий список выбора листа"""
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        sheet_label = QLabel("📊 Лист Excel:")
        sheet_label.setFont(get_font("form_label"))
        sheet_label.setStyleSheet("color: #707579; background-color: transparent;")

        self.sheet_combo = QComboBox()
        self.sheet_combo.setObjectName("sheet_selector")
        self.sheet_combo.setFont(get_font("form_input"))
        self.sheet_combo.addItems(["Все листы", "По курсу", "Предварительный", "Итоговый"])
        self.sheet_combo.currentTextChanged.connect(self._on_sheet_changed)
        self.sheet_combo.setStyleSheet("""
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

        layout.addWidget(sheet_label)
        layout.addWidget(self.sheet_combo)
        layout.addStretch()

        return widget

    def _on_sheet_changed(self, sheet_name: str):
        """Обработчик смены листа"""
        self.current_sheet = sheet_name
        self.sheet_changed.emit(sheet_name)

    def _create_table_view(self) -> QTableWidget:
        """Создаёт таблицу результатов"""
        table = QTableWidget()
        table.setObjectName("results_table")
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "Респондент", "Дата", "Уровень", "Баллы"])

        table.setRowCount(0)

        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setDragEnabled(False)
        
        # Плавная прокрутка (как в Excel)
        table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                gridline-color: #DFE1E5;
                show-decoration-selected: 0;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #DFE1E5;
                background-color: transparent;
            }
            QTableWidget::item:hover {
                background-color: #F4F4F5;
            }
            QTableWidget::item:focus {
                background-color: #E3F2FD;
            }
            QTableWidget::item:selected {
                background-color: #B3D9F5;
                color: #000000;
            }
            QHeaderView::section {
                background-color: transparent;
                color: #707579;
                font-size: 13px;
                font-weight: 600;
                padding: 12px;
                border: none;
                border-bottom: 1px solid #DFE1E5;
            }
            QScrollBar:vertical {
                background-color: #F0F0F0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #C4C9CC;
                border-radius: 5px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #A0A5A9;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #F0F0F0;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background-color: #C4C9CC;
                border-radius: 5px;
                min-width: 40px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #A0A5A9;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        return table

    def _create_badge(self, text: str, level: str) -> QWidget:
        """Создаёт бейдж уровня (Низкий/Средний/Высокий)"""
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)

        label = QLabel(text)
        label.setWordWrap(False)
        label.setStyleSheet("background-color: transparent;")

        if level == "success":
            label.setStyleSheet("""
                QLabel {
                    background-color: #E8F5E9;
                    color: #2E7D32;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: 600;
                }
            """)
        elif level == "warning":
            label.setStyleSheet("""
                QLabel {
                    background-color: #FFF3E0;
                    color: #EF6C00;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: 600;
                }
            """)
        elif level == "danger":
            label.setStyleSheet("""
                QLabel {
                    background-color: #FFEBEE;
                    color: #C62828;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: 600;
                }
            """)

        layout.addWidget(label)
        layout.addStretch()

        return widget

    def _create_chart_placeholder(self, icon: str, title: str, subtitles: list) -> QWidget:
        """Создаёт заглушку для графика"""
        widget = QWidget()
        widget.setObjectName("chart_placeholder")

        if len(subtitles) == 1:
            # Один блок на всю ширину
            layout = QVBoxLayout(widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setSpacing(12)

            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 64px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            title_label = QLabel(title)
            title_label.setFont(get_font("section_title"))
            title_label.setStyleSheet("color: #000000; background-color: transparent;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            subtitle_label = QLabel(subtitles[0])
            subtitle_label.setFont(get_font("caption"))
            subtitle_label.setStyleSheet("color: #707579; background-color: transparent;")
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            layout.addWidget(icon_label)
            layout.addWidget(title_label)
            layout.addWidget(subtitle_label)
        else:
            # Сетка 1fr 1fr
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(20)

            grid_widget = QWidget()
            grid_layout = QHBoxLayout(grid_widget)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(20)

            for subtitle in subtitles:
                placeholder = QWidget()
                placeholder.setObjectName("chart_placeholder_item")
                placeholder.setStyleSheet("""
                    QWidget#chart_placeholder_item {
                        background-color: #F8F9FA;
                        border: 1px solid #DFE1E5;
                        border-radius: 8px;
                    }
                """)
                placeholder.setMinimumHeight(250)

                ph_layout = QVBoxLayout(placeholder)
                ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                ph_layout.setSpacing(12)

                ph_icon = QLabel(icon)
                ph_icon.setStyleSheet("font-size: 48px;")
                ph_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

                ph_title = QLabel(subtitle)
                ph_title.setFont(get_font("caption"))
                ph_title.setStyleSheet("color: #707579; background-color: transparent;")
                ph_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

                ph_layout.addWidget(ph_icon)
                ph_layout.addWidget(ph_title)

                grid_layout.addWidget(placeholder)

            layout.addWidget(grid_widget)

        return widget

    def _switch_view(self, index: int):
        """Переключает вид (таблица/графики)"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.views_stack.setCurrentIndex(index)

    def set_data(self, df):
        """Устанавливает данные из pandas DataFrame (результаты процессора)"""
        if df is None or df.empty:
            return

        self.current_df = df

        # Очистка таблицы
        self.table_view.setRowCount(0)
        self.table_view.setColumnCount(len(df.columns))
        self.table_view.setHorizontalHeaderLabels([str(col) for col in df.columns])

        # Заполнение из DataFrame
        for row_idx, (_, row) in enumerate(df.iterrows()):
            self.table_view.insertRow(row_idx)
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                self.table_view.setItem(row_idx, col_idx, item)

        # Автоподбор ширины колонок по содержимому
        self.table_view.resizeColumnsToContents()
        
        # Устанавливаем минимальную ширину для колонок
        for col in range(self.table_view.columnCount()):
            current_width = self.table_view.columnWidth(col)
            if current_width < 100:
                self.table_view.setColumnWidth(col, 100)

    def clear_data(self):
        """Очищает данные из таблицы результатов."""
        self.current_df = None
        self.table_view.setRowCount(0)
        self.table_view.setColumnCount(5)
        self.table_view.setHorizontalHeaderLabels(["ID", "Респондент", "Дата", "Уровень", "Баллы"])

    def _get_level_type(self, level: str) -> str:
        """Определяет тип уровня для бейджа"""
        level_lower = level.lower()
        if 'низк' in level_lower:
            return 'success'
        elif 'средн' in level_lower:
            return 'warning'
        elif 'высок' in level_lower:
            return 'danger'
        return 'warning'

    def _load_processed_data(self):
        """Загружает данные из processed_data.xlsx"""
        if self.processed_file_path.exists():
            try:
                self.current_df = pd.read_excel(self.processed_file_path)
                self._populate_table_from_df()
            except Exception as e:
                print(f"Ошибка загрузки данных: {e}")

    def _populate_table_from_df(self):
        """Заполняет таблицу данными из DataFrame"""
        if self.current_df is None or self.current_df.empty:
            return

        self.table_view.setRowCount(0)

        for row_idx, row in self.current_df.iterrows():
            self.table_view.insertRow(row_idx)

            # ID (индекс + 1)
            item = QTableWidgetItem(f'#{row_idx + 1}')
            self.table_view.setItem(row_idx, 0, item)

            # ФИО
            fio = row.get('ФИО', 'Unknown')
            item = QTableWidgetItem(str(fio))
            self.table_view.setItem(row_idx, 1, item)

            # Дата
            date = row.get('Дата', '')
            if pd.notna(date):
                item = QTableWidgetItem(str(date))
            else:
                item = QTableWidgetItem('')
            self.table_view.setItem(row_idx, 2, item)

            # Уровень риска (Risk Level)
            risk_level = row.get('Risk Level', 'Не определено')
            level_type = self._get_level_type(str(risk_level))
            badge_widget = self._create_badge(str(risk_level), level_type)
            self.table_view.setCellWidget(row_idx, 3, badge_widget)

            # % риска (баллы)
            risk_percent = row.get('% риска', '0')
            item = QTableWidgetItem(str(risk_percent))
            self.table_view.setItem(row_idx, 4, item)

    def refresh_data(self):
        """Обновляет данные из processed_data.xlsx"""
        self._load_processed_data()

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
        """Экспортирует результаты в Excel файл."""
        if self.current_df is None or self.current_df.empty:
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
            # Создаём Excel writer с несколькими листами
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Лист 1: Индивидуальные результаты
                self.current_df.to_excel(writer, sheet_name='Результаты', index=False)

                # Лист 2: Сводки (если есть в атрибутах)
                if hasattr(self.current_df, 'attrs') and 'сводки' in self.current_df.attrs:
                    summaries = self.current_df.attrs['сводки']
                    
                    if 'длинная_таблица' in summaries:
                        summaries['длинная_таблица'].to_excel(
                            writer, 
                            sheet_name='Сводка по группам', 
                            index=False
                        )
                    
                    if 'широкая_таблица' in summaries:
                        summaries['широкая_таблица'].to_excel(
                            writer, 
                            sheet_name='Сводка для отчёта', 
                            index=False
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