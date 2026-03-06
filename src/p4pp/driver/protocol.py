class Command:
    """Firmware-native commands sent from PC to Arduino."""
    MEASURE = "MEASURE"
    MEASURE_N = "MEASURE_N"  # Usage: MEASURE_N <cycles> (multi-cycle avg)
    MOVE_LIN = "MOVE_LIN"    # Usage: MOVE_LIN <target> (absolute steps)
    MOVE_ROT = "MOVE_ROT"    # Usage: MOVE_ROT <target> (absolute steps)
    HOME_LIN = "HOME_LIN"
    HOME_ROT = "HOME_ROT"
    GET_POS = "GET_POS"
    ZERO = "ZERO"
    STATUS = "STATUS"


class Response:
    """Key firmware response markers."""
    OK_MEASURE_COMPLETE = "OK MEASURE_COMPLETE"
    OK_HOMING_LIN_COMPLETE = "OK HOMING_LIN_COMPLETE"
    OK_HOMING_ROT_COMPLETE = "OK HOMING_ROT_COMPLETE"
    ERR_PREFIX = "ERR "
    ERROR_PREFIX = "ERROR:"


class State:
    """Internal states of the Python Controller."""
    DISCONNECTED = "DISCONNECTED"
    IDLE = "IDLE"
    MEASURING = "MEASURING"
    MOVING = "MOVING"
    HOMING = "HOMING"
    ERROR = "ERROR"
