import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QSlider,
)
from PyQt6.QtCore import Qt

from live_reader import LiveReader
from ibt_parser import ReferenceLap
from overlay import OverlayWindow, MODE_BARS, MODE_TRACE, MODE_FULL


class ControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.live = LiveReader()
        self.reference = None
        self.overlay = None

        self.setWindowTitle("iRacing Telemetry Overlay")
        self.setFixedSize(380, 240)
        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # Reference file
        ref_row = QHBoxLayout()
        self.ref_label = QLabel("No reference loaded")
        self.ref_label.setWordWrap(True)
        ref_btn = QPushButton("Load reference .ibt…")
        ref_btn.clicked.connect(self._load_reference)
        ref_row.addWidget(self.ref_label, 1)
        ref_row.addWidget(ref_btn)
        layout.addLayout(ref_row)

        # Display mode
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Display mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Scrolling trace", "Bars", "Full lap"])
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        mode_row.addWidget(self.mode_combo)
        layout.addLayout(mode_row)

        # Opacity
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Overlay opacity:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(85)
        self.opacity_slider.valueChanged.connect(self._opacity_changed)
        opacity_row.addWidget(self.opacity_slider)
        layout.addLayout(opacity_row)

        # Show/hide overlay
        btn_row = QHBoxLayout()
        self.toggle_btn = QPushButton("Show Overlay")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(self._toggle_overlay)
        btn_row.addWidget(self.toggle_btn)
        layout.addLayout(btn_row)

        # Status
        self.status_label = QLabel("Load a reference lap, then show the overlay.")
        self.status_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _load_reference(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select reference lap", "", "iRacing telemetry (*.ibt)"
        )
        if not path:
            return
        try:
            self.reference = ReferenceLap(path)
            name = path.split("/")[-1].split("\\")[-1]
            self.ref_label.setText(f"Ref: {name}")
            self.status_label.setText("Reference loaded. Click 'Show Overlay' to start.")
            if self.overlay:
                self.overlay.set_reference(self.reference)
        except Exception as e:
            self.ref_label.setText("Failed to load file")
            self.status_label.setText(str(e))

    def _mode_changed(self, idx: int):
        modes = [MODE_TRACE, MODE_BARS, MODE_FULL]
        if self.overlay:
            self.overlay.set_mode(modes[idx])

    def _opacity_changed(self, value: int):
        if self.overlay:
            self.overlay.setWindowOpacity(value / 100)

    def _toggle_overlay(self, checked: bool):
        if checked:
            self.overlay = OverlayWindow(self.live, self.reference)
            modes = [MODE_TRACE, MODE_BARS, MODE_FULL]
            self.overlay.set_mode(modes[self.mode_combo.currentIndex()])
            self.overlay.setWindowOpacity(self.opacity_slider.value() / 100)
            self.overlay.show()
            self.toggle_btn.setText("Hide Overlay")
        else:
            if self.overlay:
                self.overlay.close()
                self.overlay = None
            self.toggle_btn.setText("Show Overlay")

    def closeEvent(self, event):
        if self.overlay:
            self.overlay.close()
        self.live.disconnect()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ControlPanel()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
