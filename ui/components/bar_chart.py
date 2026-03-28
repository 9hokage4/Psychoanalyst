# ui/components/bar_chart.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd


class BarChartWidget(QWidget):
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

        self.figure = Figure(figsize=(10, 6))
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
        self._plot_bar(scale_name)

    def _plot_bar(self, scale_name: str):
        """Строит столбчатую диаграмму сравнения групп по выбранной шкале"""
        if self.charts_data is None or "by_group_scale" not in self.charts_data:
            return
        
        df = self.charts_data["by_group_scale"]
        if df.empty:
            return
        
        # Фильтруем по выбранной шкале
        scale_df = df[df["Название шкалы"] == scale_name]
        if scale_df.empty:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Группируем по областям (группам)
        groups = scale_df["Название области"].unique().tolist()
        levels = scale_df["Название уровня"].unique().tolist()
        
        # Порядок уровней из конфигурации
        level_order_ru = [self.level_ru.get(k, k) for k in self.level_order]
        levels = [l for l in level_order_ru if l in levels]
        
        if not groups or not levels:
            ax.text(0.5, 0.5, "Нет данных для отображения", ha='center', va='center', fontsize=14)
            self.canvas.draw()
            return
        
        # Параметры для столбцов
        bar_width = 0.2
        x = range(len(groups))
        
        # Цвета для уровней
        colors = ["#66BB6A", "#FFA726", "#42A5F5", "#EF5350"][:len(levels)]
        
        # Строим столбцы для каждого уровня
        for i, level in enumerate(levels):
            level_data = scale_df[scale_df["Название уровня"] == level]
            values = []
            for group in groups:
                group_data = level_data[level_data["Название области"] == group]
                if not group_data.empty:
                    values.append(group_data["Процент по уровню"].values[0])
                else:
                    values.append(0)
            
            offset = (i - len(levels) / 2 + 0.5) * bar_width
            ax.bar(
                [pos + offset for pos in x], 
                values, 
                bar_width, 
                label=level,
                color=colors[i % len(colors)],
                edgecolor='white',
                linewidth=1
            )
        
        # Настройка осей и легенды
        ax.set_xlabel('Группа', fontsize=12)
        ax.set_ylabel('Процент (%)', fontsize=12)
        ax.set_title(f'Сравнение групп по шкале "{scale_name}"', fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(groups, rotation=45, ha='right', fontsize=10)
        ax.legend(title='Уровни', loc='upper right', fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Увеличиваем отступы для размещения подписей
        self.figure.tight_layout()
        
        self.canvas.draw()
