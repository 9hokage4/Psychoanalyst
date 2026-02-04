# ui/components/analyze_frame.py
import customtkinter as ctk
from tkinter import filedialog
import pandas as pd
from core.processor import process_data
from ui.components.excel_table import ExcelTable


class AnalyzeFrame(ctk.CTkFrame):
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app

        # * Кнопка обработки
        self.process_btn = ctk.CTkButton(
            self,
            text="⚙️ Обработать данные",
            command=self._run_processing,
            font=("Arial", 16, "bold"),
            corner_radius=12,
            height=45
        )
        self.process_btn.pack(pady=(20, 10))

        # * Таблица результата
        self.result_table = ExcelTable(self)
        self.result_table.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        # * Кнопка экспорта (изначально неактивна)
        self.export_btn = ctk.CTkButton(
            self,
            text="📤 Сохранить результат в Excel",
            state="disabled",
            command=self._export_result
        )
        self.export_btn.pack(pady=10)

    def _run_processing(self):
        if self.app.current_raw_data is None:
            print("# ! Нет загруженных данных")
            return

        try:
            processed_df = process_data(self.app.current_raw_data)
            self.app.current_processed_data = processed_df
            self.result_table.display_data(processed_df)
            self.export_btn.configure(state="normal")  # * Активируем кнопку
            print("# * Обработка завершена")
        except Exception as e:
            print(f"# ! Ошибка обработки: {e}")

    def _export_result(self):
        if self.app.current_processed_data is None:
            return

        # * Открываем диалог сохранения
        file_path = filedialog.asksaveasfilename(
            title="Сохранить результат",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if not file_path:
            return

        try:
            # * Сохраняем DataFrame в Excel
            self.app.current_processed_data.to_excel(file_path, index=False)
            print(f"# * Результат сохранён: {file_path}")
            # ! Здесь позже можно добавить уведомление через CTkMessagebox
        except Exception as e:
            print(f"# ! Ошибка сохранения: {e}")