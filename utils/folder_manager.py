# -*- coding: utf-8 -*-
# utils/folder_manager.py
"""
Управление папками для сохранения результатов тестов.

Логика:
1. Первая обработка: файлы в `Базовая папка/Название теста/`
2. Вторая обработка: 
   - Старые файлы → `Базовая папка/Название теста/Тестирование ДАТА_СТАРОЙ/`
   - Новые файлы → `Базовая папка/Название теста/Тестирование ДАТА_НОВОЙ/`
3. Третья и далее:
   - Новые файлы → `Базовая папка/Название теста/Тестирование ДАТА_НОВОЙ/`
   - Старые папки "Тестирование" не трогаем

При переименовании теста:
- Старая папка остаётся как есть (НЕ переименовывается)
- Создаётся новая папка с новым названием
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import QSettings


class FolderManager:
    """Управление папками для сохранения результатов"""
    
    def __init__(self):
        self.settings = QSettings("Psychoanalyst", "Settings")
        
    def get_base_folder(self) -> str:
        """Получает базовую директорию"""
        return self.settings.value("output_base_folder", "", type=str)
    
    def set_base_folder(self, path: str):
        """Устанавливает базовую директорию"""
        self.settings.setValue("output_base_folder", path)
    
    def get_test_name(self) -> str:
        """Получает название теста"""
        return self.settings.value("current_test_name", "", type=str)
    
    def set_test_name(self, name: str):
        """Устанавливает название теста"""
        self.settings.setValue("current_test_name", name)
    
    
    def get_expected_test_folder(self) -> str:
        """
        Возвращает ожидаемый путь сохранения (для отображения в UI),
        не создавая папок и не перемещая файлы.
        """
        base_folder = self.get_base_folder()
        test_name = self.get_test_name()
        
        if not base_folder or not test_name:
            return ""
        
        base_path = Path(base_folder)
        test_folder = base_path if base_path.name == test_name else base_path / test_name
        
        # Если папка теста существует и в ней уже есть подпапки «Тестирование» или файлы,
        # то следующий экспорт создаст новую датированную подпапку.
        if test_folder.exists():
            subfolders = [f for f in test_folder.iterdir() if f.is_dir() and f.name.startswith("Тестирование")]
            files = [f for f in test_folder.iterdir() if f.is_file()]
            if subfolders or files:
                date_str = datetime.now().strftime("%d-%m-%Y")
                new_subfolder = test_folder / f"Тестирование {date_str}"
                return str(new_subfolder)
        
        return str(test_folder)
    
    def get_test_folder(self) -> str:
        base_folder = self.get_base_folder()
        test_name = self.get_test_name()
        
        if not base_folder or not test_name:
            return ""
        
        base_path = Path(base_folder)
        
        # Если выбранная папка уже называется как тест, используем её как папку теста
        if base_path.name == test_name:
            test_folder = base_path
        else:
            test_folder = base_path / test_name

        # Если папка не существует - создаём
        if not test_folder.exists():
            test_folder.mkdir(parents=True, exist_ok=True)
            return str(test_folder)
        
        # Проверяем есть ли вложенные папки "Тестирование"
        subfolders = [f for f in test_folder.iterdir() if f.is_dir() and f.name.startswith("Тестирование")]
        files = [f for f in test_folder.iterdir() if f.is_file()]
        
        if subfolders or files:
            # Уже есть папки или файлы - это повторная обработка
            if files:
                old_date_str = datetime.fromtimestamp(
                    min(f.stat().st_mtime for f in files)
                ).strftime("%d-%m-%Y")
                old_subfolder_name = f"Тестирование {old_date_str}"
                old_subfolder = test_folder / old_subfolder_name
                old_subfolder.mkdir(parents=True, exist_ok=True)
                
                for item in files:
                    shutil.move(str(item), str(old_subfolder / item.name))
            
            # Создаём папку для новых файлов
            date_str = datetime.now().strftime("%d-%m-%Y")
            new_subfolder_name = f"Тестирование {date_str}"
            new_subfolder = test_folder / new_subfolder_name
            new_subfolder.mkdir(parents=True, exist_ok=True)
            
            return str(new_subfolder)
        
        return str(test_folder)
    
    def ensure_folder_exists(self, test_name: str, base_folder: str) -> str:
        if not base_folder or not test_name:
            return ""
        base_path = Path(base_folder)
        self.set_test_name(test_name)

        # Если выбранная папка уже называется как тест, не создаём вложенную
        if base_path.name == test_name:
            test_folder = base_path
        else:
            test_folder = base_path / test_name

        test_folder.mkdir(parents=True, exist_ok=True)
        return str(test_folder)
    
    def save_file(self, source_path: str, filename: str) -> str:
        """
        Сохраняет файл в папку теста.
        """
        test_folder = self.get_test_folder()
        if not test_folder:
            return ""
        
        dest_path = Path(test_folder) / filename
        shutil.copy2(source_path, dest_path)
        
        return str(dest_path)
    
    def create_folder_structure(self, test_name: str, base_folder: str) -> dict:
        """
        Создаёт структуру папок для теста.
        """
        if not base_folder or not test_name:
            return {}
        
        base_path = Path(base_folder)
        test_folder = base_path / test_name
        test_folder.mkdir(parents=True, exist_ok=True)
        
        self.set_test_name(test_name)
        self.set_base_folder(str(base_folder))
        
        return {
            "test_folder": str(test_folder),
            "base_folder": str(base_folder),
            "test_name": test_name
        }
