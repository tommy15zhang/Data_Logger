# Arduino Environment Monitor


## Current Progress

- [ ] run a week long reading, and based on the data, give some suggestion to farmer what plants he/she can plant here.
- [x] Different plants have different perferred temperature and humidity. We can fetch a list of plants and let the farmer to choose which plants they want, and place the data logger near the plant. We also provide advice to what to do, like turn on the heater or remove the heater. 
- [ ] Also another interesting mode is to run the arduino for a specific amount of time, and then generate a report in pdf


## Arduino-Host Communication Protocol

Host can send the following command `d` in serial to make arduino into analysis mode, current default is to run weekly data. Once the arduino is finished



Data will be sent from the Arduino to the computer in this format
```cpp
    Serial.print(temp);
    Serial.print(",");
    Serial.print(humidity);
    Serial.print(",");
    Serial.print(quality);
    Serial.print(",");
    Serial.print(tempAverage);
    Serial.print(",");
    Serial.print(humidityAverage);
    Serial.print(",");
    Serial.print(tempTooHigh);
    Serial.print(",");
    Serial.print(tempTooLow);
    Serial.print(",");
    Serial.print(humidityTooLow);
    Serial.print(",");
    Serial.print(humidityTooHigh);
    Serial.print(",");
    Serial.println(airQualityIssue);
```

for quality, it gives a 0,1,2,3 value where

FORCE_SIGNAL   = 0;
HIGH_POLLUTION = 1;
LOW_POLLUTION = 2;
FRESH_AIR = 3;

The first values are actual values and the last 5 will be a flag where it indicates any issue with the current environment

The actual data will look like this

25,67,40,22,50,38,0,0,1,0,1




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
