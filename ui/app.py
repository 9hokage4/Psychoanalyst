# ui/app.py
import customtkinter as ctk
from ui.components.upload_frame import UploadFrame
from ui.components.analyze_frame import AnalyzeFrame
from ui.components.chart_frame import ChartFrame
from ui.components.history_frame import HistoryFrame


class PsychoTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # * Полноэкранный режим при запуске
        self.title("Анализатор психологических тестов")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        
        # * Разрешаем растягивание контента
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # * Создаём TabView
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # * Добавляем вкладки
        self.tabview.add("Загрузка")
        self.tabview.add("Анализ")
        self.tabview.add("Графики")
        self.tabview.add("История")

        # * Настройка сетки внутри каждой вкладки
        for tab_name in ["Загрузка", "Анализ", "Графики", "История"]:
            self.tabview.tab(tab_name).grid_rowconfigure(0, weight=1)
            self.tabview.tab(tab_name).grid_columnconfigure(0, weight=1)

        # * Создаём фреймы и привязываем к вкладкам
        self.upload_frame = UploadFrame(self.tabview.tab("Загрузка"))
        self.upload_frame.grid(row=0, column=0, sticky="nsew")

        self.analyze_frame = AnalyzeFrame(self.tabview.tab("Анализ"))
        self.analyze_frame.grid(row=0, column=0, sticky="nsew")

        self.chart_frame = ChartFrame(self.tabview.tab("Графики"))
        self.chart_frame.grid(row=0, column=0, sticky="nsew")

        self.history_frame = HistoryFrame(self.tabview.tab("История"))
        self.history_frame.grid(row=0, column=0, sticky="nsew")

        # * Активируем первую вкладку
        self.tabview.set("Загрузка")