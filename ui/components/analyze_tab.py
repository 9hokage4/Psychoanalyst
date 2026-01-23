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

        # * Панель направлений + поиск по ФИО
        direction_row = QHBoxLayout()
        direction_panel = QWidget()
        direction_layout = QHBoxLayout()
        direction_panel.setLayout(direction_layout)
        direction_row.addWidget(direction_panel, 3)  # 3 части ширины
        
        # * Поиск по ФИО (справа от направлений)
        search_layout = QVBoxLayout()
        search_layout.addWidget(QLabel("Поиск по ФИО:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите имя...")
        self.search_input.textChanged.connect(self.apply_filters)
        search_layout.addWidget(self.search_input)
        direction_row.addLayout(search_layout, 1)  # 1 часть ширины
        main_layout.addLayout(direction_row)

        # * Панель курсов + уровень риска
        course_row = QHBoxLayout()
        course_panel = QWidget()
        course_layout = QHBoxLayout()
        course_panel.setLayout(course_layout)
        course_row.addWidget(course_panel, 3)
        
        # * Уровень риска (справа от курсов)
        risk_layout = QVBoxLayout()
        risk_layout.addWidget(QLabel("Уровень риска:"))
        self.risk_filter = QComboBox()
        self.risk_filter.addItems(["Все", "Низкий", "Средний", "Высокий"])
        self.risk_filter.currentTextChanged.connect(self.apply_filters)
        risk_layout.addWidget(self.risk_filter)
        course_row.addLayout(risk_layout, 1)
        main_layout.addLayout(course_row)

        # * Панель групп
        group_row = QHBoxLayout()
        group_panel = QWidget()
        group_layout = QHBoxLayout()
        group_panel.setLayout(group_layout)
        group_row.addWidget(group_panel, 3)
        
        # * Пустое пространство справа от групп
        group_row.addStretch(1)
        main_layout.addLayout(group_row)

        # * Сохраняем layout'ы для обновления
        self.direction_layout = direction_layout
        self.course_layout = course_layout
        self.group_layout = group_layout

        # * Таблица
        self.view_table = ExcelPreviewTable()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.view_table)
        scroll_area.setMinimumHeight(300)
        main_layout.addWidget(scroll_area)

        self.stacked_widget.addWidget(widget)
        
    def create_chart_screen(self):
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # * Холст для диаграмм
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

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
            self.update_charts(df)  # ← Добавлено!
            
        except Exception as e:
            self.status_label.setText(f"Ошибка загрузки листа: {str(e)}")

    def update_charts(self, df: pd.DataFrame):
        """Обновляет диаграммы."""
        if not hasattr(self, 'figure'):
            return
        
        # Очистка холста
        self.figure.clear()
        
        # Подготовка данных
        risk_counts = df["Risk Level"].value_counts()
        questions = [f"Вопрос {i}" for i in range(1, 11)]
        avg_scores = [df[f"Вопрос {i}"].mean() for i in range(1, 11)]
        
        # Создание подграфиков
        ax1 = self.figure.add_subplot(121)  # Распределение риска
        ax2 = self.figure.add_subplot(122)  # Средние баллы
        
        # Диаграмма 1: Распределение риска
        ax1.bar(risk_counts.index, risk_counts.values, color=["green", "orange", "red"])
        ax1.set_title("Распределение по уровню риска")
        ax1.set_ylabel("Количество студентов")
        
        # Диаграмма 2: Средние баллы
        ax2.plot(questions, avg_scores, marker="o", color="blue")
        ax2.set_title("Средние баллы по вопросам")
        ax2.set_ylabel("Средний балл")
        ax2.set_ylim(0, 5)
        ax2.tick_params(axis='x', rotation=45)
        
        # Обновление холста
        self.canvas.draw()

    def update_filters_from_data(self, df: pd.DataFrame):
        """Обновляет bar'ы с Направлениями, Курсами и Группами."""
        # Очистка старых кнопок
        for layout in [self.direction_layout, self.course_layout, self.group_layout]:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        directions = set()
        courses = set()
        groups = set()
        
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
        
        # Создание кнопок
        self._create_toggles(self.direction_layout, directions, self.on_direction_toggle, "direction")
        self._create_toggles(self.course_layout, courses, self.on_course_toggle, "course")
        self._create_toggles(self.group_layout, groups, self.on_group_toggle, "group")
        
    def _create_toggles(self, layout, items, callback, name=""):
        """Создаёт кнопки или комбобокс в зависимости от количества элементов."""
        # Очистка layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        items = sorted(items)
        
        if len(items) <= 5:
            # Кнопки
            for item in items:
                btn = QPushButton(str(item))
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked, val=item: callback(val, checked))
                layout.addWidget(btn)
        else:
            # Выпадающий список с мультивыбором
            combo = QComboBox()
            combo.setEditable(False)
            combo.addItem("Выберите...")
            for item in items:
                combo.addItem(str(item))
            combo.currentTextChanged.connect(lambda text: self._handle_combo_select(text, callback, items))
            layout.addWidget(combo)
            setattr(self, f"_{name}_combo", combo)
            setattr(self, f"_{name}_selected", set())
        
        layout.addStretch()

    def _handle_combo_select(self, text, callback, all_items):
        """Обрабатывает выбор из комбобокса."""
        if text == "Выберите..." or not text:
            return
        
        # Снимаем выделение со всех
        for item in all_items:
            callback(item, False)
        
        # Выделяем выбранный
        callback(text, True)

    def on_direction_toggle(self, direction: str, checked: bool):
        """Обрабатывает переключение направления."""
        if checked:
            self.current_directions.add(direction)
        else:
            self.current_directions.discard(direction)
        self.apply_filters()

    def on_course_toggle(self, course: int, checked: bool):
        """Обрабатывает переключение курса."""
        if checked:
            self.current_courses.add(course)
        else:
            self.current_courses.discard(course)
        self.apply_filters()

    def on_group_toggle(self, group: str, checked: bool):
        """Обрабатывает переключение группы."""
        if checked:
            self.current_groups.add(group)
        else:
            self.current_groups.discard(group)
        self.apply_filters()
        
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
            risk_map = {"Низкий": "Низкий риск", "Средний": "Средний риск", "Высокий": "Высокий риск"}
            df = df[df['Risk Level'] == risk_map.get(risk_level, risk_level)]
        
        df = df.reset_index(drop=True)
        self.view_table.load_dataframe(df)

    def show_view(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_charts(self):
        self.stacked_widget.setCurrentIndex(2)
        if hasattr(self, '_full_data'):
            self.update_charts(self._full_data)