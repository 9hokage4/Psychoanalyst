# ui/components/upload_frame.py
import customtkinter as ctk
from tkinter import filedialog
import pandas as pd
from ui.components.excel_table import ExcelTable


class UploadFrame(ctk.CTkFrame):
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.table = ExcelTable(self)
        self.table.pack(fill="both", expand=True, padx=10, pady=(10, 10))

        self.load_btn = ctk.CTkButton(
            self,
            text="📂 Загрузить Excel",
            command=self._load_excel_file,
            font=("Arial", 16, "bold"),
            corner_radius=14,
            height=50
        )
        self.load_btn.pack(pady=(20, 10))

    def _load_excel_file(self):
        path = filedialog.askopenfilename(
            title="Выберите Excel-файл",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not path:
            return

        try:
            df = pd.read_excel(path)
            self.app.current_raw_data = df
            self.app.table_cache[path] = (df, None)

            file_name = path.split("\\")[-1].split("/")[-1]
            self.table.set_file_name(file_name)
            self.table.display_data(df)

            print(f"# * Загружено: {len(df)} строк из {file_name}")

        except Exception as e:
            print(f"# ! Ошибка: {e}")