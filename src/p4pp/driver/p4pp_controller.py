import logging
import re
import time
from typing import Optional
from collections import deque
from .protocol import Command, Response, State
from .arduino_serial import ArduinoSerial
from .mock_hardware import MockHardware

logger = logging.getLogger(__name__)


class P4PPController:
    """
    High-level API for P4PP hardware.
    GUI should interact with this class only.
    """

    POS_PATTERN = re.compile(r"^POS LIN:\s*(-?\d+)\s+ROT:\s*(-?\d+)$")
    RS_PATTERN = re.compile(r"Raw R_sheet:\s*(-?\d+(?:\.\d+)?)")
    CYCLE_PATTERN = re.compile(r"^CYCLE:(\d+)\s+Rs:(-?\d+(?:\.\d+)?)$")
    AVG_STD_PATTERN = re.compile(r"^AVG:(-?\d+(?:\.\d+)?)\s+STD:(-?\d+(?:\.\d+)?)$")
    LIN_TARGET_PATTERN = re.compile(r"^OK LIN_TARGET:\s*(-?\d+)$")
    ROT_TARGET_PATTERN = re.compile(r"^OK ROT_TARGET:\s*(-?\d+)$")
    LIN_STEPS_PER_MM = 200.0
    ROT_STEPS_PER_DEG = 4.444444
    LIN_MIN_STEPS = 0
    LIN_MAX_STEPS = 10000
    ROT_MIN_STEPS = 0
    ROT_MAX_STEPS = 1250

    def __init__(self, port: str = "COM3", mock: bool = False):
        self.mock_mode = mock
        self.hw = MockHardware() if self.mock_mode else ArduinoSerial(port=port)
        self.state = State.DISCONNECTED
        self.latest_result = None
        self.latest_std = None
        self.latest_raw_result = None
        self.cycle_results = []
        self.correction_factor = 1.0

        self.has_homed_lin = False
        self.has_homed_rot = False
        self.pos_lin = 0
        self.pos_rot = 0
        self.target_lin: Optional[int] = None
        self.target_rot: Optional[int] = None
        self.active_task = None
        self._recent_lines = deque(maxlen=500)
        self._last_pos_line = None
        self._last_pos_query_at = 0.0

        mode_name = "MOCK" if self.mock_mode else f"HW({port})"
        logger.info("Initialized P4PP Controller in %s mode.", mode_name)

    def connect(self) -> bool:
        if self.hw.connect():
            self.state = State.IDLE
            self.hw.send_command(Command.GET_POS)
            self._last_pos_query_at = time.monotonic()
            return True
        self.state = State.ERROR
        return False

    def disconnect(self):
        self.hw.disconnect()
        self.state = State.DISCONNECTED

    def tick(self):
        """
        Called periodically by GUI to process inbound serial lines.
        """
        while self.hw.has_data():
            line = self.hw.get_line()
            self._process_line(line)

        # Keep position view fresh while idle.
        now = time.monotonic()
        if self.state == State.IDLE and (now - self._last_pos_query_at) > 0.5:
            self.hw.send_command(Command.GET_POS)
            self._last_pos_query_at = now

    def _process_line(self, line: str):
        if not line:
            return

        should_log = True
        if line.startswith("POS LIN:"):
            # Status polling can emit many identical position lines.
            # Keep parsing every line, but suppress unchanged duplicates in UI logs.
            if line == self._last_pos_line:
                should_log = False
            else:
                self._last_pos_line = line

        if should_log:
            self._recent_lines.append(line)
        logger.debug("RX: %s", line)

        if line == Response.OK_HOMING_LIN_COMPLETE:
            self.has_homed_lin = True
            self.pos_lin = 0
            self.active_task = None
            self.state = State.IDLE
            return

        if line == Response.OK_HOMING_ROT_COMPLETE:
            self.has_homed_rot = True
            self.pos_rot = 0
            self.active_task = None
            self.state = State.IDLE
            return

        if line == Response.OK_MEASURE_COMPLETE:
            self.active_task = None
            self.state = State.IDLE
            return

        rs_match = self.RS_PATTERN.search(line)
        if rs_match:
            try:
                raw_rs = float(rs_match.group(1))
                self.latest_raw_result = raw_rs
                self.latest_result = raw_rs * self.correction_factor
            except ValueError:
                logger.error("Failed to parse Raw R_sheet from: %s", line)
            return

        cycle_match = self.CYCLE_PATTERN.match(line)
        if cycle_match:
            try:
                self.cycle_results.append(float(cycle_match.group(2)))
            except ValueError:
                pass
            return

        avg_std_match = self.AVG_STD_PATTERN.match(line)
        if avg_std_match:
            try:
                raw_avg = float(avg_std_match.group(1))
                self.latest_std = float(avg_std_match.group(2)) * self.correction_factor
                self.latest_raw_result = raw_avg
                self.latest_result = raw_avg * self.correction_factor
            except ValueError:
                logger.error("Failed to parse AVG/STD from: %s", line)
            return

        pos_match = self.POS_PATTERN.match(line)
        if pos_match:
            self.pos_lin = int(pos_match.group(1))
            self.pos_rot = int(pos_match.group(2))
            
            if self.state == State.MOVING:
                if self.active_task == Command.MOVE_LIN and self.target_lin is not None:
                    if self.pos_lin == self.target_lin:
                        self.active_task = None
                        self.state = State.IDLE
                        self.target_lin = None
                elif self.active_task == Command.MOVE_ROT and self.target_rot is not None:
                    if self.pos_rot == self.target_rot:
                        self.active_task = None
                        self.state = State.IDLE
                        self.target_rot = None
            return

        lin_target_match = self.LIN_TARGET_PATTERN.match(line)
        if lin_target_match:
            self.target_lin = int(lin_target_match.group(1))
            if self.pos_lin == self.target_lin:
                self.active_task = None
                self.state = State.IDLE
                self.target_lin = None
            return

        rot_target_match = self.ROT_TARGET_PATTERN.match(line)
        if rot_target_match:
            self.target_rot = int(rot_target_match.group(1))
            if self.pos_rot == self.target_rot:
                self.active_task = None
                self.state = State.IDLE
                self.target_rot = None
            return

        if line.startswith(Response.ERR_PREFIX) or line.startswith(Response.ERROR_PREFIX):
            logger.error("Arduino Error: %s", line)
            self.active_task = None
            self.state = State.ERROR
            return

        # Informational lines from firmware during measurement/homing are expected.
        if line.startswith("HOMING_") or line.startswith("OK ") or line.startswith("---"):
            return

    def measure(self, cycles: int = 1) -> bool:
        if self.state != State.IDLE:
            return False
        self.state = State.MEASURING
        self.active_task = Command.MEASURE
        self.latest_result = None
        self.latest_std = None
        self.latest_raw_result = None
        self.cycle_results = []
        if cycles > 1:
            self.hw.send_command(f"{Command.MEASURE_N} {cycles}")
        else:
            self.hw.send_command(Command.MEASURE)
        return True

    def home_linear(self) -> bool:
        if self.state != State.IDLE:
            return False
        self.state = State.HOMING
        self.active_task = Command.HOME_LIN
        self.hw.send_command(Command.HOME_LIN)
        return True

    def home_rotational(self) -> bool:
        if self.state != State.IDLE:
            return False
        self.state = State.HOMING
        self.active_task = Command.HOME_ROT
        self.hw.send_command(Command.HOME_ROT)
        return True

    def move_linear(self, target_steps: int, relative: bool = False) -> bool:
        if self.state != State.IDLE:
            return False
        if not self.has_homed_lin and not self.mock_mode:
            logger.warning("Linear move blocked: HOME_LIN required first.")
            return False

        final_target = self.pos_lin + target_steps if relative else target_steps
        if final_target < self.LIN_MIN_STEPS or final_target > self.LIN_MAX_STEPS:
            logger.warning(
                "Linear move blocked by limit: target=%s, allowed=[%s, %s]",
                final_target,
                self.LIN_MIN_STEPS,
                self.LIN_MAX_STEPS,
            )
            return False
        self.state = State.MOVING
        self.active_task = Command.MOVE_LIN
        self.hw.send_command(f"{Command.MOVE_LIN} {final_target}")
        return True

    def move_rotational(self, target_steps: int, relative: bool = False) -> bool:
        if self.state != State.IDLE:
            return False
        if not self.has_homed_rot and not self.mock_mode:
            logger.warning("Rotation move blocked: HOME_ROT required first.")
            return False

        final_target = self.pos_rot + target_steps if relative else target_steps
        if final_target < self.ROT_MIN_STEPS or final_target > self.ROT_MAX_STEPS:
            logger.warning(
                "Rotation move blocked by limit: target=%s, allowed=[%s, %s]",
                final_target,
                self.ROT_MIN_STEPS,
                self.ROT_MAX_STEPS,
            )
            return False
        self.state = State.MOVING
        self.active_task = Command.MOVE_ROT
        self.hw.send_command(f"{Command.MOVE_ROT} {final_target}")
        return True

    @classmethod
    def lin_steps_to_mm(cls, steps: int) -> float:
        return steps / cls.LIN_STEPS_PER_MM

    @classmethod
    def rot_steps_to_deg(cls, steps: int) -> float:
        return steps / cls.ROT_STEPS_PER_DEG

    @classmethod
    def mm_to_lin_steps(cls, mm: float) -> int:
        return int(round(mm * cls.LIN_STEPS_PER_MM))

    @classmethod
    def deg_to_rot_steps(cls, deg: float) -> int:
        return int(round(deg * cls.ROT_STEPS_PER_DEG))

    def drain_recent_lines(self):
        lines = list(self._recent_lines)
        self._recent_lines.clear()
        return lines
