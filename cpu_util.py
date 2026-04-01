import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                              QWidget, QScrollArea)
from PyQt6.QtCore import QTimer

from helpers import INTERVAL
from panels import CpuThroughputPanel

# =========================
# Dark theme stylesheet
# =========================
DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
}
QLabel {
    color: #e0e0e0;
}
QScrollArea {
    border: none;
}
"""


# =========================
# Main window
# =========================
class MainWindow(QMainWindow):
    """
    Top-level window that holds monitoring panels.
    To add a new panel, create a BasePanel subclass and call add_panel().
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Monitor")
        self.resize(1100, 700)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(6)

        # Scrollable panel area (useful once multiple panels are added)
        self.panel_container = QWidget()
        self.panel_layout = QVBoxLayout(self.panel_container)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidget(self.panel_container)
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        # Panel registry
        self.panels = []

        # --- Register panels here ---
        self.add_panel(CpuThroughputPanel())
        # Future: self.add_panel(TemperaturePanel())
        # Future: self.add_panel(FanSpeedPanel())

        # Update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_all)
        self.timer.start(INTERVAL)

    def add_panel(self, panel):
        self.panels.append(panel)
        self.panel_layout.addWidget(panel)

    def _update_all(self):
        for panel in self.panels:
            panel.update_data()


# =========================
# Entry point
# =========================
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
