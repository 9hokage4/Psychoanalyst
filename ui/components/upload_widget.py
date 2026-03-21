# ui/components/upload_widget.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                             QLabel, QPushButton, QFileDialog, QStackedWidget,
                             QGridLayout, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent, QIcon, QFont

import pandas as pd
from ui.components.table_widget import ExcelTable
from utils.fonts import get_font, FontWeights


class DragDropArea(QFrame):
    """Область для перетаскивания файлов (и клика)."""
    file_dropped = pyqtSignal(str)  # путь к файлу

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(250)  # Уменьшил высоту
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Стиль: пунктирная рамка, скруглённые углы, фоновый цвет
        self.setStyleSheet("""
            DragDropArea {
                border: 2px dashed #3390EC;
                border-radius: 12px;
                background-color: #F5F8FB;
            }
            DragDropArea:hover {
                background-color: #E3F2FD;
            }
        """)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Иконка (эмодзи как временная замена)
        icon_label = QLabel("📂")
        icon_label.setStyleSheet("font-size: 40px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Текст
        text_label = QLabel("Перетащите Excel файл сюда")
        text_label.setFont(get_font("section_title"))
        text_label.setStyleSheet("color: #000000;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        # Подсказка
        hint_label = QLabel("или нажмите, чтобы выбрать файл (.xlsx, .xls)")
        hint_label.setFont(get_font("hint"))
        hint_label.setStyleSheet("color: #707579;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        # Кнопка "Выбрать файл" (увеличенная)
        self.select_btn = QPushButton("Выбрать файл")
        self.select_btn.setFixedSize(200, 44)  # ширина 200, высота 44
        self.select_btn.setFont(get_font("button", size=16))
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
        """)
        self.select_btn.clicked.connect(self._on_select_clicked)
        layout.addWidget(self.select_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith(('.xlsx', '.xls')):
                self.file_dropped.emit(file_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_select_clicked()
        super().mousePressEvent(event)

    def _on_select_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите Excel-файл", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.file_dropped.emit(file_path)


class ConfigSummary(QFrame):
    """Блок «Текущая конфигурация» с разделителями."""
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ConfigSummary {
                background-color: #F8F9FA;
                border: 1px solid #DFE1E5;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Заголовок
        title = QLabel("⚙️ Текущая конфигурация")
        title.setFont(get_font("section_title_small"))
        title.setStyleSheet("color: #707579; text-transform: uppercase; letter-spacing: 0.5px;")
        layout.addWidget(title)

        # Строки конфигурации с разделителями
        self._add_config_row(layout, "Профиль настроек", "Default_v1.json")
        self._add_separator(layout)
        self._add_config_row(layout, "Количество вопросов", "45")
        self._add_separator(layout)
        self._add_config_row(layout, "Активные шкалы", "3 (Агрессивность, Цинизм, Эмпатия)")
        self._add_separator(layout)

        # Статус
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_label = QLabel("Статус:")
        status_label.setFont(get_font("caption"))
        status_label.setStyleSheet("color: #707579;")
        status_value = QLabel("✅ Готов к обработке")
        status_value.setFont(get_font("badge_text"))
        status_value.setStyleSheet("color: #2E7D32; background-color: #E8F5E9; "
                                   "padding: 4px 12px; border-radius: 12px; font-weight: 600;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(status_value)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Кнопка "Изменить настройки"
        settings_btn = QPushButton("⚙️ Изменить настройки")
        settings_btn.setFont(get_font("button_small"))
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #3390EC;
                border: 1px solid #3390EC;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #F4F4F5;
            }
        """)
        settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    def _add_config_row(self, layout, label_text, value_text):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        label = QLabel(label_text + ":")
        label.setFont(get_font("caption"))
        label.setStyleSheet("color: #707579;")
        value = QLabel(value_text)
        value.setFont(get_font("form_input"))
        value.setStyleSheet("color: #000000; font-weight: 500;")
        row.addWidget(label)
        row.addStretch()
        row.addWidget(value)
        layout.addLayout(row)

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #DFE1E5; max-height: 1px;")
        layout.addWidget(line)

    def update_config(self, profile_name, questions_count, scales_text, status_text, status_color):
        """Обновляет отображаемые значения. Пока заглушка."""
        pass


class UploadWidget(QWidget):
    """Виджет вкладки «Загрузка»."""
    file_loaded = pyqtSignal(object)  # передаёт DataFrame
    filename_updated = pyqtSignal(str)
    settings_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_df = None
        self.current_file_path = None
        self.sheet_names = []

        # Главная карточка
        self.card = QFrame(self)
        self.card.setObjectName("upload_card")
        self.card.setStyleSheet("""
            QFrame#upload_card {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
        """)

        # Тень для карточки
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(20)

        # --- Область загрузки / Таблица (Stacked) ---
        self.upload_stack = QStackedWidget()
        self.upload_stack.setFixedHeight(250)  # под размер области

        self.drag_drop_area = DragDropArea()
        self.drag_drop_area.file_dropped.connect(self.load_file_from_path)

        self.table_view = ExcelTable()
        self.table_view.setVisible(False)  # изначально скрыта

        self.upload_stack.addWidget(self.drag_drop_area)
        self.upload_stack.addWidget(self.table_view)
        self.upload_stack.setCurrentWidget(self.drag_drop_area)

        card_layout.addWidget(self.upload_stack)

        # Разделитель
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("background-color: #DFE1E5; max-height: 1px;")
        card_layout.addWidget(sep1)

        # Блок конфигурации
        self.config_summary = ConfigSummary()
        self.config_summary.settings_clicked.connect(self.settings_requested.emit)
        card_layout.addWidget(self.config_summary)

        # Разделитель
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: #DFE1E5; max-height: 1px;")
        card_layout.addWidget(sep2)

        # Горизонтальный ряд для кнопок (обработка + отмена)
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(10)
        button_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Кнопка обработки
        self.process_btn = QPushButton("🚀 ОБРАБОТАТЬ ДАННЫЕ")
        self.process_btn.setEnabled(False)
        self.process_btn.setFont(get_font("button", size=16, weight=FontWeights.SEMIBOLD))
        self.process_btn.setStyleSheet("""
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
        self.process_btn.clicked.connect(self.start_processing)

        # Кнопка отмены (красная)
        self.cancel_btn = QPushButton("✖ Отмена")
        self.cancel_btn.setVisible(False)  # скрыта, пока файл не выбран
        self.cancel_btn.setFont(get_font("button", size=16))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E07B7B;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 24px;
            }
            QPushButton:hover {
                background-color: #C96A6A;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_selection)

        button_row.addWidget(self.process_btn)
        button_row.addWidget(self.cancel_btn)

        card_layout.addLayout(button_row)

        # Основной layout виджета (просто добавляем карточку)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addStretch()
        main_layout.addWidget(self.card)
        main_layout.addStretch()
        self.card.setFixedWidth(1600)

    def load_file_from_path(self, file_path):
        """Загружает файл по пути, переключает на таблицу."""
        try:
            self.sheet_names = pd.ExcelFile(file_path).sheet_names
            self.current_file_path = file_path
            # Загружаем первый лист
            df = pd.read_excel(file_path, sheet_name=self.sheet_names[0])
            self.current_df = df
            self.table_view.set_data_frame(df)
            # Переключаем стек на таблицу
            self.upload_stack.setCurrentWidget(self.table_view)
            # Показываем кнопку отмены
            self.cancel_btn.setVisible(True)
            # Обновляем сигналы
            self.file_loaded.emit(df)
            file_name = file_path.split("/")[-1].split("\\")[-1]
            self.filename_updated.emit(file_name)
            # Активируем кнопку обработки (позже будет зависеть от конфигурации)
            self.process_btn.setEnabled(True)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")

    def cancel_selection(self):
        """Отменяет выбор файла, возвращает область загрузки."""
        self.current_df = None
        self.current_file_path = None
        self.sheet_names = []
        self.table_view.set_data_frame(None)  # очищаем таблицу
        self.upload_stack.setCurrentWidget(self.drag_drop_area)
        self.cancel_btn.setVisible(False)
        self.process_btn.setEnabled(False)
        # Можно также сбросить имя файла, если оно где-то отображается
        self.filename_updated.emit("")  # или None

    def start_processing(self):
        """Запускает обработку данных (пока заглушка)."""
        print("Обработка запущена...")
        # Здесь будет вызов ProcessWorker, а потом переключение на вкладку результатов
        # TODO: реализовать