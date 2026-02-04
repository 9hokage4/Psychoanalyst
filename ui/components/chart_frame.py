# ui/components/chart_frame.py
import customtkinter as ctk


class ChartFrame(ctk.CTkFrame):
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, **kwargs)
    
        self.app = app

        label = ctk.CTkLabel(self, text="Графики", font=("Arial", 18, "bold"))
        label.pack(pady=20)

        placeholder = ctk.CTkLabel(self, text="Генерация графиков — в разработке")
        placeholder.pack()