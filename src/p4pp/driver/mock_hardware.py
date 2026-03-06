import logging
import queue
import random
import threading
import time
from .protocol import Command

logger = logging.getLogger(__name__)


class MockHardware:
    """
    Simulates firmware responses using the same serial strings as p4pp_firmware.ino.
    """

    def __init__(self):
        self._rx_queue = queue.Queue()
        self._running = False
        self._mock_thread = None
        self.is_open = False
        self.port = "COM_MOCK"
        self.pos_lin = 0
        self.pos_rot = 0

    def connect(self) -> bool:
        self.is_open = True
        self._running = True
        self._mock_thread = threading.Thread(target=self._mock_loop, daemon=True)
        self._mock_thread.start()
        logger.info("Mock Hardware Connected.")
        return True

    def disconnect(self):
        self._running = False
        self.is_open = False
        if self._mock_thread and self._mock_thread.is_alive():
            self._mock_thread.join(1.0)
        logger.info("Mock Hardware Disconnected.")

    def send_command(self, command: str):
        cmd = command.strip()
        logger.debug("[MOCK] TX: %s", cmd)

        if cmd.startswith(Command.MEASURE_N):
            try:
                n = int(cmd.split(" ", 1)[1])
            except (IndexError, ValueError):
                n = 5
            n = max(1, min(n, 20))
            base_rs = 4.532 * (((124.8020 - (-124.2060)) / 2.0) / ((0.8234 + 0.8181) / 2.0))
            delay = 0.1
            self._queue_delayed_response(f"--- Multi-Cycle Measurement (N={n}) ---", delay)
            rs_vals = []
            for i in range(n):
                rs = base_rs + random.uniform(-0.3, 0.3)
                rs_vals.append(rs)
                delay += 0.15
                self._queue_delayed_response(f"CYCLE:{i+1} Rs:{rs:.4f}", delay)
            avg = sum(rs_vals) / len(rs_vals)
            std = (sum((r - avg)**2 for r in rs_vals) / max(len(rs_vals) - 1, 1)) ** 0.5
            delay += 0.1
            self._queue_delayed_response(f"AVG:{avg:.4f} STD:{std:.4f}", delay)
            delay += 0.05
            self._queue_delayed_response(f"Raw R_sheet: {avg:.4f} Ohm/sq", delay)
            delay += 0.05
            self._queue_delayed_response("OK MEASURE_COMPLETE", delay)
            return

        if cmd == Command.MEASURE:
            self._queue_delayed_response("--- Delta Cycle Data ---", 0.1)
            self._queue_delayed_response("I_fwd: 0.8234 mA", 0.15)
            self._queue_delayed_response("V_fwd: 124.8020 mV", 0.2)
            self._queue_delayed_response("I_rev: 0.8181 mA", 0.25)
            self._queue_delayed_response("V_rev: -124.2060 mV", 0.3)
            rs = 4.532 * (((124.8020 - (-124.2060)) / 2.0) / ((0.8234 + 0.8181) / 2.0))
            rs += random.uniform(-0.3, 0.3)
            self._queue_delayed_response(f"Raw R_sheet: {rs:.4f} Ohm/sq", 0.45)
            self._queue_delayed_response("OK MEASURE_COMPLETE", 0.6)
            return

        if cmd == Command.HOME_LIN:
            self.pos_lin = 0
            self._queue_delayed_response("HOMING_LIN_START", 0.1)
            self._queue_delayed_response("OK HOMING_LIN_COMPLETE", 1.0)
            return

        if cmd == Command.HOME_ROT:
            self.pos_rot = 0
            self._queue_delayed_response("HOMING_ROT_START", 0.1)
            self._queue_delayed_response("OK HOMING_ROT_COMPLETE", 1.0)
            return

        if cmd.startswith(Command.MOVE_LIN):
            try:
                target = int(cmd.split(" ", 1)[1])
                dist = abs(target - self.pos_lin)
                move_time = max(0.5, min(dist / 5000.0, 2.0))  # 0.5-2s
                self.pos_lin = target
                self._queue_delayed_response(f"POS LIN: {target} ROT: {self.pos_rot}", move_time * 0.5)
                self._queue_delayed_response(f"OK LIN_TARGET: {target}", move_time)
            except Exception:
                self._queue_delayed_response("ERR Invalid MOVE_LIN argument", 0.1)
            return

        if cmd.startswith(Command.MOVE_ROT):
            try:
                target = int(cmd.split(" ", 1)[1])
                dist = abs(target - self.pos_rot)
                move_time = max(0.5, min(dist / 500.0, 2.0))  # 0.5-2s
                self.pos_rot = target
                self._queue_delayed_response(f"POS LIN: {self.pos_lin} ROT: {target}", move_time * 0.5)
                self._queue_delayed_response(f"OK ROT_TARGET: {target}", move_time)
            except Exception:
                self._queue_delayed_response("ERR Invalid MOVE_ROT argument", 0.1)
            return

        if cmd == Command.GET_POS:
            self._queue_delayed_response(f"POS LIN: {self.pos_lin} ROT: {self.pos_rot}", 0.05)
            return

        if cmd == Command.ZERO:
            self.pos_lin = 0
            self.pos_rot = 0
            self._queue_delayed_response("OK ZEROED", 0.05)
            return

        if cmd == Command.STATUS:
            self._queue_delayed_response("OK READY", 0.05)
            return

        self._queue_delayed_response(f"ERR Unknown command: {cmd}", 0.05)

    def _queue_delayed_response(self, response: str, delay: float):
        def task():
            time.sleep(delay)
            self._rx_queue.put(response)
            logger.debug("[MOCK] RX: %s", response)

        threading.Thread(target=task, daemon=True).start()

    def has_data(self) -> bool:
        return not self._rx_queue.empty()

    def get_line(self) -> str:
        try:
            return self._rx_queue.get_nowait()
        except queue.Empty:
            return ""

    def _mock_loop(self):
        while self._running:
            time.sleep(0.1)
