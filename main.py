import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Psychological Test Analyzer")
        self.resize(800, 600)

        # * Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # * Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # * Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # * Вкладки
        self.process_tab = QWidget()
        self.analyze_tab = QWidget()

        self.tabs.addTab(self.process_tab, "Process")
        self.tabs.addTab(self.analyze_tab, "Analyze")

        # * Заполним заглушками
        process_layout = QVBoxLayout()
        process_layout.addWidget(QLabel("Process Tab: Select file and run analysis"))
        self.process_tab.setLayout(process_layout)

        analyze_layout = QVBoxLayout()
        analyze_layout.addWidget(QLabel("Analyze Tab: View and filter results"))
        self.analyze_tab.setLayout(analyze_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())