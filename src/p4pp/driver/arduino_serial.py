import serial
import threading
import queue
import time
import logging

logger = logging.getLogger(__name__)

class ArduinoSerial:
    """
    Low-level serial wrapper that continuously reads from the Arduino
    in a background thread to prevent UI freezing.
    """
    def __init__(self, port, baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self._serial = None
        self._rx_queue = queue.Queue()
        self._thread = None
        self._running = False
        
    def connect(self) -> bool:
        """Opens the serial port and starts the reader thread."""
        try:
            self._serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset upon connection
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            logger.info(f"Connected to Arduino on {self.port} at {self.baud_rate} baud.")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self):
        """Stops the reader thread and closes the serial port."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info(f"Disconnected from {self.port}.")

    def send_command(self, command: str):
        """Sends a newline-terminated command to the Arduino."""
        if self._serial and self._serial.is_open:
            # Enforce exactly one newline
            cmd_str = command.strip() + '\n'
            self._serial.write(cmd_str.encode('utf-8'))
            logger.debug(f"TX: {cmd_str.strip()}")
        else:
            logger.warning("Attempted to send command, but serial is not connected.")

    def has_data(self) -> bool:
        """Returns True if there is unread data in the queue."""
        return not self._rx_queue.empty()

    def get_line(self) -> str:
        """Gets a line from the queue if available, otherwise returns empty string."""
        try:
            return self._rx_queue.get_nowait()
        except queue.Empty:
            return ""

    def _read_loop(self):
        """Background thread operation that constantly fills the RX queue."""
        while self._running and self._serial and self._serial.is_open:
            try:
                if self._serial.in_waiting > 0:
                    line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        logger.debug(f"RX: {line}")
                        self._rx_queue.put(line)
                else:
                    time.sleep(0.01)  # Yield to prevent 100% CPU usage
            except serial.SerialException as e:
                logger.error(f"Serial port error during read: {e}")
                self._running = False
                break
        
        logger.debug("Serial read loop terminated.")
