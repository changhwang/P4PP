# P4PP App Architecture (Firmware-First)

## Goal
- Use `firmware/p4pp_firmware/p4pp_firmware.ino` as the single source of truth.
- Ensure GUI behavior follows firmware command/response timing and strings exactly.

## Layered Structure
1. `GUI` (`src/p4pp/gui`)
- Renders controls, status, result trend.
- Calls high-level controller methods only.
- Does not parse serial text directly.

2. `Controller` (`src/p4pp/driver/p4pp_controller.py`)
- Owns state machine: `DISCONNECTED`, `IDLE`, `MEASURING`, `MOVING`, `HOMING`, `ERROR`.
- Converts UI actions into firmware commands.
- Parses raw serial lines into state/result/position updates.

3. `Transport` (`src/p4pp/driver/arduino_serial.py`)
- Handles serial connection and background RX thread.
- Provides non-blocking queue interface to controller.

4. `Firmware` (`firmware/p4pp_firmware/p4pp_firmware.ino`)
- Executes device commands and prints canonical response lines.

## Contract (App -> Firmware)
- `MEASURE`
- `HOME_LIN`
- `HOME_ROT`
- `MOVE_LIN <target_steps>`
- `MOVE_ROT <target_steps>`
- `GET_POS`
- `ZERO`
- `STATUS`

## Contract (Firmware -> App)
- Homing complete: `OK HOMING_LIN_COMPLETE`, `OK HOMING_ROT_COMPLETE`
- Move accepted: `OK LIN_TARGET: <n>`, `OK ROT_TARGET: <n>`
- Position: `POS LIN: <n> ROT: <n>`
- Measurement value source: `Raw R_sheet: <float> Ohm/sq`
- Measurement done: `OK MEASURE_COMPLETE`
- Errors: `ERR ...` or `ERROR: ...`

## State Transitions
- `connect()` success -> `IDLE`
- `measure()` -> `MEASURING` -> `IDLE` when `OK MEASURE_COMPLETE`
- `home_*()` -> `HOMING` -> `IDLE` when homing complete marker arrives
- `move_*()` -> `MOVING` -> `IDLE` when `OK *_TARGET` arrives
- Any `ERR`/`ERROR:` while active -> `ERROR`

## UI Behavior Rules
- Disable action buttons while in `MEASURING`/`MOVING`/`HOMING`.
- Re-enable in `IDLE` and `ERROR`.
- Always show latest `LIN/ROT` positions from parsed `POS` lines.
- Append graph point only when measurement cycle returns to `IDLE`.

## Test Strategy
- `MockHardware` must emit firmware-like lines, not synthetic protocol variants.
- `test_driver.py` validates:
  - connect/home/move/measure full loop
  - state returns to `IDLE`
  - measurement result is parsed from `Raw R_sheet`.
