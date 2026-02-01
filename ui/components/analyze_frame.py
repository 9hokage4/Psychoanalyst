# ui/components/analyze_frame.py
import customtkinter as ctk


class AnalyzeFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        label = ctk.CTkLabel(self, text="Анализ данных", font=("Arial", 18, "bold"))
        label.pack(pady=20)
        # ! Здесь будет логика агрегации и обработки по алгоритму
        placeholder = ctk.CTkLabel(self, text="Функционал обработки будет добавлен позже")
        placeholder.pack()