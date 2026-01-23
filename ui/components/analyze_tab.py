from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QStackedWidget, QScrollArea, QComboBox, QLineEdit, QCheckBox
)
from ui.components.excel_preview import ExcelPreviewTable
import pandas as pd
from PyQt6.QtCore import Qt
from typing import List, Set

class AnalyzeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path: str = None
        self.sheet_names: List[str] = []
        self.current_directions: Set[str] = set()
        self.current_courses: Set[int] = set()
        self.current_groups: Set[str] = set()
        
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Левая панель
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(10, 10, 10, 10)

        self.load_button = QPushButton("Выбрать файл")
        self.load_button.setObjectName("selectFileButton")
        self.load_button.clicked.connect(self.load_file)
        left_layout.addWidget(self.load_button)

        self.sheet_label = QLabel("Лист:")
        self.sheet_combo = QComboBox()
        self.sheet_combo.setEnabled(False)
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)
        left_layout.addWidget(self.sheet_label)
        left_layout.addWidget(self.sheet_combo)

        self.view_button = QPushButton("Просмотр данных")
        self.view_button.setEnabled(False)
        self.view_button.clicked.connect(self.show_view)
        left_layout.addWidget(self.view_button)

        self.chart_button = QPushButton("Построение диаграмм")
        self.chart_button.setEnabled(False)
        self.chart_button.clicked.connect(self.show_charts)
        left_layout.addWidget(self.chart_button)

        self.status_label = QLabel("Загрузите файл")
        self.status_label.setFixedHeight(30)
        self.status_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        left_layout.addStretch()
        left_layout.addWidget(self.status_label)

        main_layout.addWidget(left_panel, 1)

        # Правая область
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 3)

        self.create_empty_screen()
        self.create_view_screen()
        self.create_chart_screen()

    def create_empty_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel("Загрузите обработанный Excel-файл")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        widget.setLayout(layout)
        self.stacked_widget.addWidget(widget)

    def create_view_screen(self):
        widget = QWidget()
        main_layout = QVBoxLayout()
        widget.setLayout(main_layout)

        # Панель направлений
        self.direction_layout = QHBoxLayout()
        direction_panel = QWidget()
        direction_panel.setLayout(self.direction_layout)
        main_layout.addWidget(direction_panel)

        # Панель курсов
        self.course_layout = QHBoxLayout()
        course_panel = QWidget()
        course_panel.setLayout(self.course_layout)
        main_layout.addWidget(course_panel)

        # Панель групп
        self.group_layout = QHBoxLayout()
        group_panel = QWidget()
        group_panel.setLayout(self.group_layout)
        main_layout.addWidget(group_panel)

        # Таблица
        self.view_table = ExcelPreviewTable()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.view_table)
        scroll_area.setMinimumHeight(300)
        main_layout.addWidget(scroll_area)

        # Правая панель фильтров
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        right_layout.addWidget(QLabel("Поиск по ФИО:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите имя...")
        self.search_input.textChanged.connect(self.apply_filters)
        right_layout.addWidget(self.search_input)
        
        right_layout.addWidget(QLabel("Уровень риска:"))
        self.risk_filter = QComboBox()
        self.risk_filter.addItems(["Все", "Низкий", "Средний", "Высокий"])
        self.risk_filter.currentTextChanged.connect(self.apply_filters)
        right_layout.addWidget(self.risk_filter)
        
        right_layout.addStretch()
        main_layout.addWidget(right_panel, 1)

        self.stacked_widget.addWidget(widget)

    def create_chart_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        label = QLabel("Здесь будут диаграммы")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.stacked_widget.addWidget(widget)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать обработанный файл", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            try:
                self.file_path = file_path
                excel_file = pd.ExcelFile(file_path)
                self.sheet_names = excel_file.sheet_names
                
                self.view_button.setEnabled(True)
                self.chart_button.setEnabled(True)
                self.sheet_combo.clear()
                self.sheet_combo.addItems(self.sheet_names)
                self.sheet_combo.setEnabled(True)
                
                if self.sheet_names:
                    self.on_sheet_changed(self.sheet_names[0])
                
            except Exception as e:
                self.status_label.setText(f"Ошибка: {str(e)}")

    def on_sheet_changed(self, sheet_name: str):
        if not hasattr(self, 'file_path') or not sheet_name:
            return
        
        try:
            df = pd.read_excel(self.file_path, sheet_name=sheet_name)
            self._full_data = df
            self.view_table.load_dataframe(df)
            self.status_label.setText(f"Лист: {sheet_name}")
            
            self.update_filters_from_data(df)
            
        except Exception as e:
            self.status_label.setText(f"Ошибка загрузки листа: {str(e)}")

    def update_filters_from_data(self, df: pd.DataFrame):
        # Очистка старых чекбоксов
        for layout in [self.direction_layout, self.course_layout, self.group_layout]:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        directions = set()
        courses = set()
        groups = set()
        
        # Определяем тип листа
        is_course_sheet = "курс" in df.iloc[0, 0].lower() if df.shape[0] > 0 and isinstance(df.iloc[0, 0], str) else False
        is_direction_sheet = df.iloc[0, 0] in ["ПМИ", "МКН", "ПИЖ", "ФИТ", "БИО"] if df.shape[0] > 0 else False
        
        # Сбор данных из реальных строк студентов
        for _, row in df.iterrows():
            if not isinstance(row["ФИО"], str) or pd.isna(row["ФИО"]):
                continue
            
            # Пропускаем заголовочные строки
            if isinstance(row["ФИО"], str) and ("курс" in row["ФИО"].lower() or row["ФИО"] in ["ПМИ", "МКН", "ПИЖ", "ФИТ", "БИО"]):
                continue
            
            if "Направление" in df.columns and pd.notna(row["Направление"]):
                directions.add(str(row["Направление"]))
            if "Курс" in df.columns and pd.notna(row["Курс"]):
                courses.add(int(row["Курс"]))
            if "Группа" in df.columns and pd.notna(row["Группа"]):
                groups.add(str(row["Группа"]))
        
        # Создание чекбоксов
        self._create_checkboxes(self.direction_layout, directions, self.on_direction_changed)
        self._create_checkboxes(self.course_layout, courses, self.on_course_changed)
        self._create_checkboxes(self.group_layout, groups, self.on_group_changed)

    def _create_checkboxes(self, layout, items, callback):
        for item in sorted(items):
            cb = QCheckBox(str(item))
            cb.stateChanged.connect(lambda state, val=item: callback(val, state))
            layout.addWidget(cb)
        layout.addStretch()

    def on_direction_changed(self, direction: str, state: int):
        if state == Qt.CheckState.Checked.value:
            self.current_directions.add(direction)
        else:
            self.current_directions.discard(direction)
        self.apply_filters()

    def on_course_changed(self, course: int, state: int):
        if state == Qt.CheckState.Checked.value:
            self.current_courses.add(course)
        else:
            self.current_courses.discard(course)
        self.apply_filters()

    def on_group_changed(self, group: str, state: int):
        if state == Qt.CheckState.Checked.value:
            self.current_groups.add(group)
        else:
            self.current_groups.discard(group)
        self.apply_filters()

    def apply_filters(self):
        if not hasattr(self, '_full_data') or self._full_data is None:
            return
        
        df = self._full_data.copy()
        
        # Поиск по ФИО
        search_text = self.search_input.text().strip().lower()
        if search_text:
            df = df[df['ФИО'].str.lower().str.contains(search_text, na=False, regex=False)]
        
        # Фильтр по направлению
        if self.current_directions:
            df = df[df["Направление"].isin(self.current_directions)]
        
        # Фильтр по курсу
        if self.current_courses:
            df = df[df["Курс"].isin(self.current_courses)]
        
        # Фильтр по группе
        if self.current_groups:
            df = df[df["Группа"].isin(self.current_groups)]
        
        # Уровень риска
        risk_level = self.risk_filter.currentText()
        if risk_level != "Все" and "Risk Level" in df.columns:
            risk_map = {"Низкий": "Low Risk", "Средний": "Medium Risk", "Высокий": "High Risk"}
            df = df[df['Risk Level'] == risk_map.get(risk_level, risk_level)]
        
        df = df.reset_index(drop=True)
        self.view_table.load_dataframe(df)

    def show_view(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_charts(self):
        self.stacked_widget.setCurrentIndex(2)