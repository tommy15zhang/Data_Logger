from PyQt5 import QtCore, QtWidgets, QtGui
import serial
from serial.tools import list_ports
from collections import deque
import numpy as np
import pyqtgraph as pg
from widgets import MetricCard, SerialMonitorWidget, MoistureCard
import json
import os

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌿 Arduino Environment Monitor")
        self.resize(1100, 700)

        self.ser = None
        self.h_data = deque([0.0] * 50, maxlen=50)
        self.t_data = deque([0.0] * 50, maxlen=50)
        self.m_data = deque([0.0] * 50, maxlen=50)
        self.timer = QtCore.QTimer(self, interval=200)
        self.timer.timeout.connect(self._timer_tick)

        self._apply_dark_theme()

        self.port_combo, self.baud_combo = QtWidgets.QComboBox(), QtWidgets.QComboBox()
        self._populate_baud_rates()
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.refresh_ports()
        self.led = QtWidgets.QLabel()
        self.led.setFixedSize(16, 16)
        self._set_led("red")

        topbar = QtWidgets.QHBoxLayout()
        for w in (
            QtWidgets.QLabel("Port:"),
            self.port_combo,
            QtWidgets.QLabel("  Baud:"),
            self.baud_combo,
            self.refresh_btn,
            self.connect_btn,
        ):
            topbar.addWidget(w)
        topbar.addStretch(1)
        topbar.addWidget(self.led)

        self.temp_card = MetricCard("Temperature", "#FF9800", "°C")
        self.hum_card = MetricCard("Humidity", "#2196F3", "%")
        self.moisture_card = MoistureCard()
        self.aq_card = MetricCard("Air Quality", "#4CAF50")
        self.aq_card.set_value("–")

        metrics_col = QtWidgets.QVBoxLayout()
        metrics_col.setSpacing(16)
        metrics_col.addWidget(self.temp_card)
        metrics_col.addWidget(self.hum_card)
        metrics_col.addWidget(self.moisture_card)
        metrics_col.addWidget(self.aq_card)
        metrics_col.addStretch(1)

        metrics_container = QtWidgets.QWidget()
        metrics_container.setLayout(metrics_col)
        metrics_container.setFixedWidth(220)

        pg.setConfigOptions(antialias=True)
        self.env_plot = pg.PlotWidget(title="Environmental Conditions")
        self.env_plot.setLabel("bottom", "Samples (latest →)")
        self.env_plot.showGrid(x=True, y=True)
        self.env_plot.addLegend(offset=(10, 10))
        self.env_plot.enableAutoRange(axis="y", enable=True)

        self.h_curve = self.env_plot.plot(
            self.h_data, pen=pg.mkPen("#2196F3", width=2), name="Humidity"
        )
        self.t_curve = self.env_plot.plot(
            self.t_data, pen=pg.mkPen("#FF9800", width=2), name="Temperature"
        )

        # Two separate plots for humidity and temperature
        self.hum_plot = pg.PlotWidget(title="Humidity")
        self.hum_plot.setLabel("left", "Humidity (%)")
        self.hum_plot.setLabel("bottom", "Samples (latest →)")
        self.hum_plot.showGrid(x=True, y=True)
        self.hum_plot.enableAutoRange(axis="y", enable=True)
        self.hum_plot.getPlotItem().getViewBox().setBackgroundColor(None)
        self.hum_plot.getPlotItem().setTitle("Humidity", size="18pt", color="#4CAF50")
        self.hum_curve = self.hum_plot.plot(self.h_data, pen=pg.mkPen("#2196F3", width=2), name="Humidity")
        # Threshold lines for humidity
        self.hum_thresh_low = self.hum_plot.addLine(y=0, pen=pg.mkPen("#FFC107", width=2, style=QtCore.Qt.DashLine))
        self.hum_thresh_high = self.hum_plot.addLine(y=0, pen=pg.mkPen("#4CAF50", width=2, style=QtCore.Qt.DashLine))

        self.temp_plot = pg.PlotWidget(title="Temperature")
        self.temp_plot.setLabel("left", "Temperature (°C)")
        self.temp_plot.setLabel("bottom", "Samples (latest →)")
        self.temp_plot.showGrid(x=True, y=True)
        self.temp_plot.enableAutoRange(axis="y", enable=True)
        self.temp_plot.getPlotItem().getViewBox().setBackgroundColor(None)
        self.temp_plot.getPlotItem().setTitle("Temperature", size="18pt", color="#FF9800")
        self.temp_curve = self.temp_plot.plot(self.t_data, pen=pg.mkPen("#FF9800", width=2), name="Temperature")
        # Threshold lines for temperature
        self.temp_thresh_low = self.temp_plot.addLine(y=0, pen=pg.mkPen("#FFC107", width=2, style=QtCore.Qt.DashLine))
        self.temp_thresh_high = self.temp_plot.addLine(y=0, pen=pg.mkPen("#4CAF50", width=2, style=QtCore.Qt.DashLine))

        self.moisture_plot = pg.PlotWidget(title="Soil Moisture")
        self.moisture_plot.setLabel("left", "Moisture")
        self.moisture_plot.setLabel("bottom", "Samples (latest →)")
        self.moisture_plot.showGrid(x=True, y=True)
        self.moisture_plot.enableAutoRange(axis="y", enable=True)
        self.moisture_plot.getPlotItem().getViewBox().setBackgroundColor(None)
        self.moisture_plot.getPlotItem().setTitle("Soil Moisture", size="18pt", color="#8BC34A")
        self.moisture_curve = self.moisture_plot.plot(self.m_data, pen=pg.mkPen("#8BC34A", width=2), name="Moisture")
        self.moisture_thresh_low = self.moisture_plot.addLine(y=0, pen=pg.mkPen("#FFC107", width=2, style=QtCore.Qt.DashLine))
        self.moisture_thresh_high = self.moisture_plot.addLine(y=0, pen=pg.mkPen("#4CAF50", width=2, style=QtCore.Qt.DashLine))

        # Remove advice/status cards and plant table, add single plant widget
        # Remove advice_row, right_col, right_container, plant_table, and related widgets
        # Instead, add plant_widget and nav_layout to a new layout below main_row

        # ...existing code up to main_row...
        main_row = QtWidgets.QHBoxLayout()
        main_row.setSpacing(24)
        main_row.addWidget(metrics_container)
        main_row.addWidget(self.hum_plot, 1)
        main_row.addWidget(self.temp_plot, 1)
        main_row.addWidget(self.moisture_plot, 1)

        # Add autoscale button near the plots
        autoscale_btn = QtWidgets.QPushButton("Auto Scale Plots")
        autoscale_btn.setToolTip("Automatically rescale all plots to fit the data.")
        autoscale_btn.clicked.connect(self._autoscale_plots)

        plots_and_btn = QtWidgets.QVBoxLayout()
        plots_and_btn.addLayout(main_row)
        plots_and_btn.addWidget(autoscale_btn, alignment=QtCore.Qt.AlignRight)

        # Plant widget and navigation
        self.current_plant_index = 0
        self._load_plant_data()
        self.plant_widget = QtWidgets.QGroupBox("Plant Preferences")
        plant_layout = QtWidgets.QGridLayout()
        plant_layout.setContentsMargins(16, 32, 16, 16)
        plant_layout.setSpacing(12)
        # Plant selection dropdown
        self.plant_combo = QtWidgets.QComboBox()
        self._populate_plant_combo()
        self.plant_combo.currentIndexChanged.connect(self._on_plant_selected)
        plant_layout.addWidget(self.plant_combo, 0, 0, 1, 2)
        self.temp_range_label = QtWidgets.QLabel()
        self.hum_range_label = QtWidgets.QLabel()
        self.aq_label = QtWidgets.QLabel()
        self.moisture_label = QtWidgets.QLabel()
        plant_layout.addWidget(self.temp_range_label, 1, 0)
        plant_layout.addWidget(self.hum_range_label, 1, 1)
        plant_layout.addWidget(self.aq_label, 2, 0)
        plant_layout.addWidget(self.moisture_label, 2, 1)
        self._update_plant_widget()
        self.plant_widget.setLayout(plant_layout)
        self.plant_widget.setStyleSheet("QGroupBox { font-size: 18px; font-weight: bold; color: #4CAF50; border: 1.5px solid #4CAF50; border-radius: 8px; margin-top: 10px; padding-top: 18px; } QLabel { font-size: 16px; color: #e0e6ed; }")

        nav_layout = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Add Plant")
        self.remove_btn = QtWidgets.QPushButton("Remove Plant")
        # Add Analysis button
        self.analysis_btn = QtWidgets.QPushButton("Analysis")
        nav_layout.addWidget(self.add_btn)
        nav_layout.addWidget(self.remove_btn)
        nav_layout.addWidget(self.analysis_btn)
        self.add_btn.clicked.connect(self._add_plant_dialog)
        self.remove_btn.clicked.connect(self._remove_plant)
        self.analysis_btn.clicked.connect(self._start_analysis)

        # Progress bar for analysis
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Analyzing... %p%")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        # Add a progress bar for analysis below nav_layout
        self.analysis_progress = QtWidgets.QProgressBar()
        self.analysis_progress.setMinimum(0)
        self.analysis_progress.setMaximum(60)
        self.analysis_progress.setValue(0)
        self.analysis_progress.setVisible(False)

        # Add a persistent warning label below the plots
        self.warning_label = QtWidgets.QLabel()
        self.warning_label.setStyleSheet("color: #F44336; font-size: 16px; font-weight: bold; margin: 8px 0;")
        self.warning_label.setAlignment(QtCore.Qt.AlignCenter)

        # --- Serial Monitor Panel ---
        self.serial_monitor = SerialMonitorWidget()
        self.serial_monitor.serial_send_btn.clicked.connect(self._send_serial_message)
        self.serial_monitor.serial_input.returnPressed.connect(self._send_serial_message)

        # Compose the main layout
        central = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(central)
        outer.addLayout(topbar)
        outer.addSpacing(10)
        outer.addLayout(plots_and_btn, 1)
        outer.addSpacing(10)
        outer.addWidget(self.plant_widget)
        outer.addLayout(nav_layout)
        outer.addWidget(self.progress_bar)  # Add progress bar to the layout
        outer.addWidget(self.analysis_progress)  # Add analysis progress bar
        outer.addWidget(self.warning_label)  # Add warning label to the layout
        outer.addWidget(self.serial_monitor)

        # Wrap the central widget in a scroll area
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(central)
        self.setCentralWidget(scroll_area)

        # Add a title label at the top
        title = QtWidgets.QLabel("🌿 Arduino Environment Monitor")
        title.setObjectName("titleLabel")
        title.setAlignment(QtCore.Qt.AlignCenter)
        outer.insertWidget(0, title)

        # Add tooltips for controls
        self.port_combo.setToolTip("Select the serial port for your Arduino device.")
        self.baud_combo.setToolTip("Select the baud rate (communication speed).")
        self.refresh_btn.setToolTip("Refresh the list of available serial ports.")
        self.connect_btn.setToolTip("Connect or disconnect from the Arduino.")

        # Add a status bar for user feedback
        self.statusBar().showMessage("Ready. Select a port and connect to begin.")

        self._last_serial_line = None

    def _populate_baud_rates(self):
        for br in (9600, 19200, 38400, 57600, 115200, 250000):
            self.baud_combo.addItem(str(br), br)
        self.baud_combo.setCurrentText("9600")

    def refresh_ports(self):
        self.port_combo.clear()
        for p in list_ports.comports():
            self.port_combo.addItem(f"{p.device} — {p.description}", p.device)

    def toggle_connection(self):
        (self._disconnect if self.ser and self.ser.is_open else self._connect)()

    def _connect(self):
        port = self.port_combo.currentData()
        baud = int(self.baud_combo.currentData())
        if not port:
            QtWidgets.QMessageBox.warning(self, "No port", "Select a serial port.")
            return
        try:
            self.ser = serial.Serial(port, baud, timeout=0.05)
        except serial.SerialException as e:
            QtWidgets.QMessageBox.critical(self, "Connection failed", str(e))
            return
        self._set_led("green"); self.connect_btn.setText("Disconnect")
        for w in (self.port_combo, self.baud_combo, self.refresh_btn):
            w.setEnabled(False)
        self.timer.start()
        # Send plant thresholds to Arduino after connecting
        self._send_plant_thresholds_to_arduino()

    def _send_plant_thresholds_to_arduino(self):
        if self.ser and self.ser.is_open and self.plant_data:
            plant = self.plant_data[self.current_plant_index]
            # Compose the string: temp_low,temp_high,humidity_low,humidity_high,air_quality_required\n
            msg = f"{plant.get('temperature_low',0)},{plant.get('temperature_high',0)},{plant.get('humidity_low',0)},{plant.get('humidity_high',0)},{plant.get('air_quality_score_min',0)},{plant.get('moisture_low',0)},{plant.get('moisture_high',1000)}\n"
            print(f"[LOG] Sending to Arduino: {msg.strip()}")
            try:
                self.ser.write(msg.encode('utf-8'))
            except Exception as e:
                print(f"Failed to send plant thresholds: {e}")

    def _disconnect(self):
        self.timer.stop()
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None; self._set_led("red"); self.connect_btn.setText("Connect")
        for w in (self.port_combo, self.baud_combo, self.refresh_btn):
            w.setEnabled(True)

    def _read_serial_line(self):
        """Read and decode a line from the serial port."""
        return self.ser.readline().decode("utf-8", "ignore").strip()

    def _timer_tick(self):
        if not (self.ser and self.ser.is_open):
            return
        self._last_serial_line = self._read_serial_line()
        self.update_plot(line_override=self._last_serial_line)
        # If analysis is running, _collect_analysis_sample will use this line

    def _send_serial_message(self):
        msg = self.serial_monitor.serial_input.text().strip()
        if msg and self.ser and self.ser.is_open:
            try:
                self.ser.write((msg + '\n').encode('utf-8'))
                self.serial_monitor.append_tx(msg)
            except Exception as e:
                self.serial_monitor.append_error(f"Failed to send: {e}")
        self.serial_monitor.serial_input.clear()

    def update_plot(self, line_override=None):
        if not (self.ser and self.ser.is_open):
            return
        try:
            line = line_override if line_override is not None else self._read_serial_line()
            if not line:
                return
            # Ignore lines that are not standard real-time data (e.g., lists or analysis responses)
            if line.startswith("[") or "NaN" in line:
                return
            self.serial_monitor.append_rx(line)  # Show all received lines
            print(f"[RX] {line}")  # Print only what is shown in GUI
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 13:
                return

            temp = float(parts[0])
            humidity = float(parts[1])
            moisture = float(parts[2])
            quality = int(parts[3])
            temp_avg = float(parts[4])
            humidity_avg = float(parts[5])
            moisture_avg = float(parts[6])
            temp_too_high = int(parts[7])
            temp_too_low = int(parts[8])
            humidity_too_low = int(parts[9])
            humidity_too_high = int(parts[10])
            soil_too_dry = int(parts[11])
            air_quality_issue = int(parts[12])

            print(f"Received: Temp={temp}, Humidity={humidity}, Moisture={moisture}, Quality={quality}, TempAvg={temp_avg}, HumAvg={humidity_avg}, MoistAvg={moisture_avg}, T_High={temp_too_high}, T_Low={temp_too_low}, H_Low={humidity_too_low}, H_High={humidity_too_high}, SoilDry={soil_too_dry}, AQ_Issue={air_quality_issue}")

            # Update left widget with current temp/humidity
            self.temp_card.set_value(f"{temp:.1f}")
            self.hum_card.set_value(f"{humidity:.1f}")
            self.moisture_card.set_value(f"{moisture:.0f}")
            self._update_quality(quality)

            # Update plot with averages
            self.t_data.append(temp_avg)
            self.h_data.append(humidity_avg)
            self.m_data.append(moisture_avg)
            x_raw = np.arange(len(self.h_data))
            x_fine = np.linspace(x_raw[0], x_raw[-1], len(self.h_data) * 4)
            h_interp = np.interp(x_fine, x_raw, list(self.h_data))
            t_interp = np.interp(x_fine, x_raw, list(self.t_data))
            m_interp = np.interp(x_fine, x_raw, list(self.m_data))
            self.hum_curve.setData(x_fine, h_interp)
            self.temp_curve.setData(x_fine, t_interp)
            self.moisture_curve.setData(x_fine, m_interp)

            # Update threshold lines from current plant
            plant = self.plant_data[self.current_plant_index] if self.plant_data else None
            if plant:
                self.hum_thresh_low.setValue(plant.get('humidity_low', 0))
                self.hum_thresh_high.setValue(plant.get('humidity_high', 100))
                self.temp_thresh_low.setValue(plant.get('temperature_low', 0))
                self.temp_thresh_high.setValue(plant.get('temperature_high', 100))
                self.moisture_thresh_low.setValue(plant.get('moisture_low', 0))
                self.moisture_thresh_high.setValue(plant.get('moisture_high', 1000))

            # Collect warnings for display
            warnings = []
            if temp_too_high:
                warnings.append("Temperature is too high!")
            if temp_too_low:
                warnings.append("Temperature is too low!")
            if humidity_too_low:
                warnings.append("Humidity is too low!")
            if humidity_too_high:
                warnings.append("Humidity is too high!")
            if soil_too_dry:
                warnings.append("Soil is too dry!")
            if air_quality_issue:
                warnings.append("Air quality issue detected!")
            self.warning_label.setText("<br>".join(warnings) if warnings else "")

        except (ValueError, serial.SerialException):
            # Only show lost connection if the line is not an analysis/unknown line
            pass  # Ignore parse errors for unfamiliar lines

    def _collect_analysis_sample(self):
        if not (self.ser and self.ser.is_open):
            self.analysis_timer.stop()
            self.statusBar().showMessage("Serial not connected. Analysis aborted.")
            self.analysis_progress.setVisible(False)
            return
        try:
            line = self._last_serial_line
            valid = False
            if line:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 10:
                    temp = float(parts[0])
                    humidity = float(parts[1])
                    quality = int(parts[2])
                    self.analysis_data.append((temp, humidity, quality))
                    valid = True
            if valid:
                self.analysis_elapsed += 1
                self.analysis_progress.setValue(self.analysis_elapsed)
            # No need to call update_plot here, as it's already called in _timer_tick
            if self.analysis_elapsed >= self.analysis_target:
                self.analysis_timer.stop()
                self.analysis_progress.setVisible(False)
                self._show_analysis_result()
                self.statusBar().showMessage("Analysis complete.")
        except Exception as e:
            self.analysis_timer.stop()
            self.analysis_progress.setVisible(False)
            self.statusBar().showMessage(f"Analysis error: {e}")

    def _update_quality(self, score: int):
        label = {3: "Excellent", 2: "Good", 1: "Fair", 0: "Poor"}.get(score, "Unknown")
        colour = {3: "#4CAF50", 2: "#8BC34A", 1: "#FFC107", 0: "#F44336"}.get(score, "#607D8B")
        self.aq_card.set_value(label)
        self.aq_card.value_bg.setStyleSheet(
            f"background:{colour}; border-radius:6px; padding:8px 12px;"
            "color:#000; font-weight:600; font-size:28px;"
        )

    def _set_led(self, col):
        self.led.setStyleSheet(
            f"border-radius:8px; background-color:{col}; border:1px solid #444;"
        )

    def _apply_dark_theme(self):
        self.setStyleSheet(
            """
            QWidget      { background: #181c24; color: #e0e6ed; font-family: 'Segoe UI', 'Inter', Arial, sans-serif; font-size: 15px; }
            QMainWindow  { background: #181c24; }
            QPushButton  { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2d3542, stop:1 #232834); border: 1px solid #3a4252; border-radius: 6px; padding: 6px 14px; color: #e0e6ed; font-weight: 500; }
            QPushButton:hover { background: #3a4252; color: #fff; }
            QComboBox    { background: #232834; border: 1px solid #3a4252; border-radius: 5px; padding: 4px 10px; color: #e0e6ed; }
            QComboBox QAbstractItemView { background: #232834; color: #e0e6ed; selection-background-color: #2d3542; }
            QProgressBar { background: #232834; border: 1px solid #3a4252; border-radius: 5px; height: 12px; }
            QProgressBar::chunk { background: #4CAF50; border-radius: 5px; }
            QTableWidget { background: #20232a; color: #e0e6ed; border: 1px solid #3a4252; border-radius: 6px; }
            QHeaderView::section { background: #232834; color: #b0b8c1; border: none; font-weight: 600; font-size: 14px; padding: 6px; }
            QLabel#titleLabel { font-size: 22px; font-weight: bold; color: #4CAF50; letter-spacing: 1px; }
            QFrame[card="true"] { background: #232834; border-radius: 10px; border: 1.5px solid #2d3542; }
            """
        )
        pg.setConfigOption("background", "#181c24")
        pg.setConfigOption("foreground", "#e0e6ed")

    def closeEvent(self, ev):
        # Save serial log with timestamp on close
        import datetime
        log_text = self.serial_monitor.serial_text.toPlainText()
        if log_text.strip():
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = os.path.join(os.path.dirname(__file__), f"serial_log_{timestamp}.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(log_text)
        self._disconnect()
        super().closeEvent(ev)

    def _load_plant_data(self):
        with open(os.path.join(os.path.dirname(__file__), 'plant_preferences.json'), 'r') as f:
            self.plant_data = json.load(f)["plants"]

    def _save_plant_data(self):
        with open(os.path.join(os.path.dirname(__file__), 'plant_preferences.json'), 'w') as f:
            json.dump({"plants": self.plant_data}, f, indent=2)

    def _populate_plant_combo(self):
        self.plant_combo.blockSignals(True)
        self.plant_combo.clear()
        for plant in self.plant_data:
            self.plant_combo.addItem(plant["name"])
        self.plant_combo.setCurrentIndex(self.current_plant_index)
        self.plant_combo.blockSignals(False)

    def _on_plant_selected(self, idx):
        if 0 <= idx < len(self.plant_data):
            self.current_plant_index = idx
            self._update_plant_widget()
            # Update threshold lines when plant changes
            plant = self.plant_data[self.current_plant_index]
            self.hum_thresh_low.setValue(plant.get('humidity_low', 0))
            self.hum_thresh_high.setValue(plant.get('humidity_high', 100))
            self.temp_thresh_low.setValue(plant.get('temperature_low', 0))
            self.temp_thresh_high.setValue(plant.get('temperature_high', 100))
            self.moisture_thresh_low.setValue(plant.get('moisture_low', 0))
            self.moisture_thresh_high.setValue(plant.get('moisture_high', 1000))
            # Send new plant thresholds to Arduino
            self._send_plant_thresholds_to_arduino()

    def _update_plant_widget(self):
        if not self.plant_data:
            self.temp_range_label.setText("No plants available.")
            self.hum_range_label.setText("")
            if hasattr(self, 'aq_label'): self.aq_label.setText("")
            if hasattr(self, 'moisture_label'): self.moisture_label.setText("")
            self.plant_combo.setCurrentIndex(-1)
            return
        plant = self.plant_data[self.current_plant_index]
        self.temp_range_label.setText(f"Preferred Temperature: <b>{plant['temperature_low']}°C - {plant['temperature_high']}°C</b>")
        self.hum_range_label.setText(f"Preferred Humidity: <b>{plant['humidity_low']}% - {plant['humidity_high']}%</b>")
        # Add air quality and moisture if present
        layout = self.plant_widget.layout()
        if not hasattr(self, 'aq_label'):
            self.aq_label = QtWidgets.QLabel()
            if layout is not None:
                layout.addWidget(self.aq_label)
        if not hasattr(self, 'moisture_label'):
            self.moisture_label = QtWidgets.QLabel()
            if layout is not None:
                layout.addWidget(self.moisture_label)
        aq = plant.get('air_quality_score_min', None)
        if aq is not None:
            self.aq_label.setText(f"Min Air Quality Score: <b>{aq}</b>")
        else:
            self.aq_label.setText("")
        moist_low = plant.get('moisture_low', None)
        moist_high = plant.get('moisture_high', None)
        if moist_low is not None and moist_high is not None:
            self.moisture_label.setText(f"Preferred Moisture: <b>{moist_low} - {moist_high}</b>")
        else:
            self.moisture_label.setText("")
        self.plant_combo.setCurrentIndex(self.current_plant_index)

    def _remove_plant(self):
        if not self.plant_data:
            return
        idx = self.current_plant_index
        removed_plant = self.plant_data.pop(idx)
        self._save_plant_data()
        if self.plant_data:
            self.current_plant_index = min(idx, len(self.plant_data) - 1)
        else:
            self.current_plant_index = 0
        self._populate_plant_combo()
        self._update_plant_widget()

    def _add_plant_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add New Plant")
        layout = QtWidgets.QFormLayout(dialog)
        name_edit = QtWidgets.QLineEdit()
        temp_low_edit = QtWidgets.QSpinBox(); temp_low_edit.setRange(-30, 60)
        temp_high_edit = QtWidgets.QSpinBox(); temp_high_edit.setRange(-30, 60)
        hum_low_edit = QtWidgets.QSpinBox(); hum_low_edit.setRange(0, 100)
        hum_high_edit = QtWidgets.QSpinBox(); hum_high_edit.setRange(0, 100)
        layout.addRow("Plant Name:", name_edit)
        layout.addRow("Temp Low (°C):", temp_low_edit)
        layout.addRow("Temp High (°C):", temp_high_edit)
        layout.addRow("Humidity Low (%):", hum_low_edit)
        layout.addRow("Humidity High (%):", hum_high_edit)
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addRow(btn_box)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            name = name_edit.text().strip()
            temp_low = temp_low_edit.value()
            temp_high = temp_high_edit.value()
            hum_low = hum_low_edit.value()
            hum_high = hum_high_edit.value()
            if name:
                self.plant_data.append({
                    "name": name,
                    "temperature_low": temp_low,
                    "temperature_high": temp_high,
                    "humidity_low": hum_low,
                    "humidity_high": hum_high
                })
                self._save_plant_data()
                self.current_plant_index = len(self.plant_data) - 1
                self._populate_plant_combo()
                self._update_plant_widget()

    def _start_analysis(self):
        # Send 'd' command to Arduino to request data lists
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b'd\n')
                self.serial_monitor.append_tx('d')
            except Exception as e:
                self.serial_monitor.append_error(f"Failed to send analysis command: {e}")
                return
        self.statusBar().showMessage("Waiting for analysis data from Arduino...")
        self.analysis_data_lists = []
        self.analysis_air_quality = None
        self.analysis_timer = QtCore.QTimer(self)
        self.analysis_timer.timeout.connect(self._collect_analysis_lists)
        self.analysis_timer.start(100)

    def _collect_analysis_lists(self):
        if not (self.ser and self.ser.is_open):
            self.analysis_timer.stop()
            self.statusBar().showMessage("Serial not connected. Analysis aborted.")
            return
        try:
            line = self._read_serial_line()
            if not line:
                return
            self.serial_monitor.append_rx(line)
            # Only process lines that look like analysis lists (contain many commas and 'nan' or '[')
            if (line.startswith('[') and line.endswith(']')) or (line.count(',') > 20 and ('nan' in line or 'NaN' in line)):
                # Remove brackets if present
                line_clean = line.strip('[]')
                # Parse list, ignore NaN/nan/empty
                values = [float(x) for x in line_clean.split(',') if x.strip().lower() not in ('nan', '')]
                self.analysis_data_lists.append(values)
            elif line.isdigit() or (line.replace('.', '', 1).isdigit() and '.' in line):
                # Air quality value (int or float)
                self.analysis_air_quality = float(line)
            # When we have 3 lists and air quality, process
            if len(self.analysis_data_lists) == 3 and self.analysis_air_quality is not None:
                self.analysis_timer.stop()
                self._show_analysis_result_lists()
                self.statusBar().showMessage("Analysis complete.")
        except Exception as e:
            self.analysis_timer.stop()
            self.statusBar().showMessage(f"Analysis error: {e}")

    def _show_analysis_result_lists(self):
        if len(self.analysis_data_lists) != 3 or self.analysis_air_quality is None:
            QtWidgets.QMessageBox.information(self, "Analysis Result", "Incomplete data received.")
            return
        temps, hums, moistures = self.analysis_data_lists
        # Filter out empty lists
        temps = [v for v in temps if isinstance(v, (int, float))]
        hums = [v for v in hums if isinstance(v, (int, float))]
        moistures = [v for v in moistures if isinstance(v, (int, float))]
        if not temps or not hums or not moistures:
            QtWidgets.QMessageBox.information(self, "Analysis Result", "No valid data received.")
            return
        avg_temp = sum(temps) / len(temps)
        avg_hum = sum(hums) / len(hums)
        avg_moist = sum(moistures) / len(moistures)
        avg_aq = round(self.analysis_air_quality)
        # Find suitable plants
        suitable = []
        for plant in self.plant_data:
            if (plant['temperature_low'] <= avg_temp <= plant['temperature_high'] and
                plant['humidity_low'] <= avg_hum <= plant['humidity_high'] and
                plant.get('moisture_low', 0) <= avg_moist <= plant.get('moisture_high', 1000) and
                avg_aq >= plant.get('air_quality_score_min', 0)):
                suitable.append(plant['name'])
        # Show result in a table
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Analysis Result")
        layout = QtWidgets.QVBoxLayout(dialog)
        summary = QtWidgets.QLabel(f"<b>Average Temp:</b> {avg_temp:.1f}°C   <b>Average Humidity:</b> {avg_hum:.1f}%   <b>Average Moisture:</b> {avg_moist:.1f}   <b>Air Quality:</b> {avg_aq}")
        layout.addWidget(summary)
        table = QtWidgets.QTableWidget(dialog)
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["Suitable Plants"])
        table.setRowCount(len(suitable))
        for i, name in enumerate(suitable):
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(name))
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)
        if not suitable:
            layout.addWidget(QtWidgets.QLabel("<b>No plants can survive under these conditions.</b>"))
        btn = QtWidgets.QPushButton("OK", dialog)
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.exec_()

        # Hide progress bar after analysis
        self.progress_bar.hide()

    def _autoscale_plots(self):
        self.hum_plot.enableAutoRange(axis="y", enable=True)
        self.hum_plot.enableAutoRange(axis="x", enable=True)
        self.temp_plot.enableAutoRange(axis="y", enable=True)
        self.temp_plot.enableAutoRange(axis="x", enable=True)
        self.moisture_plot.enableAutoRange(axis="y", enable=True)
        self.moisture_plot.enableAutoRange(axis="x", enable=True)
        self.env_plot.enableAutoRange(axis="y", enable=True)
        self.env_plot.enableAutoRange(axis="x", enable=True)