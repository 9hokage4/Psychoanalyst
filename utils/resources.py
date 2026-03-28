# utils/resources.py
"""
Модуль для получения абсолютных путей к ресурсам.
Решает проблему с относительными путями при смене рабочей директории.
"""
from pathlib import Path


# Базовый путь - корень проекта (где находится main.py)
BASE_DIR = Path(__file__).parent.parent


def get_resource_path(*args):
    """
    Получить абсолютный путь к ресурсу.
    
    Args:
        *args: Части пути относительно папки resources
        
    Returns:
        Path: Абсолютный путь к файлу ресурса
    """
    return BASE_DIR / "resources" / str(Path(*args))


def get_icon_path(icon_name):
    """
    Получить путь к иконке.
    
    Args:
        icon_name: Имя файла иконки (например, "upload.svg")
        
    Returns:
        str: Абсолютный путь к иконке
    """
    return str(get_resource_path("icons", icon_name))


def get_font_path(font_name):
    """
    Получить путь к шрифту.
    
    Args:
        font_name: Имя файла шрифта (например, "Vollkorn.ttf")
        
    Returns:
        str: Абсолютный путь к шрифту
    """
    return str(get_resource_path("fonts", font_name))
