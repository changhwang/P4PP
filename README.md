<div align="center">
  <img src="assets/icon.png" alt="P4PP Logo" width="140" />
  <h1>P4PP</h1>
  <p><b>Precision 4-Point Probe Controller</b></p>
  <p>
    Desktop software for controlling a 4-point probe measurement rig,
    automating motion + measurement cycles, and generating structured Rs data.
  </p>
</div>

---

## Overview

**P4PP** is an integrated software stack for a 4-point probe (4PP) system used to measure **sheet resistance (Rs, Ohm/sq)** on ITO and thin-film samples.

It combines:

- A desktop GUI for hardware control and operator workflow
- A controller state machine that maps UI actions to firmware commands
- Serial transport for Arduino-based device communication
- Measurement visualization and CSV reporting

If you need a complete software + firmware workflow for a custom 4PP bench setup, this repository is the operational layer.

## What This Project Does

- Connects to the P4PP hardware controller over serial (`COMx`)
- Supports homing and movement control for linear/rotational axes
- Runs single or multi-cycle resistance measurements
- Parses firmware responses into structured app state
- Displays live measurement history graph
- Saves:
  - per-measurement detailed CSV reports
  - full history CSV exports

## Key Features

- Hardware mode and `MOCK` mode (for UI/protocol verification without device)
- Explicit runtime state machine:
  - `DISCONNECTED`, `IDLE`, `MEASURING`, `MOVING`, `HOMING`, `ERROR`
- Safety gate for movement logic (rotation blocking under unsafe linear position)
- PyInstaller-based Windows packaging (`P4PP.exe`)

## Repository Structure

```text
P4PP/
├─ assets/                           # App icon and static assets
├─ data/                             # Measurement outputs / exported CSVs
├─ dist/                             # Built distribution artifacts
├─ docs/                             # Hardware and architecture docs (EN)
├─ firmware/                         # Arduino firmware source
├─ planning/                         # BOM and planning materials
├─ src/
│  └─ p4pp/
│     ├─ driver/
│     │  ├─ p4pp_controller.py       # Core state machine/controller
│     │  ├─ arduino_serial.py        # Serial transport abstraction
│     │  ├─ mock_hardware.py         # Mock transport implementation
│     │  └─ protocol.py              # Command/response definitions
│     └─ gui/
│        ├─ app.py                   # Main GUI application
│        └─ components/              # UI panels/components
├─ main.py                           # Runtime entry point
├─ setup.py                          # Python package metadata
└─ P4PP.spec                         # PyInstaller spec for distribution build
```

## Setup Guide (Recommended Path)

### 1) Environment

- OS: Windows 10/11
- Python: **3.12 recommended**
- Shell: PowerShell

Create and activate virtual environment:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install project in editable mode:

```powershell
pip install -e .
```

### 2) Run the App

```powershell
python main.py
```

or

```powershell
p4pp-gui
```

### 3) First Validation (Without Hardware)

1. Launch app
2. Select `MOCK` in port dropdown
3. Connect
4. Run homing/move/measure actions
5. Confirm graph updates and CSV output flow

This verifies UI + controller + parsing path before touching hardware.

---

## Hardware/Firmware Bring-up Order

For a clean setup, read and execute in this order:

1. `docs/4pp_master_guide.md`
2. `docs/analog_wiring_guide.md`
3. `docs/movement_implementation_guide.md`
4. `docs/app_architecture.md`

Then flash firmware from:

- `firmware/p4pp_firmware/p4pp_firmware.ino`

## Command/Response Contract (Summary)

App -> Firmware examples:

- `MEASURE`
- `HOME_LIN`, `HOME_ROT`
- `MOVE_LIN <target_steps>`, `MOVE_ROT <target_steps>`
- `GET_POS`, `STATUS`, `ZERO`

Firmware -> App examples:

- `POS LIN: <n> ROT: <n>`
- `Raw R_sheet: <float> Ohm/sq`
- `OK MEASURE_COMPLETE`
- `OK HOMING_LIN_COMPLETE`, `OK HOMING_ROT_COMPLETE`
- `ERR ...` / `ERROR: ...`

Detailed behavior is documented in `docs/app_architecture.md`.

---

## Build Distribution (Windows)

> `build/` is temporary and safe to delete. PyInstaller recreates it automatically.

### Clean build environment

```powershell
py -3.12 -m venv build_venv
.\build_venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pyserial customtkinter matplotlib Pillow pyinstaller
```

### Build

```powershell
python -m PyInstaller --noconfirm --clean P4PP.spec
```

### Outputs

- `dist/P4PP/P4PP.exe`
- optional packaged zip: `dist/P4PP.zip`

## Troubleshooting

### `PackageNotFoundError: No package metadata was found for p4pp`

Cause:
- Building from `venv\Scripts\p4pp-gui-script.py` as entry script

Fix:
- Use `main.py` as the PyInstaller entry script (already configured in `P4PP.spec`)

### PyInstaller analysis/build instability on Python 3.10

Fix:
- Build using Python 3.12 venv

### Serial connection fails

- Verify COM port in Device Manager
- Ensure no other app holds the same port
- Validate full workflow with `MOCK` first

---

## Current Status

- Runtime executable naming standardized to `P4PP`
- Distribution naming standardized to `P4PP`
- Build spec updated for stable packaging

## License

Internal R&D project unless otherwise specified.
Validate safety, calibration, and measurement consistency before external deployment.
