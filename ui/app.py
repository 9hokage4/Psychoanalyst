# ui/app.py
import customtkinter as ctk
from ui.components.upload_frame import UploadFrame
from ui.components.analyze_frame import AnalyzeFrame
from ui.components.chart_frame import ChartFrame
from ui.components.history_frame import HistoryFrame


class PsychoTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Анализатор тестов")
        self.state('zoomed')

        # * Shared state
        self.current_raw_data = None
        self.current_processed_data = None
        self.table_cache = {}  # кэш: file_path -> (raw_df, processed_df)

        # * TabView
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        for name in ["Загрузка", "Анализ", "Графики", "История"]:
            self.tabview.add(name)
            self.tabview.tab(name).grid_rowconfigure(0, weight=1)
            self.tabview.tab(name).grid_columnconfigure(0, weight=1)

        self.upload_frame = UploadFrame(self.tabview.tab("Загрузка"), app=self)
        self.upload_frame.grid(row=0, column=0, sticky="nsew")

        self.analyze_frame = AnalyzeFrame(self.tabview.tab("Анализ"), app=self)
        self.analyze_frame.grid(row=0, column=0, sticky="nsew")

        self.chart_frame = ChartFrame(self.tabview.tab("Графики"), app=self)
        self.chart_frame.grid(row=0, column=0, sticky="nsew")

        self.history_frame = HistoryFrame(self.tabview.tab("История"), app=self)
        self.history_frame.grid(row=0, column=0, sticky="nsew")

        self.tabview.set("Загрузка")