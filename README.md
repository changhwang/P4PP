<div align="center">
  <img src="assets/icon.png" alt="P4PP Logo" width="140" />
  <h1>P4PP</h1>
  <p><b>Precision 4-Point Probe Controller</b></p>
  <p>Windows GUI for operating a 4-point probe system and logging sheet resistance measurements.</p>
</div>

---

## Overview

P4PP is the control application for a custom 4-point probe measurement setup.

It provides:

- motion and hardware control through serial communication
- measurement execution (single or multi-cycle)
- live result visualization
- automatic CSV reporting

Target metric: **Sheet Resistance (Rs, Ohm/sq)**.

## Quick Start (1 Minute)

1. Download latest release: https://github.com/changhwang/P4PP/releases/latest
2. In release assets, download `P4PP.zip`.
3. Extract to a stable folder (example: `C:\Tools\P4PP`).
4. Open extracted `P4PP` folder and run `P4PP.exe`.
5. In the app, select `MOCK` and validate `Connect -> Home -> Measure`.

Important:

- Keep the extracted `P4PP` folder structure as-is.
- Do not move `P4PP.exe` outside the `P4PP` folder.

## Highlights

- Live GUI for connect/home/move/measure workflow
- `MOCK` mode for validation without hardware
- Real-time status + graph updates
- Auto-save per-measurement CSV reports
- History CSV export
- Explicit controller state handling

## Hardware Bring-Up (Real Device)

Before using real hardware:

1. Flash firmware: `firmware/p4pp_firmware/p4pp_firmware.ino`
2. Confirm COM port in Windows Device Manager.
3. Complete wiring and calibration checks in docs below.

Read docs in this order:

1. [4PP Master Guide](docs/4pp_master_guide.md)
2. [Analog Wiring Guide](docs/analog_wiring_guide.md)
3. [Movement Implementation Guide](docs/movement_implementation_guide.md)
4. [App Architecture](docs/app_architecture.md)

## First Real Measurement Checklist

1. Pass full `MOCK` workflow first.
2. Switch to real COM port and connect.
3. Run one low-risk test sample.
4. Confirm graph updates and CSV output in `data/`.

## Troubleshooting

### Serial connection fails

- Recheck COM port in Device Manager.
- Ensure no other application is holding the port.
- Re-test with `MOCK` mode first.

### App does not start (`ModuleNotFoundError: tkinter`)

- Use the official release package (`P4PP.zip`) from Releases.
- If you built locally, use Python 3.11 and rebuild with `P4PP.spec`.

### Build/runtime metadata error (`PackageNotFoundError: p4pp`)

- Build with `main.py` as entry script.
- Use the provided `P4PP.spec`.

### Build instability on mixed Python environments

- Build using a clean Python 3.11 virtual environment.
- Clear `PYTHONPATH` before packaging to avoid external site-package contamination.

---

## Developer Notes

### Repository Structure

```text
P4PP/
|- assets/               # logo/icons
|- data/                 # measurement outputs
|- docs/                 # English docs
|- firmware/             # Arduino firmware
|- src/p4pp/             # application source
|- main.py               # app entry point
|- P4PP.spec             # PyInstaller spec
`- setup.py              # package metadata
```

### Local Run

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python main.py
```

### Build

```powershell
py -3.11 -m venv build_venv
.\build_venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pyserial customtkinter matplotlib Pillow pyinstaller
$env:PYTHONPATH = ""
python -m PyInstaller --noconfirm --clean P4PP.spec
```

Output:

- `dist/P4PP/P4PP.exe`
- optional archive: `dist/P4PP.zip`

## Distribution Policy

- `dist/` is **not tracked** in `main` (ignored by `.gitignore`).
- Binaries are distributed via **GitHub Releases assets**.
- `build/` is temporary and can be deleted safely.

## License

Internal R&D project unless otherwise specified.
Validate safety and calibration before production usage.
