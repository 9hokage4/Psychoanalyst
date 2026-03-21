# utils/fonts.py
"""
Модуль управления шрифтами приложения.
Все шрифты семейства PizzaHutCYR из resources/fonts.
"""
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import QDir
from pathlib import Path


class FontWeights:
    """Константы весов шрифтов PizzaHutCYR Antiqua."""
    THIN = 100
    LIGHT = 300
    REGULAR = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700
    BLACK = 900


# Маппинг контекстов к весам шрифтов
FONT_CONTEXTS = {
    # Заголовки окон и крупные заголовки
    "window_title": {"weight": FontWeights.BOLD, "size": 20, "italic": False},
    
    # Заголовки разделов (вкладки, группы)
    "section_title": {"weight": FontWeights.BOLD, "size": 16, "italic": False},
    "section_title_small": {"weight": FontWeights.SEMIBOLD, "size": 14, "italic": False},
    
    # Заголовки элементов (шкалы, уровни)
    "item_title": {"weight": FontWeights.BOLD, "size": 20, "italic": False},
    "badge_text": {"weight": FontWeights.MEDIUM, "size": 13, "italic": False},
    
    # Основной текст
    "body": {"weight": FontWeights.REGULAR, "size": 14, "italic": False},
    "body_small": {"weight": FontWeights.REGULAR, "size": 12, "italic": False},
    
    # Подписи, hint-текст
    "caption": {"weight": FontWeights.REGULAR, "size": 13, "italic": False},
    "hint": {"weight": FontWeights.LIGHT, "size": 12, "italic": False},
    
    # Кнопки
    "button": {"weight": FontWeights.MEDIUM, "size": 14, "italic": False},
    "button_small": {"weight": FontWeights.MEDIUM, "size": 13, "italic": False},
    
    # Навигация
    "nav_button": {"weight": FontWeights.MEDIUM, "size": 14, "italic": False},
    
    # Таблицы и данные
    "table_header": {"weight": FontWeights.SEMIBOLD, "size": 14, "italic": False},
    "table_cell": {"weight": FontWeights.REGULAR, "size": 14, "italic": False},
    
    # Формы (label, input)
    "form_label": {"weight": FontWeights.MEDIUM, "size": 13, "italic": False},
    "form_input": {"weight": FontWeights.REGULAR, "size": 14, "italic": False},
    
    # Цифровые данные (спинбоксы, значения)
    "numeric": {"weight": FontWeights.REGULAR, "size": 14, "italic": False},
}


def get_font(context: str, size: int = None, weight: int = None, italic: bool = None) -> QFont:
    """
    Получить шрифт по контексту с возможностью переопределения параметров.
    
    Args:
        context: Контекст использования (из FONT_CONTEXTS)
        size: Переопределение размера (опционально)
        weight: Переопределение веса (опционально)
        italic: Переопределение курсива (опционально)
    
    Returns:
        QFont: Настроенный объект шрифта
    """
    if context not in FONT_CONTEXTS:
        context = "body"
    
    config = FONT_CONTEXTS[context].copy()
    
    if size is not None:
        config["size"] = size
    if weight is not None:
        config["weight"] = weight
    if italic is not None:
        config["italic"] = italic

    font = QFont("PizzaHutCYR")
    font.setPointSize(config["size"])
    font.setWeight(_weight_to_qt_weight(config["weight"]))
    font.setItalic(config["italic"])

    return font


def _weight_to_qt_weight(weight: int) -> QFont.Weight:
    """Конвертация числового веса в QFont.Weight."""
    if weight <= FontWeights.THIN:
        return QFont.Weight.Thin
    elif weight <= FontWeights.LIGHT:
        return QFont.Weight.Light
    elif weight <= FontWeights.REGULAR:
        return QFont.Weight.Normal
    elif weight <= FontWeights.MEDIUM:
        return QFont.Weight.Medium
    elif weight <= FontWeights.SEMIBOLD:
        return QFont.Weight.DemiBold
    elif weight <= FontWeights.BOLD:
        return QFont.Weight.Bold
    else:
        return QFont.Weight.Black


def load_fonts() -> bool:
    """
    Загрузить все шрифты из resources/fonts.
    
    Returns:
        bool: True если загрузка успешна
    """
    fonts_dir = Path("resources/fonts")
    if not fonts_dir.exists():
        print(f"❌ Папка со шрифтами не найдена: {fonts_dir}")
        return False
    
    success = True
    for font_file in fonts_dir.glob("*.ttf"):
        font_id = QFontDatabase.addApplicationFont(str(font_file.absolute()))
        if font_id == -1:
            print(f"❌ Не удалось загрузить шрифт: {font_file.name}")
            success = False
        else:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                print(f"✅ Загружен шрифт: {font_file.name} ({families[0]})")
    
    return success


def get_font_family() -> str:
    """Получить название семейства шрифтов."""
    return "PizzaHutCYR"


def apply_font_to_widget(widget, context: str):
    """
    Применить шрифт к виджету.
    
    Args:
        widget: QWidget для применения шрифта
        context: Контекст использования шрифта
    """
    font = get_font(context)
    widget.setFont(font)
