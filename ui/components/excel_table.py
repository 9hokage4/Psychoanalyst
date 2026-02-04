# ui/components/excel_table.py
import customtkinter as ctk
import pandas as pd
from tkinter import Canvas, Scrollbar


class ExcelTable(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # * 1. Имя файла
        self.file_label = ctk.CTkLabel(
            self,
            text="Файл: не выбран",
            font=("Arial", 12, "bold"),
            anchor="w",
            fg_color="#f8f9fa",
            corner_radius=6,
            padx=12,
            pady=6
        )
        self.file_label.pack(fill="x", padx=10, pady=(10, 5))

        # * 2. Фиксированное окно таблицы: 800x500 px
        self.table_frame = ctk.CTkFrame(self, width=800, height=500, fg_color="transparent")
        self.table_frame.pack(padx=10, pady=(0, 10))
        self.table_frame.pack_propagate(False)  # ← КЛЮЧЕВОЕ: запрещает изменение размера

        # * Canvas внутри фиксированного фрейма
        self.canvas = Canvas(
            self.table_frame,
            bg="#ffffff",
            highlightthickness=0,
            width=800,
            height=500
        )
        self.canvas.pack(fill="both", expand=True)

        # * Скроллбары
        self.h_scrollbar = ctk.CTkScrollbar(
            self, orientation="horizontal", command=self.canvas.xview
        )
        self.h_scrollbar.pack(side="bottom", fill="x")
        self.v_scrollbar = ctk.CTkScrollbar(
            self, orientation="vertical", command=self.canvas.yview
        )
        self.v_scrollbar.pack(side="right", fill="y")

        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)

        # * Внутренний фрейм для таблицы
        self.inner = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_window = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")

        # * Масштаб
        self.scale = 1.0
        self.current_df = None

        # * Привязка масштаба
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel)

    def _on_ctrl_mousewheel(self, event):
        if event.delta > 0:
            self.scale = min(self.scale * 1.1, 2.0)
        else:
            self.scale = max(self.scale / 1.1, 0.5)
        if self.current_df is not None:
            self.display_data(self.current_df)
        print(f"# * Масштаб: {self.scale:.1f}x")

    def set_file_name(self, name: str):
        self.file_label.configure(text=f"Файл: {name}")

    def display_data(self, df: pd.DataFrame):
        self.current_df = df
        for w in self.inner.winfo_children():
            w.destroy()

        if df.empty:
            self.set_file_name("пустой файл")
            return

        # * Параметры с масштабом
        base_row_height = 34
        base_col_width = 80
        font_size = max(8, int(11 * self.scale))
        row_height = int(base_row_height * self.scale)
        col_width = int(base_col_width * self.scale)

        # * Заголовок
        header_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="nsew")
        for j, col in enumerate(df.columns):
            cell = ctk.CTkFrame(
                header_frame,
                fg_color="#e9ecef",
                border_width=1,
                border_color="#dee2e6",
                corner_radius=6,
                width=col_width,
                height=row_height
            )
            cell.grid(row=0, column=j, sticky="nsew", padx=(0, 1), pady=1)
            cell.pack_propagate(False)
            label = ctk.CTkLabel(
                cell,
                text=str(col),
                font=("Arial", max(10, int(12 * self.scale)), "bold"),
                anchor="w",
                padx=6,
                pady=4
            )
            label.pack(fill="both", expand=True)

        # * Данные
        for i, (_, row) in enumerate(df.iterrows()):
            bg_color = "#ffffff" if i % 2 == 0 else "#f8f9fa"
            row_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
            row_frame.grid(row=i+1, column=0, sticky="nsew")
            for j, val in enumerate(row):
                text = str(val) if not pd.isna(val) else ""
                cell = ctk.CTkFrame(
                    row_frame,
                    fg_color=bg_color,
                    border_width=1,
                    border_color="#dee2e6",
                    corner_radius=4,
                    width=col_width,
                    height=row_height
                )
                cell.grid(row=0, column=j, sticky="nsew", padx=(0, 1), pady=1)
                cell.pack_propagate(False)
                label = ctk.CTkLabel(
                    cell,
                    text=text,
                    font=("Arial", font_size),
                    anchor="w",
                    padx=6,
                    pady=4
                )
                label.pack(fill="both", expand=True)

        # * Установка scrollregion
        total_width = len(df.columns) * col_width + 10
        total_height = (len(df) + 1) * row_height + 10
        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))

        self.set_file_name("загружен.xlsx")