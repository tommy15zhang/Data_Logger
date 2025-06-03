class SerialHandler:
    def __init__(self):
        self.ser = None

    def connect(self, port, baud_rate):
        import serial
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=0.05)
            return True
        except serial.SerialException as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None

    def read_data(self):
        if self.ser and self.ser.is_open:
            line = self.ser.readline().decode("utf-8", "ignore").strip()
            return line
        return None

    def is_connected(self):
        return self.ser is not None and self.ser.is_open