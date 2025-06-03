# Arduino Environment Monitor

## Overview
The Arduino Environment Monitor is a Python application designed to monitor environmental conditions such as temperature, humidity, and air quality using an Arduino. The application features a user-friendly graphical interface built with PyQt5, allowing users to visualize real-time data and receive watering advice based on the monitored conditions.

## Features
- Real-time monitoring of temperature, humidity, and air quality.
- Interactive graphical interface with auto-scaling plots.
- Customizable serial connection settings.
- Visual indicators for air quality and watering advice.

## Installation
To set up the project, ensure you have Python 3 installed on your system. Then, install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage
1. Connect your Arduino to your computer via USB.
2. Open the application by running the `main.py` file:

```bash
python src/main.py
```

3. Select the appropriate serial port and baud rate from the dropdown menus.
4. Click the "Connect" button to start monitoring the environmental conditions.
5. The application will display real-time data and provide watering advice based on the current conditions.

## File Structure
```
Datalogger
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── gui.py
│   ├── serial_handler.py
│   └── widgets.py
├── requirements.txt
└── README.md
```

## Dependencies
- PyQt5
- PySerial
- PyQtGraph
- NumPy

## License
This project is licensed under the MIT License. See the LICENSE file for more details.