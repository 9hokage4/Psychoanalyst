# -*- coding: utf-8 -*-
# utils/worker.py
"""
Модуль для фоновой обработки данных.
Использует QThread для неблокирующей обработки больших Excel-файлов.
"""
from PyQt6.QtCore import QThread, pyqtSignal
import pandas as pd
import sys
import os

# Добавляем корневую директорию в путь для импорта processor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.processor import process_data


class ProcessWorker(QThread):
    """
    Воркер для фоновой обработки данных.
    
    Сигналы:
        started - начало обработки
        finished - обработка завершена (успех или ошибка)
        progress - прогресс обработки (текущий шаг, всего шагов)
        error - произошла ошибка
    """
    started = pyqtSignal()
    finished = pyqtSignal(object, bool, str)  # результат, успех, сообщение
    progress = pyqtSignal(int, int)  # текущий шаг, всего шагов
    error = pyqtSignal(str)  # сообщение об ошибке

    def __init__(self, df: pd.DataFrame, config: dict, parent=None):
        super().__init__(parent)
        self.df = df
        self.config = config
        self.setObjectName("ProcessWorker")

    def run(self):
        """Выполняет обработку данных в фоновом потоке."""
        try:
            self.started.emit()
            self.progress.emit(1, 4)  # Начало обработки

            # Проверка входных данных
            if self.df is None or self.df.empty:
                self.error.emit("DataFrame пуст или не загружен")
                self.finished.emit(None, False, "DataFrame пуст")
                return

            if not self.config:
                self.error.emit("Конфигурация не задана")
                self.finished.emit(None, False, "Конфигурация не задана")
                return

            self.progress.emit(2, 4)  # Проверка завершена

            # Извлекаем параметры из конфигурации
            scales_config = self.config.get("scales", {})
            level_order = self.config.get("level_order", [])
            level_ru = self.config.get("levels", {})
            answer_weights = self.config.get("answer_weights", {})

            # Проверка наличия всех необходимых данных
            if not scales_config:
                error_msg = "Не заданы шкалы в конфигурации"
                self.error.emit(error_msg)
                self.finished.emit(None, False, error_msg)
                return

            if not level_order:
                error_msg = "Не задан порядок уровней в конфигурации"
                self.error.emit(error_msg)
                self.finished.emit(None, False, error_msg)
                return

            if not answer_weights:
                error_msg = "Не заданы веса ответов в конфигурации"
                self.error.emit(error_msg)
                self.finished.emit(None, False, error_msg)
                return

            # Вызов процессора
            result_df = process_data(
                self.df,
                scales_config,
                level_order,
                level_ru,
                answer_weights
            )

            self.progress.emit(3, 4)  # Обработка завершена

            # Проверка результата
            if result_df is None or result_df.empty:
                self.error.emit("Процессор вернул пустой результат")
                self.finished.emit(None, False, "Пустой результат")
                return

            self.progress.emit(4, 4)  # Всё готово

            # Успешное завершение
            self.finished.emit(result_df, True, "Обработка завершена успешно")

        except KeyError as e:
            error_msg = f"Отсутствует необходимая колонка: {str(e)}"
            self.error.emit(error_msg)
            self.finished.emit(None, False, error_msg)

        except ValueError as e:
            error_msg = f"Ошибка в данных: {str(e)}"
            self.error.emit(error_msg)
            self.finished.emit(None, False, error_msg)

        except Exception as e:
            error_msg = f"Неизвестная ошибка: {str(e)}"
            self.error.emit(error_msg)
            self.finished.emit(None, False, error_msg)
