from PyQt5 import QtCore, QtWidgets, QtGui
import serial
from serial.tools import list_ports
from collections import deque
import numpy as np
import pyqtgraph as pg
from widgets import MetricCard, SerialMonitorWidget, MoistureCard
import json
import os
from sklearn.linear_model import LinearRegression
import datetime # Ensure datetime is imported at the top

class AnalysisResultsDialog(QtWidgets.QDialog):
    def __init__(self, avg_temp, avg_hum, avg_moist, avg_aq, 
                 raw_temps, raw_hums, raw_moists, 
                 suitable_plants, closest_plants_details, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detailed Analysis Results")
        self.setMinimumSize(1000, 950)
        self.parent_window = parent

        # Main layout for the dialog (will be set as the widget for QScrollArea)
        main_layout = QtWidgets.QVBoxLayout()

        # Summary Section
        summary_group = QtWidgets.QGroupBox("Average Conditions")
        summary_layout = QtWidgets.QFormLayout(summary_group)
        summary_layout.addRow("Average Temperature:", QtWidgets.QLabel(f"{avg_temp:.1f}°C"))
        summary_layout.addRow("Average Humidity:", QtWidgets.QLabel(f"{avg_hum:.1f}%"))
        summary_layout.addRow("Average Moisture:", QtWidgets.QLabel(f"{avg_moist:.1f}"))
        summary_layout.addRow("Air Quality Score:", QtWidgets.QLabel(f"{avg_aq}"))
        main_layout.addWidget(summary_group)

        # Time axis for 10-minute intervals
        time_points = [i * 10 for i in range(len(raw_temps))]

        # Temperature Plot (lines only, no markers)
        self.raw_temps_plot = pg.PlotWidget()
        self.raw_temps_plot.setTitle("Temperature Averages (10-minute intervals)")
        self.raw_temps_plot.setLabel('left', 'Temperature', units='°C')
        self.raw_temps_plot.setLabel('bottom', 'Time', units='minutes')
        self.raw_temps_plot.plot(time_points, raw_temps, pen=pg.mkPen('#FF9800', width=2))
        self.raw_temps_plot.setMinimumHeight(220)
        self.raw_temps_plot.showGrid(x=True, y=True, alpha=0.3)
        self.raw_temps_plot.getPlotItem().getAxis('bottom').setStyle(showValues=True, autoExpandTextSpace=True)
        main_layout.addWidget(self.raw_temps_plot)

        # Humidity Plot (lines only, no markers)
        self.raw_hums_plot = pg.PlotWidget()
        self.raw_hums_plot.setTitle("Humidity Averages (10-minute intervals)")
        self.raw_hums_plot.setLabel('left', 'Humidity', units='%')
        self.raw_hums_plot.setLabel('bottom', 'Time', units='minutes')
        self.raw_hums_plot.plot(time_points, raw_hums, pen=pg.mkPen('#2196F3', width=2))
        self.raw_hums_plot.setMinimumHeight(220)
        self.raw_hums_plot.showGrid(x=True, y=True, alpha=0.3)
        self.raw_hums_plot.getPlotItem().getAxis('bottom').setStyle(showValues=True, autoExpandTextSpace=True)
        main_layout.addWidget(self.raw_hums_plot)

        # Moisture Plot (lines only, no markers)
        self.raw_moists_plot = pg.PlotWidget()
        self.raw_moists_plot.setTitle("Moisture Averages (10-minute intervals)")
        self.raw_moists_plot.setLabel('left', 'Moisture')
        self.raw_moists_plot.setLabel('bottom', 'Time', units='minutes')
        self.raw_moists_plot.plot(time_points, raw_moists, pen=pg.mkPen('#8BC34A', width=2))
        self.raw_moists_plot.setMinimumHeight(220)
        self.raw_moists_plot.showGrid(x=True, y=True, alpha=0.3)
        self.raw_moists_plot.getPlotItem().getAxis('bottom').setStyle(showValues=True, autoExpandTextSpace=True)
        main_layout.addWidget(self.raw_moists_plot)

        # Plant Suitability Section
        plant_suitability_group = QtWidgets.QGroupBox("Plant Suitability")
        plant_suitability_layout = QtWidgets.QVBoxLayout(plant_suitability_group)

        if suitable_plants:
            plant_suitability_layout.addWidget(QtWidgets.QLabel("<b>Perfectly Suitable Plants:</b>"))
            list_widget = QtWidgets.QListWidget()
            for plant_name in suitable_plants:
                list_widget.addItem(plant_name)
            plant_suitability_layout.addWidget(list_widget)
        elif closest_plants_details:
            plant_suitability_layout.addWidget(QtWidgets.QLabel("<b>No perfectly suitable plants found. Top 3 closest matches:</b>"))
            table = QtWidgets.QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["Plant Name", "Match Score (out of 4)", "Details"])
            table.setRowCount(len(closest_plants_details))
            table.setMinimumHeight(250)
            table.setAlternatingRowColors(False)  # Disable alternating to set all rows manually
            for i, details in enumerate(closest_plants_details):
                for j in range(3):
                    item = None
                    if j == 0:
                        item = QtWidgets.QTableWidgetItem(details['name'])
                    elif j == 1:
                        item = QtWidgets.QTableWidgetItem(f"{details['score']}/4")
                    elif j == 2:
                        unmet_summary = []
                        if not details['met_temp']:
                            unmet_summary.append(f"Temp: {avg_temp:.1f}°C (Needs: {details['plant_temp_low']}-{details['plant_temp_high']}°C)")
                        if not details['met_hum']:
                            unmet_summary.append(f"Hum: {avg_hum:.1f}% (Needs: {details['plant_hum_low']}-{details['plant_hum_high']}%)")
                        if not details['met_moist']:
                            unmet_summary.append(f"Moist: {avg_moist:.1f} (Needs: {details['plant_moist_low']}-{details['plant_moist_high']})")
                        if not details['met_aq']:
                            unmet_summary.append(f"AQ: {avg_aq} (Needs >= {details['plant_aq_min']})")
                        item = QtWidgets.QTableWidgetItem("; ".join(unmet_summary) if unmet_summary else "All conditions met")
                    # Set a consistent background color for all rows
                    item.setBackground(QtGui.QColor("#232834"))
                    item.setForeground(QtGui.QColor("#e0e6ed"))
                    table.setItem(i, j, item)
            table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            for i in range(table.rowCount()):
                table.setRowHeight(i, 60)
            plant_suitability_layout.addWidget(table)
        else:
            plant_suitability_layout.addWidget(QtWidgets.QLabel("No plant data available or no matches found."))
        main_layout.addWidget(plant_suitability_group)

        # Timing info label at the very bottom
        timing_label = QtWidgets.QLabel("Each point = 10 minutes, leftmost = oldest")
        timing_label.setAlignment(QtCore.Qt.AlignCenter)
        timing_label.setStyleSheet("color: #888; font-size: 13px; margin-top: 10px;")
        main_layout.addWidget(timing_label)

        # Button layout for OK and Reset
        button_layout = QtWidgets.QHBoxLayout()
        reset_button = QtWidgets.QPushButton("Reset Arduino Data")
        reset_button.setToolTip("Send reset command to Arduino to clear stored data")
        reset_button.setStyleSheet("QPushButton { background-color: #F44336; color: white; font-weight: bold; }")
        reset_button.clicked.connect(self._reset_arduino_data)
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        main_layout.addLayout(button_layout)

        # Wrap the main layout in a scroll area for vertical scrolling only
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        scroll_content.setLayout(main_layout)
        scroll_area.setWidget(scroll_content)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        # Set the scroll area as the main layout
        dialog_layout = QtWidgets.QVBoxLayout(self)
        dialog_layout.addWidget(scroll_area)
        self.setLayout(dialog_layout)

    def _reset_arduino_data(self):
        if self.parent_window and hasattr(self.parent_window, '_send_serial_message'):
            try:
                self.parent_window._send_serial_message('r', log_to_monitor=True)
                QtWidgets.QMessageBox.information(self, "Reset Command Sent", 
                    "Reset command 'r' has been sent to Arduino.\nArduino should respond with 'Reset data'.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Reset Failed", 
                    f"Failed to send reset command: {str(e)}")
        else:
            QtWidgets.QMessageBox.warning(self, "Reset Failed", 
                "Cannot send reset command - no connection to Arduino.")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🌿 Arduino Environment Monitor")
        self.resize(1100, 700)

        self.ser = None
        self.h_data = deque([0.0] * 50, maxlen=50)
        self.t_data = deque([0.0] * 50, maxlen=50)
        self.m_data = deque([0.0] * 50, maxlen=50)
        self.timer = QtCore.QTimer(self, interval=200) # Main timer for serial reads
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
        self.forecast_btn = QtWidgets.QPushButton("Forecast Next Values") # New Forecast button
        nav_layout.addWidget(self.add_btn)
        nav_layout.addWidget(self.remove_btn)
        nav_layout.addWidget(self.analysis_btn)
        nav_layout.addWidget(self.forecast_btn) # Add forecast button to layout
        self.add_btn.clicked.connect(self._add_plant_dialog)
        self.remove_btn.clicked.connect(self._remove_plant)
        self.analysis_btn.clicked.connect(self._start_analysis)
        self.forecast_btn.clicked.connect(self._forecast_next) # Connect forecast button

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

        # Central place to store the last read line, processed by _timer_tick
        self._last_raw_serial_line = None

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
        self.is_collecting_analysis_data = False
        self.last_known_real_time_aq = None
        self.raw_analysis_lines = [] # Initialize to store raw d, lines

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
        # REMOVED: self._send_plant_thresholds_to_arduino() - No longer sending immediately on connect

    def _send_serial_message(self, msg=None, log_to_monitor=True): # Added default for msg
        if msg is None: # Handle case where called by button click without explicit msg
            msg = self.serial_monitor.serial_input.text()
            if not msg:
                return # Don't send empty message
            self.serial_monitor.serial_input.clear() # Clear input after getting text

        if self.ser and self.ser.is_open: # Changed from self.serial_port to self.ser
            try:
                final_msg = msg if msg.endswith('\\n') else msg + '\\n'
                self.ser.write(final_msg.encode()) # Changed from self.serial_port to self.ser
                # Consistent logging
                print(f"[SERIAL_OUT] {final_msg.strip()}")
                if log_to_monitor and self.serial_monitor:
                    self.serial_monitor.append_tx(f"{final_msg.strip()}")
            except Exception as e:
                error_msg = f"Failed to send: {e}"
                print(f"[ERROR] {error_msg}")
                self.serial_monitor.append_error(error_msg)

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

        line = self._read_serial_line()
        if not line:
            return

        # Centralized logging for all incoming serial data
        print(f"[SERIAL_IN] {line}")
        self.serial_monitor.append_rx(line)

        self._last_raw_serial_line = line # Store the raw line

        # Conditional processing based on application state
        if self.is_collecting_analysis_data:
            self._handle_analysis_data_line(line)
        else:
            self._handle_normal_data_line(line)

    def _show_forecast_result(self, result):
        msg = f"Forecasted value for the next period: {result[0]:.2f}"
        # self.log_message(f"[INFO] {msg}", level='info') # Assuming log_message is defined elsewhere or remove
        QtWidgets.QMessageBox.information(self, "Forecast Result", msg)

    def _send_plant_thresholds_to_arduino(self):
        if self.ser and self.ser.is_open:
            if not self.plant_data or not (0 <= self.current_plant_index < len(self.plant_data)):
                print("[INFO] No plant data or invalid index to send thresholds for.")
                if hasattr(self, 'serial_monitor') and self.serial_monitor:
                    self.serial_monitor.append_info("[Thresholds] No plant data to send.")
                return

            plant = self.plant_data[self.current_plant_index]
            
            temp_min = plant.get('temperature_low', 0)
            temp_max = plant.get('temperature_high', 100)
            humidity_min = plant.get('humidity_low', 0)
            humidity_max = plant.get('humidity_high', 100)
            air_quality_min = plant.get('air_quality_score_min', 0) # Added
            moisture_min = plant.get('moisture_low', 0) 
            moisture_max = plant.get('moisture_high', 1000)

            # Message format: min_temp,high_temp,min_humidity,high_humidity,min_air_quality,min_moisture,high_moisture
            msg_parts = [
                str(temp_min),
                str(temp_max),
                str(humidity_min),
                str(humidity_max),
                str(air_quality_min),
                str(moisture_min),
                str(moisture_max)
            ]
            
            msg = ",".join(msg_parts) + "\\\\n" # Ensure newline is correctly escaped for serial
            
            try:
                self.ser.write(msg.encode())
                log_msg = f"Thresholds: {msg.strip()}" # Use .strip() for cleaner log
                print(f"[SERIAL_OUT] {log_msg}")
                if self.serial_monitor:
                    self.serial_monitor.append_tx(log_msg)
            except Exception as e:
                error_msg = f"Failed to send plant thresholds: {e}"
                print(f"[ERROR] {error_msg}")
                if self.serial_monitor:
                    self.serial_monitor.append_error(error_msg)
        else:
            print("[INFO] Serial port not open. Cannot send thresholds.")
            if hasattr(self, 'serial_monitor') and self.serial_monitor:
                 self.serial_monitor.append_warning("[Thresholds] Serial port not open.")

    # Removed update_plot method, its logic is now in _handle_normal_data_line

    def _handle_normal_data_line(self, line):
        """Processes a serial line for normal data display and actions."""
        # Logic from former update_plot()
        # Special handling for Arduino startup messages
        if line == "Sensor ready.": # Send thresholds ONLY when "Sensor ready." is received
            self._send_plant_thresholds_to_arduino()
        elif line == "Reset data": # Handle Arduino reset confirmation
            self.serial_monitor.append_info("[Arduino] Data reset confirmed by Arduino.")
            QtWidgets.QMessageBox.information(self, "Reset Confirmed", 
                "Arduino has confirmed that all stored data has been reset.")
            return

        if line.startswith("[") or "NaN" in line or line.startswith('d,'): # Corrected string literal
            return

        try:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 14:
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
            soil_too_wet = int(parts[12])
            air_quality_issue = int(parts[13])

            self.last_known_real_time_aq = float(quality) 

            self.temp_card.set_value(f"{temp:.1f}")
            self.hum_card.set_value(f"{humidity:.1f}")
            self.moisture_card.set_value(f"{moisture:.0f}")
            self._update_quality(quality)

            self.t_data.append(temp_avg)
            self.h_data.append(humidity_avg)
            self.m_data.append(moisture_avg)
            x_raw = np.arange(len(self.h_data))
            
            if len(x_raw) > 1:
                x_fine = np.linspace(x_raw[0], x_raw[-1], len(self.h_data) * 4)
                h_interp = np.interp(x_fine, x_raw, list(self.h_data))
                t_interp = np.interp(x_fine, x_raw, list(self.t_data))
                m_interp = np.interp(x_fine, x_raw, list(self.m_data))
                self.hum_curve.setData(x_fine, h_interp)
                self.temp_curve.setData(x_fine, t_interp)
                self.moisture_curve.setData(x_fine, m_interp)
            elif len(x_raw) == 1: 
                self.hum_curve.setData([x_raw[0]], [self.h_data[-1]])
                self.temp_curve.setData([x_raw[0]], [self.t_data[-1]])
                self.moisture_curve.setData([x_raw[0]], [self.m_data[-1]])


            plant = self.plant_data[self.current_plant_index] if self.plant_data else None
            if plant:
                self.hum_thresh_low.setValue(plant.get('humidity_low', 0))
                self.hum_thresh_high.setValue(plant.get('humidity_high', 100))
                self.temp_thresh_low.setValue(plant.get('temperature_low', 0))
                self.temp_thresh_high.setValue(plant.get('temperature_high', 100))
                self.moisture_thresh_low.setValue(plant.get('moisture_low', 0))
                self.moisture_thresh_high.setValue(plant.get('moisture_high', 1000))

            warnings = []
            if temp_too_high: warnings.append("Temperature is too high!")
            if temp_too_low: warnings.append("Temperature is too low!")
            if humidity_too_low: warnings.append("Humidity is too low!")
            if humidity_too_high: warnings.append("Humidity is too high!")
            if soil_too_dry: warnings.append("Soil is too dry!")
            if soil_too_wet: warnings.append("Soil is too wet!")
            if air_quality_issue: warnings.append("Air quality issue detected!")
            self.warning_label.setText("<br>".join(warnings) if warnings else "")

        except (ValueError, IndexError, TypeError) as e: 
            pass 

    # Removed _collect_analysis_sample method

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
        if not self.plant_data or not (0 <= self.current_plant_index < len(self.plant_data)): # Check if plant_data is valid and index is in range
            self.temp_range_label.setText("Preferred Temperature: <b>N/A</b>")
            self.hum_range_label.setText("Preferred Humidity: <b>N/A</b>")
            if hasattr(self, 'aq_label'): self.aq_label.setText("Min Air Quality Score: <b>N/A</b>")
            if hasattr(self, 'moisture_label'): self.moisture_label.setText("Preferred Moisture: <b>N/A</b>")
            # Clear image and other labels if plant data is not available
            if hasattr(self, 'plant_image_label'): self.plant_image_label.setPixmap(QtGui.QPixmap())
            if hasattr(self, 'light_label'): self.light_label.setText("Preferred Light: <b>N/A</b>")
            if hasattr(self, 'plant_info_label'): self.plant_info_label.setText("General Info: <b>N/A</b>")
            self.plant_combo.setCurrentIndex(-1) # No plant selected or available
            return

        plant = self.plant_data[self.current_plant_index] # Use self.current_plant_index

        # Update image
        if hasattr(self, 'plant_image_label'):
            image_path = plant.get("image")
            if image_path:
                # Construct absolute path if image_path is relative
                base_path = os.path.dirname(__file__)
                abs_image_path = os.path.join(base_path, image_path) if not os.path.isabs(image_path) else image_path
                pixmap = QtGui.QPixmap(abs_image_path) 
                if pixmap.isNull():
                    print(f"Warning: Image not found at {abs_image_path}. Check path.")
                    self.plant_image_label.setText("Image not found")
                else:
                    self.plant_image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            else:
                self.plant_image_label.setPixmap(QtGui.QPixmap()) # Clear if no image path

        # Update temperature and humidity labels (these are always present)
        self.temp_range_label.setText(f"Preferred Temperature: <b>{plant['temperature_low']}°C - {plant['temperature_high']}°C</b>")
        self.hum_range_label.setText(f"Preferred Humidity: <b>{plant['humidity_low']}% - {plant['humidity_high']}%</b>")

        layout = self.plant_widget.layout() 

        if not hasattr(self, 'aq_label'):
            self.aq_label = QtWidgets.QLabel()
            if layout and isinstance(layout, QtWidgets.QGridLayout): 
                layout.addWidget(self.aq_label, 2, 0) 
        aq_min = plant.get('air_quality_score_min', "N/A")
        self.aq_label.setText(f"Min Air Quality Score: <b>{aq_min}</b>")

        if not hasattr(self, 'moisture_label'):
            self.moisture_label = QtWidgets.QLabel()
            if layout and isinstance(layout, QtWidgets.QGridLayout): 
                layout.addWidget(self.moisture_label, 2, 1) 
        moist_low = plant.get('moisture_low', "N/A")
        moist_high = plant.get('moisture_high', "N/A") 
        if moist_low != "N/A" and moist_high != "N/A":
            self.moisture_label.setText(f"Preferred Moisture: <b>{moist_low} - {moist_high}</b>")
        else:
            self.moisture_label.setText("Preferred Moisture: <b>N/A</b>")

        if hasattr(self, 'light_label'):
            light_min = plant.get("light_hours_min", "N/A")
            light_max = plant.get("light_hours_max", "N/A")
            if light_min != "N/A" and light_max != "N/A":
                self.light_label.setText(f"Preferred Light: <b>{light_min} - {light_max} hrs</b>")
            else:
                self.light_label.setText("Preferred Light: <b>N/A</b>")
        
        if hasattr(self, 'plant_info_label'):
            info = plant.get("info", "N/A")
            self.plant_info_label.setText(f"General Info: <b>{info}</b>")

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
        if self.is_collecting_analysis_data:
            self.serial_monitor.append_info("[Analysis] Collection already in progress. Please wait.") 
            self.statusBar().showMessage("Analysis collection already in progress.")
            return

        if not (self.ser and self.ser.is_open):
            self.serial_monitor.append_error("Cannot start analysis: Serial port not open.")
            self.statusBar().showMessage("Cannot start analysis: Serial port not open.")
            return

        try:
            print("[SERIAL_OUT] d")
            self.serial_monitor.append_tx('d')
            self.ser.write(b'd\\n')
            
            self.is_collecting_analysis_data = True
            self.raw_analysis_lines = []
            self.analysis_data_lists = []
            self.statusBar().showMessage("Waiting for 3 'd,' prefixed analysis data lists from Arduino...") # Changed 4 to 3
            self.serial_monitor.append_info("[Analysis] Sent 'd'. Waiting for 3 'd,' prefixed data lists.") # Changed 4 to 3

            # Removed analysis_collection_timer

            if hasattr(self, 'analysis_overall_timeout_timer') and self.analysis_overall_timeout_timer.isActive():
                self.analysis_overall_timeout_timer.stop()
            self.analysis_overall_timeout_timer = QtCore.QTimer(self)
            self.analysis_overall_timeout_timer.setSingleShot(True)
            self.analysis_overall_timeout_timer.timeout.connect(self._handle_analysis_collection_timeout)
            self.analysis_overall_timeout_timer.start(20000) 

        except Exception as e:
            error_msg = f"Failed to send analysis command: {e}"
            print(f"[ERROR] {error_msg}")
            self.serial_monitor.append_error(error_msg)
            self.statusBar().showMessage(error_msg)
            self.is_collecting_analysis_data = False
            if hasattr(self, 'analysis_overall_timeout_timer') and self.analysis_overall_timeout_timer.isActive():
                self.analysis_overall_timeout_timer.stop()

    # read_serial_data is not directly part of the main _timer_tick flow.
    # It's kept for potential future use but needs logging consistency if activated.
    def read_serial_data(self):
        if self.is_collecting_analysis_data: 
            return

        if not (self.ser and self.ser.is_open):
            return

        line = self._read_serial_line()
        if line:
            # If this method were actively used, ensure GUI logging matches terminal logging
            # print(f\"[SERIAL_IN_READ_SERIAL_DATA] {line}\") # Example for terminal
            self.serial_monitor.append_rx(line) 

            if not line.startswith('d,'): 
                try:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 14: 
                        aq_value = float(parts[3]) 
                        self.last_known_real_time_aq = aq_value
                except (ValueError, IndexError):
                    pass 
            # self.process_serial_data(line) # This was commented out, keeping it so.

    # Removed _collect_analysis_lists_step method

    def _handle_analysis_data_line(self, line):
        """Processes a serial line when in analysis data collection mode."""
        if not self.is_collecting_analysis_data:
            return 

        if not (self.ser and self.ser.is_open):
            self._finalize_analysis_collection(error=True, message="Serial not connected during analysis. Aborted.")
            return

        try:
            if line.startswith('d,'):
                self.serial_monitor.append_info(f"[Analysis] Detected raw analysis line: {line}")
                self.raw_analysis_lines.append(line)
                self.serial_monitor.append_info(f"[Analysis] Stored raw line #{len(self.raw_analysis_lines)}.")
            # Non-'d,' lines are already logged by _timer_tick but ignored here for collection purposes.

            if len(self.raw_analysis_lines) == 3: # Changed 4 to 3
                self.serial_monitor.append_info("[Analysis] Collected 3 raw 'd,' lines.") # Changed 4 to 3
                self._finalize_analysis_collection(error=False)

        except Exception as e:
            error_msg = f"[Analysis] Error during analysis line processing: {e}"
            print(f"[ERROR] {error_msg}") 
            self.serial_monitor.append_error(error_msg) 
            self._finalize_analysis_collection(error=True, message=error_msg)

    def _finalize_analysis_collection(self, error=False, message=""):
        self.is_collecting_analysis_data = False # Reset collection flag FIRST

        if hasattr(self, 'analysis_collection_timer') and self.analysis_collection_timer.isActive():
            self.analysis_collection_timer.stop()
        if hasattr(self, 'analysis_overall_timeout_timer') and self.analysis_overall_timeout_timer.isActive():
            self.analysis_overall_timeout_timer.stop()

        if error:
            status_msg = message if message else "Analysis failed or timed out collecting raw lines."
            self.serial_monitor.append_error(f"[Analysis] {status_msg}")
            self.statusBar().showMessage(status_msg)
            return

        # Now parse the collected raw lines
        self.serial_monitor.append_info("[Analysis] Proceeding to parse collected raw lines.")
        self.analysis_data_lists = [] # Ensure it's clean before parsing
        for i, raw_line in enumerate(self.raw_analysis_lines):
            self.serial_monitor.append_info(f"[Analysis] Parsing raw line #{i+1}: {raw_line}")
            line_clean = raw_line[2:].strip('[]').strip() # Remove 'd,' and brackets
            if line_clean.endswith(','):
                line_clean = line_clean[:-1]
            
            parsed_values = []
            if not line_clean: # Handles cases like "d,[]" or "d," or "d,,,"
                self.serial_monitor.append_warning(f"[Analysis] Raw line #{i+1} resulted in empty data after cleaning: '{raw_line}'.")
            else:
                for x_str in line_clean.split(','):
                    x_str = x_str.strip()
                    if x_str.lower() == 'nan':
                        parsed_values.append(float('nan'))
                    elif x_str == '':
                        continue # Skip empty strings resulting from multiple commas e.g. val1,,val2
                    else:
                        try:
                            parsed_values.append(float(x_str))
                        except ValueError as e_parse:
                            self.serial_monitor.append_error(f"[Analysis] Skipped non-numeric value '{x_str}' in raw line #{i+1}: {e_parse}")
            
            self.analysis_data_lists.append(parsed_values)
            self.serial_monitor.append_info(f"[Analysis] Parsed list #{len(self.analysis_data_lists)} from raw line: {parsed_values}") 

        if len(self.analysis_data_lists) != 3: # Changed 4 to 3
            self.serial_monitor.append_error(f"[Analysis] Error: Expected 3 parsed lists, got {len(self.analysis_data_lists)}. Check parsing logic.") # Changed 4 to 3
            self.statusBar().showMessage("Analysis error after parsing: Incorrect number of lists.")
            return

        self.serial_monitor.append_info("[Analysis] Successfully parsed 3 analysis lists.") # Changed 4 to 3
        
        aq_for_report = self.last_known_real_time_aq
        if aq_for_report is not None:
            self.serial_monitor.append_info(f"[Analysis] Using Air Quality from last real-time normal data: {aq_for_report:.2f}") 
        else:
            self.serial_monitor.append_warning("[Analysis] No real-time Air Quality data available for report.")
        
        self.analysis_air_quality = aq_for_report 

        self.serial_monitor.append_info("[Analysis] Analysis data fully processed. Showing results dialog.")
        self._show_analysis_result_lists()
        self.statusBar().showMessage("Analysis complete.")

    def _handle_analysis_collection_timeout(self):
        if self.is_collecting_analysis_data: 
            self._finalize_analysis_collection(error=True, message="Timed out waiting for 3 analysis lists.") # Changed 4 to 3

    def _calculate_plant_match_details(self, plant, avg_temp, avg_hum, avg_moist, avg_aq):
        score = 0
        details = {
            'name': plant['name'],
            'score': 0,
            'met_temp': False, 'plant_temp_low': plant['temperature_low'], 'plant_temp_high': plant['temperature_high'],
            'met_hum': False, 'plant_hum_low': plant['humidity_low'], 'plant_hum_high': plant['humidity_high'],
            'met_moist': False, 'plant_moist_low': plant.get('moisture_low', 0), 'plant_moist_high': plant.get('moisture_high', 1000),
            'met_aq': False, 'plant_aq_min': plant.get('air_quality_score_min', 0)
        }

        if plant['temperature_low'] <= avg_temp <= plant['temperature_high']:
            score += 1
            details['met_temp'] = True
        
        if plant['humidity_low'] <= avg_hum <= plant['humidity_high']:
            score += 1
            details['met_hum'] = True

        if plant.get('moisture_low', 0) <= avg_moist <= plant.get('moisture_high', 1000):
            score += 1
            details['met_moist'] = True
        
        if avg_aq >= plant.get('air_quality_score_min', 0):
            score += 1
            details['met_aq'] = True
        
        details['score'] = score
        return details

    def _show_analysis_result_lists(self):
        if len(self.analysis_data_lists) < 3: 
            QtWidgets.QMessageBox.information(self, "Analysis Result", f"Incomplete data received for report. Expected 3 lists, got {len(self.analysis_data_lists)}.")
            self.progress_bar.hide()
            return
        
        if self.analysis_air_quality is None: # Should be float or int
            QtWidgets.QMessageBox.information(self, "Analysis Result", "Air quality data for report is missing.")
            self.progress_bar.hide()
            return

        temps_raw, hums_raw, moistures_raw = self.analysis_data_lists[0], self.analysis_data_lists[1], self.analysis_data_lists[2]
        
        temps = [v for v in temps_raw if isinstance(v, (int, float)) and not np.isnan(v)]
        hums = [v for v in hums_raw if isinstance(v, (int, float)) and not np.isnan(v)]
        moistures = [v for v in moistures_raw if isinstance(v, (int, float)) and not np.isnan(v)]

        if not temps or not hums or not moistures: 
            QtWidgets.QMessageBox.information(self, "Analysis Result", "No valid numeric data in the first three lists for analysis report after filtering NaNs and non-numeric values.")
            self.progress_bar.hide()
            return

        avg_temp = sum(temps) / len(temps)
        avg_hum = sum(hums) / len(hums)
        avg_moist = sum(moistures) / len(moistures)
        
        # Ensure avg_aq is a number before rounding, handle if it's None or non-numeric string
        try:
            avg_aq = round(float(self.analysis_air_quality))
        except (ValueError, TypeError):
             QtWidgets.QMessageBox.warning(self, "Analysis Error", "Invalid Air Quality value for analysis.")
             self.progress_bar.hide()
             return

        suitable_plants = []
        all_plant_match_details = []

        for plant in self.plant_data:
            match_details = self._calculate_plant_match_details(plant, avg_temp, avg_hum, avg_moist, avg_aq)
            all_plant_match_details.append(match_details)
            if match_details['score'] == 4: # All conditions met
                suitable_plants.append(plant['name'])
        
        closest_plants_details_for_dialog = []
        if not suitable_plants and all_plant_match_details:
            # Sort by score (descending), then by name (ascending) as a tie-breaker
            all_plant_match_details.sort(key=lambda x: (-x['score'], x['name']))
            closest_plants_details_for_dialog = all_plant_match_details[:3]

        # Show the new detailed results dialog
        dialog = AnalysisResultsDialog(
            avg_temp, avg_hum, avg_moist, avg_aq,
            temps_raw, hums_raw, moistures_raw,
            suitable_plants, closest_plants_details_for_dialog, self
        )
        dialog.exec_()

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

    def _forecast_next(self):
        # Use last N points for each series
        N = 20
        def forecast(data):
            y = np.array(list(data)[-N:])
            X = np.arange(len(y)).reshape(-1, 1)
            if len(y) < 2 or np.all(y == y[0]): # Check if all elements are the same
                return y[-1] if len(y) > 0 else 0 # Return last element or 0 if empty
            model = LinearRegression().fit(X, y)
            next_x = np.array([[len(y)]])
            return float(model.predict(next_x)[0])
        temp_pred = forecast(self.t_data)
        hum_pred = forecast(self.h_data)
        moist_pred = forecast(self.m_data)
        msg = (f"Forecasted next values:\n"
               f"Temperature: {temp_pred:.2f} °C\n"
               f"Humidity: {hum_pred:.2f} %\n"
               f"Moisture: {moist_pred:.2f}")
        QtWidgets.QMessageBox.information(self, "Forecast Result", msg)