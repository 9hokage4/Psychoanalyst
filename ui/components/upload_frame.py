# ui/components/upload_frame.py
import customtkinter as ctk
from tkinter import filedialog
import pandas as pd
from ui.components.excel_table import ExcelTable


class UploadFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.df = None
        self.file_path = None

        # * Кнопка загрузки — крупная, закруглённая, выделенная
        self.load_btn = ctk.CTkButton(
            self,
            text="📂 Загрузить Excel",
            command=self._load_excel_file,
            font=("Arial", 16, "bold"),
            corner_radius=14,
            height=50,
            width=220
        )
        self.load_btn.pack(pady=(20, 10))

        # ! Дополнительные опции (например, шаблон) — пока скрыты в комментарии
        # self.options_menu = ctk.CTkOptionMenu(...)

        # * Таблица для предпросмотра
        self.table = ExcelTable(self)
        self.table.pack(fill="both", expand=True, padx=20, pady=(10, 20))

    def _load_excel_file(self):
        path = filedialog.askopenfilename(
            title="Выберите Excel-файл с результатами",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            self.file_path = path
            self.df = pd.read_excel(path)
            self.table.display_data(self.df)
            # * Можно добавить уведомление об успехе
        except Exception as e:
            # ! Здесь позже добавим обработку ошибок через CTkMessagebox
            print(f"Ошибка загрузки: {e}")