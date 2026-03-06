# ui/components/profile_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
    QWidget, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.profile_manager import ProfileManager


class ProfileDialog(QDialog):
    profile_loaded = pyqtSignal(dict)  # Сигнал: профиль загружен

    def __init__(self, parent=None, current_config=None):
        super().__init__(parent)
        self.setWindowTitle("📁 Профили настроек")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        self.profile_manager = ProfileManager()
        self.current_config = current_config  # Текущая конфигурация для сохранения
        
        self.init_ui()
        self.load_profiles_list()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Заголовок
        title = QLabel("📁 Управление профилями")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        main_layout.addWidget(title)
        
        info_label = QLabel("Сохраняйте и загружайте настройки тестов для быстрого доступа")
        info_label.setStyleSheet("color: #666; font-size: 13px;")
        main_layout.addWidget(info_label)
        
        # Список профилей
        self.profiles_list = QListWidget()
        self.profiles_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #4a90d9;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
        """)
        self.profiles_list.itemDoubleClicked.connect(self.on_load_profile)
        main_layout.addWidget(self.profiles_list)
        
        # Поле ввода имени нового профиля
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Имя нового профиля:"))
        self.profile_name_input = QLineEdit()
        self.profile_name_input.setPlaceholderText("например, 'ММОП 2025'")
        self.profile_name_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #4a90d9;
            }
        """)
        input_layout.addWidget(self.profile_name_input)
        main_layout.addLayout(input_layout)
        
        # Кнопки действий
        btn_layout = QGridLayout()
        btn_layout.setSpacing(10)
        
        # Сохранить
        self.save_btn = QPushButton("💾 Сохранить текущие настройки")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.save_btn.clicked.connect(self.on_save_profile)
        btn_layout.addWidget(self.save_btn, 0, 0)
        
        # Загрузить
        self.load_btn = QPushButton("📂 Загрузить выбранный")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
        """)
        self.load_btn.clicked.connect(self.on_load_profile)
        btn_layout.addWidget(self.load_btn, 0, 1)
        
        # Удалить
        self.delete_btn = QPushButton("🗑️ Удалить выбранный")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete_profile)
        btn_layout.addWidget(self.delete_btn, 1, 0)
        
        # Закрыть
        self.close_btn = QPushButton("❌ Закрыть")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn, 1, 1)
        
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
    
    def load_profiles_list(self):
        """Загружает список профилей в QListWidget"""
        self.profiles_list.clear()
        profiles = self.profile_manager.list_profiles()
        
        for profile_name in profiles:
            item = QListWidgetItem(f"📄 {profile_name}")
            item.setData(Qt.ItemDataRole.UserRole, profile_name)
            self.profiles_list.addItem(item)
        
        if profiles:
            self.profiles_list.setCurrentRow(0)
    
    def on_save_profile(self):
        """Сохраняет текущую конфигурацию как профиль"""
        profile_name = self.profile_name_input.text().strip()
        
        if not profile_name:
            QMessageBox.warning(self, "Ошибка", "Введите имя профиля")
            return
        
        if self.profile_manager.profile_exists(profile_name):
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Профиль '{profile_name}' уже существует.\nПерезаписать?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        if self.current_config is None:
            QMessageBox.warning(self, "Ошибка", "Нет текущей конфигурации для сохранения")
            return
        
        success = self.profile_manager.save_profile(profile_name, self.current_config)
        
        if success:
            QMessageBox.information(self, "Успех", f"Профиль '{profile_name}' сохранён!")
            self.profile_name_input.clear()
            self.load_profiles_list()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить профиль")
    
    def on_load_profile(self):
        """Загружает выбранный профиль"""
        current_item = self.profiles_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль для загрузки")
            return
        
        profile_name = current_item.data(Qt.ItemDataRole.UserRole)
        config = self.profile_manager.load_profile(profile_name)
        
        if config:
            self.profile_loaded.emit(config)
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить профиль '{profile_name}'")
    
    def on_delete_profile(self):
        """Удаляет выбранный профиль"""
        current_item = self.profiles_list.currentItem()
        
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль для удаления")
            return
        
        profile_name = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить профиль '{profile_name}'?\nЭто действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.profile_manager.delete_profile(profile_name)
            
            if success:
                QMessageBox.information(self, "Успех", f"Профиль '{profile_name}' удалён!")
                self.load_profiles_list()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить профиль")