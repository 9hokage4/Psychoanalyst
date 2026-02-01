# ui/components/excel_table.py
import customtkinter as ctk
import tkinter.ttk as ttk
import pandas as pd


class ExcelTable(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # * Создаём Treeview
        self.tree = ttk.Treeview(self, show="headings")
        self.tree.pack(fill="both", expand=True)

        # * Прокрутка
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

    def display_data(self, df: pd.DataFrame):
        # * Очистка предыдущих данных
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree["columns"] = list(df.columns)

        # * Настройка колонок
        for col in df.columns:
            self.tree.heading(col, text=str(col))
            self.tree.column(col, width=100, minwidth=80, stretch=True)

        # * Вставка строк
        for _, row in df.iterrows():
            self.tree.insert("", "end", values=list(row.astype(str)))