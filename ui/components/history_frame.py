# ui/components/history_frame.py
import customtkinter as ctk


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        label = ctk.CTkLabel(self, text="История обработок", font=("Arial", 18, "bold"))
        label.pack(pady=20)
        # ! Здесь будет список ранее обработанных файлов с поиском и удалением
        placeholder = ctk.CTkLabel(self, text="История — в разработке")
        placeholder.pack()