import logging
import time
from src.p4pp.driver import P4PPController, State

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def wait_until_idle(controller: P4PPController, timeout_sec: float = 5.0):
    start_t = time.time()
    while controller.state in (State.MEASURING, State.MOVING, State.HOMING):
        controller.tick()
        time.sleep(0.05)
        if time.time() - start_t > timeout_sec:
            raise TimeoutError(f"Timed out waiting for IDLE. state={controller.state}")


def run_test():
    print("=== Starting P4PP Driver Mock Test (Firmware Protocol) ===")
    controller = P4PPController(mock=True)

    if not controller.connect():
        raise RuntimeError("Failed to connect mock controller")
    print(f"Connected. state={controller.state}")

    controller.home_linear()
    wait_until_idle(controller)
    print(f"HOME_LIN done. pos_lin={controller.pos_lin}")

    controller.home_rotational()
    wait_until_idle(controller)
    print(f"HOME_ROT done. pos_rot={controller.pos_rot}")

    controller.move_linear(1200, relative=False)
    wait_until_idle(controller)
    print(f"MOVE_LIN done. pos_lin={controller.pos_lin}")

    controller.move_rotational(180, relative=False)
    wait_until_idle(controller)
    print(f"MOVE_ROT done. pos_rot={controller.pos_rot}")

    controller.measure()
    wait_until_idle(controller)
    print(f"MEASURE done. latest_result={controller.latest_result}")

    controller.disconnect()
    print("=== Test Complete ===")


if __name__ == "__main__":
    run_test()
