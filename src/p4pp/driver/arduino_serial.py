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

    CONNECT_RETRIES = 3
    CONNECT_RETRY_DELAY_S = 0.75
    POST_OPEN_SETTLE_S = 2.0

    def __init__(self, port, baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self._serial = None
        self._rx_queue = queue.Queue()
        self._thread = None
        self._running = False
        self.last_error = None

    def connect(self) -> bool:
        """Opens the serial port and starts the reader thread."""
        self.disconnect()
        self.last_error = None

        last_exc = None
        for attempt in range(1, self.CONNECT_RETRIES + 1):
            try:
                # exclusive=True helps on Windows when a previous handle is sticky.
                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baud_rate,
                    timeout=1,
                    write_timeout=1,
                    exclusive=True,
                )
                # Nano 33 IoT (native USB CDC) soft-resets on DTR assert at open.
                time.sleep(self.POST_OPEN_SETTLE_S)
                try:
                    self._serial.reset_input_buffer()
                    self._serial.reset_output_buffer()
                except Exception:
                    pass

                self._running = True
                self._thread = threading.Thread(
                    target=self._read_loop, name=f"serial-rx-{self.port}", daemon=True
                )
                self._thread.start()
                logger.info(
                    "Connected to Arduino on %s at %s baud (attempt %s).",
                    self.port,
                    self.baud_rate,
                    attempt,
                )
                return True
            except (serial.SerialException, OSError, ValueError) as e:
                last_exc = e
                self.last_error = str(e)
                logger.warning(
                    "Connect attempt %s/%s to %s failed: %s",
                    attempt,
                    self.CONNECT_RETRIES,
                    self.port,
                    e,
                )
                self._force_close_port()
                if attempt < self.CONNECT_RETRIES:
                    time.sleep(self.CONNECT_RETRY_DELAY_S)

        logger.error("Failed to connect to %s after retries: %s", self.port, last_exc)
        return False

    def disconnect(self):
        """Stops the reader thread and closes the serial port."""
        self._running = False
        thread = self._thread
        self._thread = None
        if thread and thread.is_alive():
            thread.join(timeout=1.0)

        self._force_close_port()
        # Drop any stale RX lines so the next session starts clean.
        while not self._rx_queue.empty():
            try:
                self._rx_queue.get_nowait()
            except queue.Empty:
                break

    def _force_close_port(self):
        ser = self._serial
        self._serial = None
        if ser is None:
            return
        try:
            if ser.is_open:
                try:
                    ser.dtr = False
                except Exception:
                    pass
                ser.close()
                logger.info("Disconnected from %s.", self.port)
        except Exception as e:
            logger.warning("Error while closing %s: %s", self.port, e)

    def send_command(self, command: str):
        """Sends a newline-terminated command to the Arduino."""
        if self._serial and self._serial.is_open:
            # Enforce exactly one newline
            cmd_str = command.strip() + "\n"
            self._serial.write(cmd_str.encode("utf-8"))
            logger.debug("TX: %s", cmd_str.strip())
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
                    line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        logger.debug("RX: %s", line)
                        self._rx_queue.put(line)
                else:
                    time.sleep(0.01)  # Yield to prevent 100% CPU usage
            except serial.SerialException as e:
                logger.error("Serial port error during read: %s", e)
                self._running = False
                break
            except OSError as e:
                logger.error("Serial OS error during read: %s", e)
                self._running = False
                break

        logger.debug("Serial read loop terminated.")
