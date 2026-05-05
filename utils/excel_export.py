# -*- coding: utf-8 -*-
# utils/excel_export.py
"""
Утилиты для экспорта и открытия Excel файлов.
"""
import os
import subprocess
import tempfile
import pandas as pd


def open_excel_file(file_path: str) -> bool:
    """
    Открывает Excel файл в приложении по умолчанию.
    
    Args:
        file_path: Путь к Excel файлу
        
    Returns:
        bool: True если успешно открыт
    """
    try:
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # macOS/Linux
            subprocess.call(['open', file_path])
        return True
    except Exception as e:
        print(f"Ошибка открытия файла: {e}")
        return False


def export_to_simple_excel(df: pd.DataFrame, output_path: str) -> bool:
    """
    Экспортирует DataFrame в простой Excel файл.
    
    Args:
        df: DataFrame с данными
        output_path: Путь для сохранения
        
    Returns:
        bool: True если успешно сохранён
    """
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Результаты')
        return True
    except Exception as e:
        print(f"Ошибка экспорта: {e}")
        return False


def export_and_open(df: pd.DataFrame) -> str:
    """
    Экспортирует DataFrame и открывает в Excel.
    
    Args:
        df: DataFrame с данными
        
    Returns:
        str: Путь к временному файлу или пустая строка при ошибке
    """
    try:
        # Создаём временный файл
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.xlsx',
            delete=False,
            mode='w+b'
        )
        temp_path = temp_file.name
        temp_file.close()
        
        # Экспортируем данные
        if export_to_simple_excel(df, temp_path):
            # Открываем в Excel
            if open_excel_file(temp_path):
                return temp_path
        
        # Если не удалось, удаляем файл
        os.unlink(temp_path)
        return ""
        
    except Exception as e:
        print(f"Ошибка экспорта и открытия: {e}")
        return ""


class ExcelExporter:
    """
    Класс для расширенного экспорта в Excel.
    """
    
    def __init__(self):
        self.wb = None
        self.temp_files = []
    
    def create_simple_preview(self, df: pd.DataFrame) -> str:
        """
        Создаёт простой Excel файл для предпросмотра.
        
        Args:
            df: DataFrame с данными
            
        Returns:
            str: Путь к файлу
        """
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.xlsx',
            delete=False,
            mode='w+b'
        )
        temp_path = temp_file.name
        temp_file.close()
        
        with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Результаты')
        
        self.temp_files.append(temp_path)
        return temp_path
    
    def open_file(self, file_path: str) -> bool:
        """Открывает файл в Excel"""
        return open_excel_file(file_path)
    
    def export_and_open(self, df: pd.DataFrame) -> bool:
        """Экспортирует и открывает в Excel"""
        temp_path = self.create_simple_preview(df)
        if temp_path:
            return self.open_file(temp_path)
        return False
    
    def cleanup(self):
        """Удаляет временные файлы"""
        for temp_path in self.temp_files:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
        self.temp_files = []
