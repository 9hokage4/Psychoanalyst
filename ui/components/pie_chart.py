# ui/components/pie_chart.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd


class PieChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Выпадающий список для выбора шкалы
        self.scale_combo = QComboBox()
        self.scale_combo.setFixedHeight(40)
        self.scale_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                margin: 10px;
            }
            QComboBox:focus {
                border-color: #3390EC;
            }
        """)
        self.scale_combo.currentTextChanged.connect(self._on_scale_changed)
        layout.addWidget(self.scale_combo)

        # Label для пустого состояния
        self.empty_label = QLabel("Выберите шкалу для отображения")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #707579; font-size: 16px; padding: 50px;")
        layout.addWidget(self.empty_label)

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setVisible(False)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.charts_data = {}
        self.level_order = []
        self.level_ru = {}
        self.available_scales = []

    def set_data(self, charts_data: dict, level_order: list, level_ru: dict):
        """Устанавливает данные для графика"""
        self.charts_data = charts_data
        self.level_order = level_order
        self.level_ru = level_ru
        
        # Извлекаем доступные шкалы из данных
        if "by_scale_level" in charts_data and not charts_data["by_scale_level"].empty:
            self.available_scales = charts_data["by_scale_level"]["Название шкалы"].unique().tolist()
        else:
            self.available_scales = []
        
        # Обновляем выпадающий список
        self.scale_combo.clear()
        if self.available_scales:
            self.scale_combo.addItems(["Выберите шкалу"] + self.available_scales)
            self.scale_combo.setCurrentIndex(0)
        else:
            self.scale_combo.addItem("Нет данных")
            self.scale_combo.setEnabled(False)
        
        # Скрываем график, показываем empty label
        self.empty_label.setVisible(True)
        self.canvas.setVisible(False)

    def _on_scale_changed(self, scale_name: str):
        """Обработчик выбора шкалы"""
        if scale_name == "Выберите шкалу" or scale_name == "Нет данных":
            self.empty_label.setVisible(True)
            self.canvas.setVisible(False)
            return
        
        self.empty_label.setVisible(False)
        self.canvas.setVisible(True)
        self._plot_pie(scale_name)

    def _plot_pie(self, scale_name: str):
        """Строит круговую диаграмму распределения уровней для выбранной шкалы"""
        if self.charts_data is None or "by_scale_level" not in self.charts_data:
            return
        
        df = self.charts_data["by_scale_level"]
        if df.empty:
            return
        
        # Фильтруем по выбранной шкале
        scale_df = df[df["Название шкалы"] == scale_name]
        if scale_df.empty:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Данные для диаграммы
        labels = scale_df["Название уровня"].tolist()
        sizes = scale_df["Количество по уровню"].tolist()
        colors = ["#66BB6A", "#FFA726", "#42A5F5", "#EF5350"][:len(sizes)]
        
        # Фильтруем нулевые значения
        non_zero_indices = [i for i, s in enumerate(sizes) if s > 0]
        if not non_zero_indices:
            ax.text(0.5, 0.5, "Нет данных для отображения", ha='center', va='center', fontsize=14)
            self.canvas.draw()
            return
        
        labels = [labels[i] for i in non_zero_indices]
        sizes = [sizes[i] for i in non_zero_indices]
        colors = [colors[i % len(colors)] for i in non_zero_indices]
        
        # Круговая диаграмма
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            pctdistance=0.75,
            textprops={'fontsize': 11}
        )
        
        # Стилизация
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(f'Распределение уровней: {scale_name}', fontsize=14, fontweight='bold', pad=20)
        
        self.canvas.draw()
