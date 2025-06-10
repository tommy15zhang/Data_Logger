from PyQt5 import QtWidgets, QtCore

class MetricCard(QtWidgets.QFrame):
    def __init__(self, title: str, accent: str, unit: str = ""):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setLineWidth(0)
        self.setStyleSheet(
            "QFrame {background:#232834; border-radius:6px; border:1px solid #3a4252;}"
        )

        self._unit = unit
        self.title_lbl = QtWidgets.QLabel(title)
        self.title_lbl.setStyleSheet("color:#ddd; font-size:14px;")

        self.value_bg = QtWidgets.QLabel()
        self.value_bg.setAlignment(QtCore.Qt.AlignCenter)
        self.value_bg.setStyleSheet(
            f"background:{accent}; border-radius:6px; padding:8px 12px;"
            "color:#fff; font-weight:600; font-size:28px;"
        )
        self.value_bg.setMinimumHeight(70)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.addWidget(self.title_lbl)
        lay.addStretch(1)
        lay.addWidget(self.value_bg)

    def set_value(self, val):
        text = f"{val}{self._unit}" if self._unit else str(val)
        self.value_bg.setText(text)


class AdviceCard(QtWidgets.QFrame):
    def __init__(self, title="Watering Advice"):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setLineWidth(0)
        self.setStyleSheet(
            "QFrame {background:#232834; border-radius:6px; border:1px solid #3a4252;}"
        )
        hdr = QtWidgets.QLabel(title)
        hdr.setStyleSheet("color:#ddd; font-size:16px; font-weight:600;")

        self.body = QtWidgets.QLabel("–")
        self.body.setWordWrap(True)
        self.body.setAlignment(QtCore.Qt.AlignCenter)
        self.body.setStyleSheet("font-size:18px; color:#ddd;")

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.addWidget(hdr)
        lay.addStretch(1)
        lay.addWidget(self.body)

    def set_text(self, text: str):
        self.body.setText(text)


class StatusCard(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setLineWidth(0)
        self.setStyleSheet(
            "QFrame {background:#232834; border-radius:6px; border:1px solid #3a4252;}"
        )
        hdr = QtWidgets.QLabel("Watering Advice")
        hdr.setStyleSheet("color:#ddd; font-size:16px; font-weight:600;")

        self.icon = QtWidgets.QLabel("✓")
        self.icon.setAlignment(QtCore.Qt.AlignCenter)
        self.icon.setStyleSheet("font-size:48px; color:#4CAF50;")

        self.status_lbl = QtWidgets.QLabel("No Need")
        self.status_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.status_lbl.setStyleSheet("font-size:24px; font-weight:600; color:#ddd;")

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.addWidget(hdr)
        lay.addStretch(1)
        lay.addWidget(self.icon)
        lay.addWidget(self.status_lbl)

    def set_status(self, text: str, ok: bool = True):
        self.status_lbl.setText(text)
        self.icon.setText("✓" if ok else "✗")
        self.icon.setStyleSheet(
            f"font-size:48px; color:{'#4CAF50' if ok else '#F44336'};"
        )


class SerialMonitorWidget(QtWidgets.QGroupBox):
    """A widget for displaying and sending serial data."""
    def __init__(self, parent=None):
        super().__init__("Serial Monitor", parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.serial_text = QtWidgets.QTextEdit()
        self.serial_text.setReadOnly(True)
        self.serial_text.setFixedHeight(120)
        input_layout = QtWidgets.QHBoxLayout()
        self.serial_input = QtWidgets.QLineEdit()
        self.serial_input.setPlaceholderText("Type message to send to Arduino...")
        self.serial_send_btn = QtWidgets.QPushButton("Send")
        input_layout.addWidget(self.serial_input)
        input_layout.addWidget(self.serial_send_btn)
        layout.addWidget(self.serial_text)
        layout.addLayout(input_layout)
        self.setLayout(layout)

    def append_rx(self, msg):
        self.serial_text.append(f"[RX] {msg}")

    def append_tx(self, msg):
        self.serial_text.append(f"[TX] {msg}")

    def append_info(self, msg):
        self.serial_text.append(f"[INFO] {msg}")

    def append_error(self, msg):
        self.serial_text.append(f"[ERROR] {msg}")

    def clear(self):
        self.serial_text.clear()


class MoistureCard(MetricCard):
    def __init__(self):
        super().__init__("Soil Moisture", "#8BC34A", "")
        # You can adjust the accent color and unit as needed