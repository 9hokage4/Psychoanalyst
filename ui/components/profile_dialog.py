# ui/components/profile_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
    QWidget, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from utils.message_box import MessageHelper
from utils.profile_manager import ProfileManager
from utils.fonts import get_font, FontWeights


class ProfileDialog(QDialog):
    profile_loaded = pyqtSignal(dict)
    profile_saved_with_name = pyqtSignal(str)  # имя профиля

    def __init__(self, parent=None, current_config=None):
        super().__init__(parent)
        self.setWindowTitle(" Профили настроек")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        self.profile_manager = ProfileManager()
        self.current_config = current_config

        self.init_ui()
        self.load_profiles_list()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Заголовок
        title = QLabel("Управление профилями")
        title.setFont(get_font("section_title"))
        title.setObjectName("title_label")
        main_layout.addWidget(title)

        info_label = QLabel("Сохраняйте и загружайте настройки тестов для быстрого доступа")
        info_label.setFont(get_font("caption"))
        info_label.setObjectName("info_label")
        main_layout.addWidget(info_label)

        # Список профилей
        self.profiles_list = QListWidget()
        self.profiles_list.setFont(get_font("body"))
        self.profiles_list.itemDoubleClicked.connect(self.on_load_profile)
        main_layout.addWidget(self.profiles_list)

        # Поле ввода имени нового профиля
        input_layout = QHBoxLayout()
        name_label = QLabel("Имя нового профиля:")
        name_label.setFont(get_font("form_label"))
        input_layout.addWidget(name_label)
        self.profile_name_input = QLineEdit()
        self.profile_name_input.setPlaceholderText(" Личностный опросник Айзенка")
        self.profile_name_input.setFont(get_font("form_input"))
        input_layout.addWidget(self.profile_name_input)
        main_layout.addLayout(input_layout)

        # Кнопки действий
        btn_layout = QGridLayout()
        btn_layout.setSpacing(10)

        # Общий стиль для всех кнопок
        btn_stylesheet = """
            QPushButton {
                background-color: #3390EC;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #2B80D9;
            }
            QPushButton:pressed {
                background-color: #1E6BC5;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """

        # Сохранить
        self.save_btn = QPushButton(" Сохранить")
        self.save_btn.setObjectName("btn_save_profile")
        self.save_btn.setIcon(QIcon("resources/icons/save.svg"))
        self.save_btn.setFont(get_font("button"))
        self.save_btn.setStyleSheet(btn_stylesheet)
        self.save_btn.clicked.connect(self.on_save_profile)
        btn_layout.addWidget(self.save_btn, 0, 0)

        # Загрузить
        self.load_btn = QPushButton(" Загрузить")
        self.load_btn.setObjectName("btn_load_profile")
        self.load_btn.setIcon(QIcon("resources/icons/folder.svg"))
        self.load_btn.setFont(get_font("button"))
        self.load_btn.setStyleSheet(btn_stylesheet)
        self.load_btn.clicked.connect(self.on_load_profile)
        btn_layout.addWidget(self.load_btn, 0, 1)

        # Удалить
        self.delete_btn = QPushButton(" Удалить")
        self.delete_btn.setObjectName("btn_delete_profile")
        self.delete_btn.setIcon(QIcon("resources/icons/trash.svg"))
        self.delete_btn.setFont(get_font("button"))
        self.delete_btn.setStyleSheet(btn_stylesheet)
        self.delete_btn.clicked.connect(self.on_delete_profile)
        btn_layout.addWidget(self.delete_btn, 1, 0)

        # Закрыть
        self.close_btn = QPushButton(" Закрыть")
        self.close_btn.setObjectName("btn_close")
        self.close_btn.setIcon(QIcon("resources/icons/close.svg"))
        self.close_btn.setFont(get_font("button"))
        self.close_btn.setStyleSheet(btn_stylesheet)
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn, 1, 1)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    
    def load_profiles_list(self):
        self.profiles_list.clear()
        profiles = self.profile_manager.list_profiles()
        
        for profile_name in profiles:
            item = QListWidgetItem(f" {profile_name}")
            item.setData(Qt.ItemDataRole.UserRole, profile_name)
            self.profiles_list.addItem(item)
        
        if profiles:
            self.profiles_list.setCurrentRow(0)
    
    def on_save_profile(self):
        profile_name = self.profile_name_input.text().strip()

        if not profile_name:
            MessageHelper.show_error(self,"Ошибка", "Введите имя профиля")
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
            MessageHelper.show_error(self,"Ошибка", "Нет текущей конфигурации для сохранения")
            return

        success = self.profile_manager.save_profile(profile_name, self.current_config)

        if success:
            MessageHelper.show_success(self, "Успех", f"Профиль '{profile_name}' сохранён!")
            self.profile_name_input.clear()
            self.load_profiles_list()
            # Отправляем сигнал с именем сохраненного профиля
            self.profile_saved_with_name.emit(profile_name)
        else:
            MessageHelper.show_error(self,"Ошибка", "Не удалось сохранить профиль")

    def on_load_profile(self):
        current_item = self.profiles_list.currentItem()

        if not current_item:
            MessageHelper.show_error(self,"Ошибка", "Выберите профиль для загрузки")
            return

        profile_name = current_item.data(Qt.ItemDataRole.UserRole)
        config = self.profile_manager.load_profile(profile_name)

        if config:
            self.profile_loaded.emit(config)
            self.accept()
        else:
            MessageHelper.show_error(self,"Ошибка", f"Не удалось загрузить профиль '{profile_name}'")

    def on_delete_profile(self):
        current_item = self.profiles_list.currentItem()

        if not current_item:
            MessageHelper.show_error(self,"Ошибка", "Выберите профиль для удаления")
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
                MessageHelper.show_success(self, "Успех", f"Профиль '{profile_name}' удалён!")
                self.load_profiles_list()
            else:
                MessageHelper.show_error(self,"Ошибка", "Не удалось удалить профиль")