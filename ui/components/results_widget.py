# ui/components/results_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.fonts import get_font, FontWeights


class ResultsNavButton(QPushButton):
    """Кнопка вертикальной навигации"""
    
    def __init__(self, icon_path: str, text: str, parent=None):
        super().__init__(parent)
        self.setup_ui(icon_path, text)
        
    def setup_ui(self, icon_path: str, text: str):
        self.setObjectName("results_nav_button")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)
        
        # Иконка
        self.icon_label = QLabel()
        self.icon_label.setObjectName("nav_icon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Текст
        self.text_label = QLabel(text)
        self.text_label.setObjectName("nav_text")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setFont(get_font("nav_button"))

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)


class ResultsWidget(QWidget):
    sheet_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_sheet = "Все листы"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # ===== ВЕРТИКАЛЬНАЯ НАВИГАЦИЯ (ФИКСИРОВАННАЯ ВЫСОТА) =====
        self.sidebar = QWidget()
        self.sidebar.setObjectName("results_sidebar")
        self.sidebar.setFixedHeight(450)  # ✅ Фиксированная высота
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setSpacing(16)
        
        self.nav_buttons = []
        
        btn_table = ResultsNavButton("resources/icons/table.svg", "Таблица")
        btn_table.setChecked(True)
        btn_table.clicked.connect(lambda: self._switch_view(0))
        self.nav_buttons.append(btn_table)
        
        btn_pie = ResultsNavButton("resources/icons/pie.svg", "Круговая")
        btn_pie.clicked.connect(lambda: self._switch_view(1))
        self.nav_buttons.append(btn_pie)
        
        btn_bar = ResultsNavButton("resources/icons/bar.svg", "Столбчатая")
        btn_bar.clicked.connect(lambda: self._switch_view(2))
        self.nav_buttons.append(btn_bar)
        
        btn_line = ResultsNavButton("resources/icons/line.svg", "График")
        btn_line.clicked.connect(lambda: self._switch_view(3))
        self.nav_buttons.append(btn_line)
        
        for btn in self.nav_buttons:
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        layout.addWidget(self.sidebar)
        
        # ===== КОНТЕНТ (ФИКСИРОВАННАЯ ВЫСОТА) =====
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        
        # Выбор листа Excel
        self.sheet_selector_widget = self._create_sheet_selector()
        content_layout.addWidget(self.sheet_selector_widget)
        
        # Стек видов
        self.views_stack = QStackedWidget()
        self.views_stack.setObjectName("views_stack")
        
        # Таблица
        self.table_view = self._create_table_view()
        self.views_stack.addWidget(self.table_view)
        
        # Графики (заглушки)
        self.pie_view = self._create_chart_placeholder("🥧", "Круговая диаграмма", "Распределение уровней")
        self.views_stack.addWidget(self.pie_view)
        
        self.bar_view = self._create_chart_placeholder("📊", "Столбчатая диаграмма", "Сравнение показателей")
        self.views_stack.addWidget(self.bar_view)
        
        self.line_view = self._create_chart_placeholder("📈", "Линейный график", "Динамика показателей")
        self.views_stack.addWidget(self.line_view)
        
        content_layout.addWidget(self.views_stack)
        layout.addWidget(content_widget)
    
    def _create_sheet_selector(self) -> QWidget:
        """Создаёт выпадающий список выбора листа"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        sheet_label = QLabel("📊 Лист Excel:")
        sheet_label.setFont(get_font("form_label"))

        self.sheet_combo = QComboBox()
        self.sheet_combo.setObjectName("sheet_selector")
        self.sheet_combo.setFont(get_font("form_input"))
        self.sheet_combo.addItems(["Все листы", "По курсу", "Предварительный", "Итоговый"])
        self.sheet_combo.currentTextChanged.connect(self._on_sheet_changed)

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
        
        # Пример данных
        data = [
            ("#101", "Иванов А.А.", "15.03.2026", "Средний", "24/45", "warning"),
            ("#102", "Петрова Е.В.", "15.03.2026", "Низкий", "12/45", "success"),
            ("#103", "Сидоров К.К.", "14.03.2026", "Высокий", "38/45", "danger"),
        ]
        
        table.setRowCount(len(data))
        for row, row_data in enumerate(data):
            for col in range(4):  # Первые 4 колонки - обычный текст
                item = QTableWidgetItem(row_data[col])
                table.setItem(row, col, item)
            
            # Последняя колонка - бейдж с уровнем
            badge_widget = self._create_badge(row_data[3], row_data[5])
            table.setCellWidget(row, 3, badge_widget)
            
            # Баллы
            item = QTableWidgetItem(row_data[4])
            table.setItem(row, 4, item)
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        return table
    
    def _create_badge(self, text: str, level: str) -> QWidget:
        """Создаёт бейдж уровня (Низкий/Средний/Высокий)"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        
        label = QLabel(text)
        label.setWordWrap(False)
        
        if level == "success":
            label.setObjectName("badge_success")
        elif level == "warning":
            label.setObjectName("badge_warning")
        elif level == "danger":
            label.setObjectName("badge_danger")
        
        layout.addWidget(label)
        layout.addStretch()
        
        return widget
    
    def _create_chart_placeholder(self, icon: str, title: str, subtitle: str) -> QWidget:
        """Создаёт заглушку для графика"""
        widget = QWidget()
        widget.setObjectName("chart_placeholder")
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setFont(get_font("section_title"))
        title_label.setStyleSheet("color: #000000;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(get_font("caption"))
        subtitle_label.setStyleSheet("color: #707579;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        return widget
    
    def _switch_view(self, index: int):
        """Переключает вид (таблица/графики)"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.views_stack.setCurrentIndex(index)
    
    def set_data(self, df):
        """Устанавливает данные из pandas DataFrame"""
        if df is None or df.empty:
            return
        
        # Очистка таблицы
        self.table_view.setRowCount(0)
        
        # Заполнение из DataFrame
        for row_idx, row in df.iterrows():
            self.table_view.insertRow(row_idx)
            
            # ID
            item = QTableWidgetItem(str(row.get('ID', f'#{row_idx}')))
            self.table_view.setItem(row_idx, 0, item)
            
            # Респондент
            item = QTableWidgetItem(str(row.get('Респондент', 'Unknown')))
            self.table_view.setItem(row_idx, 1, item)
            
            # Дата
            item = QTableWidgetItem(str(row.get('Дата', '')))
            self.table_view.setItem(row_idx, 2, item)
            
            # Уровень (с бейджем)
            level = str(row.get('Уровень', 'Не определено'))
            level_type = self._get_level_type(level)
            badge_widget = self._create_badge(level, level_type)
            self.table_view.setCellWidget(row_idx, 3, badge_widget)
            
            # Баллы
            item = QTableWidgetItem(str(row.get('Баллы', '0/0')))
            self.table_view.setItem(row_idx, 4, item)
    
    def _get_level_type(self, level: str) -> str:
        """Определяет тип уровня для бейджа"""
        level_lower = level.lower()
        if 'низк' in level_lower:
            return 'success'
        elif 'средн' in level_lower:
            return 'warning'
        elif 'высок' in level_lower:
            return 'danger'
        return 'warning'  # По умолчанию
    
    def set_filename(self, filename: str):
        """Обновляет название файла (для отображения)"""
        # Можно добавить label с названием файла
        pass
    
    def get_current_sheet(self) -> str:
        """Возвращает текущий выбранный лист"""
        return self.current_sheet