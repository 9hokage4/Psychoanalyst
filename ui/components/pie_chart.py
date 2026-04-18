# ui/components/pie_chart.py
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd


class PieChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Верхний layout с QComboBox
        top_layout = QHBoxLayout()

        self.scale_label = QLabel("Шкала:")
        self.scale_combo = QComboBox()
        self.scale_combo.setMinimumWidth(150)
        self.scale_combo.currentTextChanged.connect(self._on_selection_changed)
        top_layout.addWidget(self.scale_label)
        top_layout.addWidget(self.scale_combo)

        self.group_label = QLabel("Группа/Курс:")
        self.group_label.setVisible(False)
        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(150)
        self.group_combo.currentTextChanged.connect(self._on_selection_changed)
        self.group_combo.setVisible(False)
        top_layout.addWidget(self.group_label)
        top_layout.addWidget(self.group_combo)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Заголовок
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 15px; padding: 5px;")
        self.title_label.setVisible(False)
        layout.addWidget(self.title_label)

        # График
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

        self.empty_label = QLabel("Выберите шкалу для отображения")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #707579; font-size: 15px; padding: 50px;")
        layout.addWidget(self.empty_label)

        self.setLayout(layout)
        self.summary_data = {}
        self.charts_data = {}
        self.level_order = []
        self.level_ru = {}
        self.scales_config = {}
        self.scope_type = "Все респонденты"
        self._block_signals = False

        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #DFE1E5;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 18px;
                background-color: white;
                color: #000000;
            }
            QComboBox:focus {
                border-color: #3390EC;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)

    def set_data(self, summary_data, charts_data, level_order, level_ru, scales_config, scope_type="Результат по всем респондентам"):
        self.summary_data = summary_data
        self.charts_data = charts_data
        self.level_order = level_order
        self.level_ru = level_ru
        self.scales_config = scales_config
        self.scope_type = scope_type

        # Заполняем шкалы
        self._block_signals = True
        self.scale_combo.clear()
        for scale_name in scales_config.keys():
            self.scale_combo.addItem(scale_name)
        self._block_signals = False

        # Группа/Курс
        if scope_type == "Результат по группам":
            self.group_label.setVisible(True)
            self.group_combo.setVisible(True)
            self._update_group_combo("group_summary")
        elif scope_type == "Результат по курсам":
            self.group_label.setVisible(True)
            self.group_combo.setVisible(True)
            self._update_group_combo("course_summary")
        else:  # "Результат по всем респондентам"
            self.group_label.setVisible(False)
            self.group_combo.setVisible(False)

        if self.scale_combo.count() > 0:
            self.empty_label.setVisible(False)
            self.canvas.setVisible(True)
            self._on_selection_changed()
        else:
            self.empty_label.setVisible(True)
            self.canvas.setVisible(False)
            self.title_label.setVisible(False)

    def _update_group_combo(self, summary_key):
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        summary = self.summary_data.get(summary_key, {})
        if summary:
            # Убираем "По всем" – это дублирует общий лист
            self.group_combo.addItems(list(summary.keys()))
        self.group_combo.blockSignals(False)

    def _on_selection_changed(self):
        if self._block_signals:
            return

        scale_name = self.scale_combo.currentText()
        group_name = self.group_combo.currentText() if self.group_combo.isVisible() else "Все"

        if not scale_name:
            return

        self.empty_label.setVisible(False)
        self.canvas.setVisible(True)

        if self.scope_type == "Результат по группам":
            self.title_label.setText(f"По группе: {group_name}")
            self.title_label.setVisible(True)
        elif self.scope_type == "Результат по курсам":
            self.title_label.setText(f"По курсу: {group_name}")
            self.title_label.setVisible(True)
        else:
            self.title_label.setVisible(False)

        self._plot_pie(scale_name, group_name)

    def _get_parsed_data(self, group_name):
        if self.scope_type == "Результат по группам":
            summary_key = "group_summary"
        elif self.scope_type == "Результат по курсам":
            summary_key = "course_summary"
        else:
            summary_key = "group_summary"

        summary = self.summary_data.get(summary_key, {})

        if not summary:
            if self.summary_data.get("group_summary"):
                summary = self.summary_data["group_summary"]
            elif self.summary_data.get("course_summary"):
                summary = self.summary_data["course_summary"]
            else:
                return self._get_from_charts_data()

        if group_name == "Все" or group_name == "По всем":
            first_key = list(summary.keys())[0] if summary else None
            if not first_key:
                return self._get_from_charts_data()
            group_info = summary.get(first_key, {})
        else:
            # Ищем ключ с учётом возможных пробелов
            found_key = None
            for key in summary.keys():
                if str(key).strip() == str(group_name).strip():
                    found_key = key
                    break
            group_info = summary.get(found_key, {}) if found_key else {}

        table_df = group_info.get("table", None)

        if table_df is None or table_df.empty:
            return self._get_from_charts_data()

        result = {}
        for _, row in table_df.iterrows():
            scale_name = str(row.get("Шкала", "")).strip()
            if not scale_name:
                continue

            result[scale_name] = {}
            for level_key in self.level_order:
                level_name = self.level_ru.get(level_key, level_key)
                value_str = str(row.get(level_name, "0 чел./0%"))

                count = 0
                percent = 0.0
                try:
                    parts = value_str.replace(" ", "").split("/")
                    if len(parts) == 2:
                        count = int(parts[0].replace("чел.", ""))
                        percent = float(parts[1].replace("%", ""))
                except:
                    pass

                result[scale_name][level_key] = {"count": count, "percent": percent}

        return result if result else self._get_from_charts_data()

    def _get_from_charts_data(self):
        """Резервный метод: берет данные напрямую из charts_data"""
        if not self.charts_data:
            return {}

        df = self.charts_data.get("by_scale_level", None)
        if df is None or df.empty:
            return {}

        result = {}
        for _, row in df.iterrows():
            scale = row["Название шкалы"]
            level_code = row["Код уровня"]
            count = row["Количество по уровню"]
            percent = row["Процент по уровню"]

            if scale not in result:
                result[scale] = {}
            result[scale][level_code] = {"count": count, "percent": percent}

        return result

    def _plot_pie(self, scale_name, group_name="Все"):
        parsed = self._get_parsed_data(group_name)
        scale_data = parsed.get(scale_name, {})

        if not scale_data:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Нет данных", ha='center', va='center')
            self.canvas.draw()
            return

        labels = []
        sizes = []
        percents = []
        counts = []
        colors_map = {"low": "#66BB6A", "mid_low": "#FFA726", "mid_high": "#42A5F5", "high": "#EF5350"}
        colors = []

        for level_key in self.level_order:
            data = scale_data.get(level_key, {})
            count = data.get("count", 0)
            percent = data.get("percent", 0)

            if count > 0:
                labels.append(self.level_ru.get(level_key, level_key))
                sizes.append(count)
                percents.append(percent)
                counts.append(count)
                colors.append(colors_map.get(level_key, "#999999"))

        if not sizes:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Нет данных", ha='center', va='center')
            self.canvas.draw()
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=None,
            colors=colors,
            startangle=90,
            autopct='%1.1f%%',
            pctdistance=0.85
        )

        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)

        # Формируем заголовок легенды с контекстом
        if self.scope_type == "Результат по группам":
            context_title = f"по группе {group_name}"
        elif self.scope_type == "Результат по курсам":
            context_title = f"по курсу {group_name}"
        else:
            context_title = "Все респонденты"

        legend_labels = [f"{lbl} ({p:.1f}% = {int(c)} чел.)" for lbl, p, c in zip(labels, percents, counts)]

        ax.legend(wedges, legend_labels,
                title=f"Уровни {context_title}",
                loc="center left",
                bbox_to_anchor=(1, 0.5),
                fontsize=10)

        self.figure.subplots_adjust(left=0.05, right=0.65)
        self.canvas.draw()

    def save_to_png(self, file_path):
        if self.figure and len(self.figure.axes) > 0:
            self.figure.savefig(file_path, dpi=150, bbox_inches='tight')
            return True
        return False