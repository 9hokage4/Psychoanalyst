# utils/resources.py
import sys
import os
from pathlib import Path

def get_resource_path(relative_path):
    """Абсолютный путь к ресурсу (работает и в EXE, и при обычном запуске)."""
    if getattr(sys, 'frozen', False):
        # Запущено как EXE – временная папка PyInstaller
        base_path = Path(sys._MEIPASS)
    else:
        # Обычный запуск – корень проекта
        base_path = Path(__file__).parent.parent
    return base_path / relative_path

def get_icon_path(icon_name):
    """Возвращает абсолютный путь к иконке."""
    return str(get_resource_path(f"resources/icons/{icon_name}"))

def get_icon_url(icon_name):
    """Возвращает путь к иконке для использования в QSS: url('...')."""
    return f'url("{get_icon_path(icon_name)}")'

def get_font_path(font_name):
    """Возвращает абсолютный путь к шрифту."""
    return str(get_resource_path(f"resources/fonts/{font_name}"))