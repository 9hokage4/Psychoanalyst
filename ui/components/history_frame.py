# ui/components/history_frame.py
import customtkinter as ctk


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, app=None, **kwargs):
        # * Вызываем родительский конструктор первым — обязательно до создания дочерних виджетов
        super().__init__(master, **kwargs)
        
        # * Сохраняем ссылку на главное приложение для доступа к shared state
        self.app = app

        label = ctk.CTkLabel(self, text="История обработок", font=("Arial", 18, "bold"))
        label.pack(pady=20)
        
        # ! Здесь будет список ранее обработанных файлов с поиском и удалением
        placeholder = ctk.CTkLabel(self, text="История — в разработке")
        placeholder.pack()