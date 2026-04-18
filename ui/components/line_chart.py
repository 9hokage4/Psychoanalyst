# ui/components/line_chart.py
# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class LineChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.top_layout = QHBoxLayout()
        self.scale_label = QLabel("Шкала:")
        self.scale_combo = QComboBox()
        self.scale_combo.setMinimumWidth(150)
        self.scale_combo.currentTextChanged.connect(self._on_selection_changed)
        self.scale_label.setVisible(False)
        self.scale_combo.setVisible(False)
        self.top_layout.addWidget(self.scale_label)
        self.top_layout.addWidget(self.scale_combo)

        self.group_label = QLabel("Группа/Курс:")
        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(150)
        self.group_combo.currentTextChanged.connect(self._on_selection_changed)
        self.group_label.setVisible(False)
        self.group_combo.setVisible(False)
        self.top_layout.addWidget(self.group_label)
        self.top_layout.addWidget(self.group_combo)
        self.top_layout.addStretch()
        layout.addLayout(self.top_layout)

        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

        self.empty_label = QLabel("Выберите параметры для отображения")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #707579; font-size: 15px; padding: 50px;")
        layout.addWidget(self.empty_label)

        self.setLayout(layout)
        self.summary_data = {}
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

        self._block_signals = True
        self.scale_combo.clear()
        self.scale_combo.addItem("По всем шкалам")
        for scale_name in scales_config.keys():
            self.scale_combo.addItem(scale_name)
        self._block_signals = False

        if scope_type == "Результат по всем респондентам":
            self.scale_label.setVisible(False)
            self.scale_combo.setVisible(False)
            self.group_label.setVisible(False)
            self.group_combo.setVisible(False)
            self._plot_all_scales()
        elif scope_type == "Результат по группам":
            self.group_label.setVisible(True)
            self.group_combo.setVisible(True)
            self.scale_label.setVisible(True)
            self.scale_combo.setVisible(True)
            self._update_group_combo("group_summary")
        elif scope_type == "Результат по курсам":
            self.group_label.setVisible(True)
            self.group_combo.setVisible(True)
            self.scale_label.setVisible(True)
            self.scale_combo.setVisible(True)
            self._update_group_combo("course_summary")

        if self.scope_type == "Результат по всем респондентам":
            self._plot_all_scales()
        elif self.scale_combo.count() > 0 and self.group_combo.count() > 0:
            self._on_selection_changed()
        elif self.scale_combo.count() > 0:
            self._on_selection_changed()

    def _on_selection_changed(self):
        if self._block_signals:
            return

        scale_name = self.scale_combo.currentText()
        group_name = self.group_combo.currentText()

        if scale_name == "По всем шкалам":
            self._plot_all_scales_for_group()
        else:
            self._plot_by_group(scale_name)

    def _update_group_combo(self, summary_key):
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        summary = self.summary_data.get(summary_key, {})
        if summary:
            self.group_combo.addItems(list(summary.keys()))
        self.group_combo.blockSignals(False)

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

    def _plot_all_scales_for_group(self):
        """Линии по всем шкалам для выбранной группы/курса"""
        group_name = self.group_combo.currentText()
        parsed = self._get_parsed_data(group_name)

        if not parsed:
            self._show_no_data()
            return

        scales = list(self.scales_config.keys())
        levels_data = {level_key: [] for level_key in self.level_order}

        for scale_name in scales:
            scale_data = parsed.get(scale_name, {})
            for level_key in self.level_order:
                percent = scale_data.get(level_key, {}).get("percent", 0)
                levels_data[level_key].append(percent)

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if not scales:
            ax.text(0.5, 0.5, "Нет данных", ha='center', va='center')
            self.canvas.draw()
            return

        x = range(len(scales))
        colors = ["#66BB6A", "#FFA726", "#42A5F5", "#EF5350"][:len(self.level_order)]

        for i, level_key in enumerate(self.level_order):
            ax.plot(x, levels_data[level_key], marker='o', linestyle='-',
                    label=self.level_ru.get(level_key, level_key), color=colors[i % len(colors)])

        ax.set_xlabel('Шкалы', fontsize=12)
        ax.set_ylabel('Процент (%)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(scales, rotation=45, ha='right')

        # Формируем читаемый контекст
        if self.scope_type == "Результат по группам":
            context = f"по группе {group_name}"
        elif self.scope_type == "Результат по курсам":
            context = f"по курсу {group_name}"
        else:
            context = "Все респонденты"

        ax.legend(title=f"Уровни {context}", loc='upper right')
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()

    def _plot_by_group(self, scale_name):
        group_name = self.group_combo.currentText()
        parsed = self._get_parsed_data(group_name)
        scale_data = parsed.get(scale_name, {})

        if not scale_data:
            self._show_no_data()
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        levels = []
        percents = []
        colors = ["#66BB6A", "#FFA726", "#42A5F5", "#EF5350"][:len(self.level_order)]

        for level_key in self.level_order:
            data = scale_data.get(level_key, {})
            percent = data.get("percent", 0)
            if percent > 0:
                levels.append(self.level_ru.get(level_key, level_key))
                percents.append(percent)

        if not levels:
            self._show_no_data()
            return

        x = range(len(levels))
        ax.plot(x, percents, marker='o', linestyle='-', color=colors[0])
        ax.set_xticks(x)
        ax.set_xticklabels(levels, rotation=45, ha='right')
        ax.set_xlabel('Уровни', fontsize=12)
        ax.set_ylabel('Процент (%)', fontsize=12)

        if self.scope_type == "Результат по группам":
            context = f"по группе {group_name}"
        elif self.scope_type == "Результат по курсам":
            context = f"по курсу {group_name}"
        else:
            context = "Все респонденты"

        ax.set_title(f"{scale_name}\n{context}", fontsize=12)
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()

    def _plot_all_scales(self):
        summary_key = "group_summary"
        summary = self.summary_data.get(summary_key, {})

        if not summary:
            self.empty_label.setVisible(True)
            self.canvas.setVisible(False)
            return

        first_key = list(summary.keys())[0]
        parsed = self._get_parsed_data(first_key)

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        scales = list(self.scales_config.keys())
        levels_data = {level_key: [] for level_key in self.level_order}

        for scale_name in scales:
            scale_data = parsed.get(scale_name, {})
            for level_key in self.level_order:
                percent = scale_data.get(level_key, {}).get("percent", 0)
                levels_data[level_key].append(percent)

        if not scales:
            ax.text(0.5, 0.5, "Нет данных", ha='center', va='center')
            self.canvas.draw()
            return

        x = range(len(scales))
        colors = ["#66BB6A", "#FFA726", "#42A5F5", "#EF5350"][:len(self.level_order)]

        for i, level_key in enumerate(self.level_order):
            ax.plot(x, levels_data[level_key], marker='o', linestyle='-',
                    label=self.level_ru.get(level_key, level_key), color=colors[i % len(colors)])

        ax.set_xlabel('Шкала', fontsize=12)
        ax.set_ylabel('Процент (%)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(scales, rotation=45, ha='right')
        ax.legend(title="Уровни по всем респондентам", loc='upper right')
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.empty_label.setVisible(False)
        self.canvas.setVisible(True)
        self.canvas.draw()

    def _show_no_data(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, "Нет данных", ha='center', va='center')
        self.canvas.draw()

    def save_to_png(self, file_path):
        if self.figure and len(self.figure.axes) > 0:
            self.figure.savefig(file_path, dpi=150, bbox_inches='tight')
            return True
        return False