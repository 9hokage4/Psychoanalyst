# ui/components/chart_frame.py
import customtkinter as ctk


class ChartFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        label = ctk.CTkLabel(self, text="Графики", font=("Arial", 18, "bold"))
        label.pack(pady=20)
        # ! Здесь будет генерация графиков и экспорт в Excel
        placeholder = ctk.CTkLabel(self, text="Генерация графиков — в разработке")
        placeholder.pack()