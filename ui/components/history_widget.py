# ui/components/history_widget.py
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFrame, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from utils.history_manager import HistoryManager
from utils.fonts import get_font, FontWeights
import pandas as pd


class HistoryWidget(QWidget):
    load_to_current_requested = pyqtSignal(dict, dict)

    def __init__(self):
        super().__init__()
        self.history_manager = HistoryManager()
        self.current_record_id = None
        self.setup_ui()
        self.load_history_list()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Левая панель
        left_panel = QFrame()
        left_panel.setObjectName("history_left_panel")
        left_panel.setStyleSheet("""
            QFrame#history_left_panel {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #DFE1E5;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        title = QLabel("📋 История обработок")
        title.setFont(get_font("section_title_small"))
        title.setStyleSheet("background-color: transparent; color: #000000;")
        left_layout.addWidget(title)

        self.records_list = QListWidget()
        self.records_list.setFont(get_font("body"))
        self.records_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                background-color: #FAFAFA;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #EEEEEE;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                color: #000000;
            }
            QListWidget::item:hover {
                background-color: #F5F5F5;
            }
        """)
        self.records_list.itemSelectionChanged.connect(self.on_record_selected)
        left_layout.addWidget(self.records_list)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setIcon(QIcon("resources/icons/trash.svg"))
        self.delete_btn.setFont(get_font("button_small"))
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #E53935;
                border: 1px solid #E53935;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)

        self.clear_all_btn = QPushButton("Очистить всё")
        self.clear_all_btn.setFont(get_font("button_small"))
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #757575;
                border: 1px solid #BDBDBD;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        self.clear_all_btn.clicked.connect(self.clear_all_history)
        btn_layout.addWidget(self.clear_all_btn)

        left_layout.addLayout(btn_layout)

        # Правая панель
        right_panel = QFrame()
        right_panel.setObjectName("history_right_panel")
        right_panel.setStyleSheet("""
            QFrame#history_right_panel {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #DFE1E5;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        self.info_label = QLabel("Выберите запись для просмотра")
        self.info_label.setFont(get_font("section_title_small"))
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("background-color: transparent; color: #000000;")
        right_layout.addWidget(self.info_label)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.results_container, 1)

        self.load_btn = QPushButton("📥 Загрузить в текущую сессию")
        self.load_btn.setFont(get_font("button"))
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
        """)
        self.load_btn.clicked.connect(self.load_to_current)
        self.load_btn.setEnabled(False)
        right_layout.addWidget(self.load_btn)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        splitter.setHandleWidth(1)
        main_layout.addWidget(splitter)

        self.results_view = None

    def load_history_list(self):
        self.records_list.clear()
        print("[DEBUG] Loading history list...")
        records = self.history_manager.get_all_records()
        print("[DEBUG] Records found:", len(records))
        for rec in records:
            test_name = rec.get("test_name", "Без названия")
            timestamp = rec.get("timestamp", "")
            try:
                dt = pd.to_datetime(timestamp)
                date_str = dt.strftime("%d.%m.%Y %H:%M")
            except:
                date_str = timestamp
            respondents = rec.get("respondents_count", 0)
            item_text = f"{test_name}\n{date_str}  |  {respondents} чел."
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, rec)
            self.records_list.addItem(item)
        if self.records_list.count() > 0:
            self.records_list.setCurrentRow(0)

    def on_record_selected(self):
        selected = self.records_list.currentItem()
        if not selected:
            self.delete_btn.setEnabled(False)
            self.load_btn.setEnabled(False)
            self.info_label.setText("Выберите запись для просмотра")
            self._clear_results_view()
            return

        self.delete_btn.setEnabled(True)
        record = selected.data(Qt.ItemDataRole.UserRole)
        self.current_record_id = record.get("id")

        test_name = record.get("test_name", "—")
        profile = record.get("profile_name", "—")
        filename = record.get("original_filename", "—")
        respondents = record.get("respondents_count", 0)
        groups = record.get("groups_count", 0)
        courses = record.get("courses_count", 0)

        info_text = (
            f"<b>{test_name}</b><br>"
            f"Файл: {filename}<br>"
            f"Профиль: {profile}<br>"
            f"Респондентов: {respondents} | Групп: {groups} | Курсов: {courses}"
        )
        self.info_label.setText(info_text)

        data = self.history_manager.get_record_data(self.current_record_id)
        if data:
            self._display_results(data["summary_data"], data["charts_data"])
            self.load_btn.setEnabled(True)
        else:
            self._clear_results_view()
            self.load_btn.setEnabled(False)
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить данные записи.")

    def _clear_results_view(self):
        if self.results_view:
            self.results_layout.removeWidget(self.results_view)
            self.results_view.deleteLater()
            self.results_view = None

    def _display_results(self, summary_data: dict, charts_data: dict):
        print(f"[DEBUG] _display_results: summary_data keys = {summary_data.keys()}")
        print(f"[DEBUG] _display_results: charts_data keys = {charts_data.keys()}")
        self._clear_results_view()
        from ui.components.results_widget import ResultsWidget
        self.results_view = ResultsWidget()
        empty_df = pd.DataFrame()
        self.results_view.set_data(empty_df, charts_data, summary_data)
        self.results_view.open_excel_btn.setVisible(False)
        self.results_view.download_chart_btn.setVisible(False)
        if hasattr(self.results_view, 'export_excel_btn'):
            self.results_view.export_excel_btn.setVisible(False)
        self.results_layout.addWidget(self.results_view)
        # === ДОБАВИТЬ ЭТУ СТРОКУ ===
        self.results_view._switch_view(self.results_view.views_stack.currentIndex())

    def delete_selected(self):
        if not self.current_record_id:
            return
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить выбранную запись? Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        success = self.history_manager.delete_record(self.current_record_id)
        if success:
            self.load_history_list()
            self._clear_results_view()
            self.info_label.setText("Выберите запись для просмотра")
            self.load_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось удалить запись.")

    def clear_all_history(self):
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить ВСЕ записи истории? Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        success = self.history_manager.clear_all()
        if success:
            self.load_history_list()
            self._clear_results_view()
            self.info_label.setText("Выберите запись для просмотра")
            self.load_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось очистить историю.")

    def load_to_current(self):
        if not self.current_record_id:
            return
        data = self.history_manager.get_record_data(self.current_record_id)
        if data:
            self.load_to_current_requested.emit(data["summary_data"], data["charts_data"])
            QMessageBox.information(self, "Успех", "Данные загружены в текущую сессию.\nПерейдите на вкладку «Результаты».")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные.")