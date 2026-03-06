import re
import os
import serial.tools.list_ports
import customtkinter as ctk
from tkinter import filedialog
from src.p4pp.driver import P4PPController

_DEFAULT_SAVE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "measurements"))


class ControlPanel(ctk.CTkFrame):
    """Actuator-only control panel (connection section moved to top bar)."""

    def __init__(
        self,
        master,
        initialize_callback,
        measure_callback,
        move_lin_abs_callback,
        move_lin_rel_callback,
        move_rot_abs_callback,
        move_rot_rel_callback,
        home_lin_callback,
        home_rot_callback,
    ):
        super().__init__(master)

        self.measure_callback = measure_callback
        self.initialize_callback = initialize_callback
        self.move_lin_abs_callback = move_lin_abs_callback
        self.move_lin_rel_callback = move_lin_rel_callback
        self.move_rot_abs_callback = move_rot_abs_callback
        self.move_rot_rel_callback = move_rot_rel_callback
        self.home_lin_callback = home_lin_callback
        self.home_rot_callback = home_rot_callback

        self.grid_columnconfigure(0, weight=1)

        # --- Action Buttons ---
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        self.btn_initialize = ctk.CTkButton(
            action_frame, text="Initialize", height=40,
            command=self.on_initialize, fg_color="#1F538D",
        )
        self.btn_initialize.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.btn_measure = ctk.CTkButton(
            action_frame, text="Measure", height=40,
            command=self.on_measure, fg_color="#A31C2D", hover_color="#7A1321",
        )
        self.btn_measure.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # --- Sample Name + Save Path ---
        sample_frame = ctk.CTkFrame(self, fg_color="transparent")
        sample_frame.grid(row=1, column=0, padx=12, pady=(4, 2), sticky="ew")
        sample_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(sample_frame, text="Sample:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=(0, 4), sticky="w")
        self.sample_var = ctk.StringVar(value="untitled")
        self.entry_sample = ctk.CTkEntry(sample_frame, textvariable=self.sample_var, height=28)
        self.entry_sample.grid(row=0, column=1, sticky="ew")

        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.grid(row=2, column=0, padx=12, pady=(2, 6), sticky="ew")
        path_frame.grid_columnconfigure(0, weight=1)
        self.save_dir = _DEFAULT_SAVE_DIR
        self.lbl_save_path = ctk.CTkLabel(
            path_frame, text=self._shorten_path(self.save_dir),
            font=ctk.CTkFont(size=11), text_color="#9CB5D9", anchor="w",
        )
        self.lbl_save_path.grid(row=0, column=0, sticky="ew")
        self.btn_browse = ctk.CTkButton(
            path_frame, text="📁", width=32, height=28, command=self._browse_save_dir,
        )
        self.btn_browse.grid(row=0, column=1, padx=(4, 0))

        # --- Actuator Control ---
        ctk.CTkLabel(
            self, text="Actuator Control",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=3, column=0, padx=12, pady=(8, 4))

        self._build_linear_section(row=4)
        self._build_rotation_section(row=5)

    # ------------------------------------------------------------------ Linear
    def _build_linear_section(self, row: int):
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, padx=12, pady=4, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Linear (mm)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        self.btn_home_lin = ctk.CTkButton(header, text="HOME", width=60, height=28, command=self.on_home_lin)
        self.btn_home_lin.grid(row=0, column=1, sticky="e")

        abs_row = ctk.CTkFrame(frame, fg_color="transparent")
        abs_row.grid(row=1, column=0, padx=10, pady=3, sticky="ew")
        abs_row.grid_columnconfigure(0, weight=1)
        self.entry_lin_abs = ctk.CTkEntry(abs_row, placeholder_text="Abs target (mm)", height=28)
        self.entry_lin_abs.grid(row=0, column=0, sticky="ew")
        self.btn_move_lin_abs = ctk.CTkButton(abs_row, text="Go", width=50, height=28, command=self.on_move_lin_abs)
        self.btn_move_lin_abs.grid(row=0, column=1, padx=(6, 0))

        rel_row = ctk.CTkFrame(frame, fg_color="transparent")
        rel_row.grid(row=2, column=0, padx=10, pady=3, sticky="ew")
        rel_row.grid_columnconfigure(1, weight=1)
        self.btn_lin_left = ctk.CTkButton(rel_row, text="<", width=36, height=28, command=self.on_move_lin_rel_neg)
        self.btn_lin_left.grid(row=0, column=0)
        self.entry_lin_rel = ctk.CTkEntry(rel_row, placeholder_text="Rel delta (mm)", height=28)
        self.entry_lin_rel.grid(row=0, column=1, padx=6, sticky="ew")
        self.btn_lin_right = ctk.CTkButton(rel_row, text=">", width=36, height=28, command=self.on_move_lin_rel_pos)
        self.btn_lin_right.grid(row=0, column=2)

        lin_limit_mm = P4PPController.lin_steps_to_mm(P4PPController.LIN_MAX_STEPS)
        ctk.CTkLabel(
            frame, text=f"Range: 0 ~ {lin_limit_mm:.1f} mm  |  Sample: 46.0 mm",
            text_color="#A0A0A0", font=ctk.CTkFont(size=11),
        ).grid(row=3, column=0, padx=10, pady=(2, 8), sticky="w")

    # --------------------------------------------------------------- Rotation
    def _build_rotation_section(self, row: int):
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, padx=12, pady=4, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Rotation (deg)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        self.btn_home_rot = ctk.CTkButton(header, text="HOME", width=60, height=28, command=self.on_home_rot)
        self.btn_home_rot.grid(row=0, column=1, sticky="e")

        abs_row = ctk.CTkFrame(frame, fg_color="transparent")
        abs_row.grid(row=1, column=0, padx=10, pady=3, sticky="ew")
        abs_row.grid_columnconfigure(0, weight=1)
        self.entry_rot_abs = ctk.CTkEntry(abs_row, placeholder_text="Abs target (deg)", height=28)
        self.entry_rot_abs.grid(row=0, column=0, sticky="ew")
        self.btn_move_rot_abs = ctk.CTkButton(abs_row, text="Go", width=50, height=28, command=self.on_move_rot_abs)
        self.btn_move_rot_abs.grid(row=0, column=1, padx=(6, 0))

        rel_row = ctk.CTkFrame(frame, fg_color="transparent")
        rel_row.grid(row=2, column=0, padx=10, pady=3, sticky="ew")
        rel_row.grid_columnconfigure(1, weight=1)
        self.btn_rot_left = ctk.CTkButton(rel_row, text="<", width=36, height=28, command=self.on_move_rot_rel_neg)
        self.btn_rot_left.grid(row=0, column=0)
        self.entry_rot_rel = ctk.CTkEntry(rel_row, placeholder_text="Rel delta (deg)", height=28)
        self.entry_rot_rel.grid(row=0, column=1, padx=6, sticky="ew")
        self.btn_rot_right = ctk.CTkButton(rel_row, text=">", width=36, height=28, command=self.on_move_rot_rel_pos)
        self.btn_rot_right.grid(row=0, column=2)

        rot_limit_deg = P4PPController.rot_steps_to_deg(P4PPController.ROT_MAX_STEPS)
        ctk.CTkLabel(
            frame, text=f"Range: 0 ~ {rot_limit_deg:.1f} deg",
            text_color="#A0A0A0", font=ctk.CTkFont(size=11),
        ).grid(row=3, column=0, padx=10, pady=(2, 8), sticky="w")

    # ---------------------------------------------------------------- Handlers
    def on_initialize(self):
        self.initialize_callback()

    def on_measure(self):
        self.measure_callback()

    def on_home_lin(self):
        self.home_lin_callback()

    def on_home_rot(self):
        self.home_rot_callback()

    def on_move_lin_abs(self):
        value = self._read_float(self.entry_lin_abs)
        if value is not None:
            self.move_lin_abs_callback(value)

    def on_move_lin_rel_neg(self):
        value = self._read_float(self.entry_lin_rel)
        if value is not None:
            self.move_lin_rel_callback(value, -1)

    def on_move_lin_rel_pos(self):
        value = self._read_float(self.entry_lin_rel)
        if value is not None:
            self.move_lin_rel_callback(value, 1)

    def on_move_rot_abs(self):
        value = self._read_float(self.entry_rot_abs)
        if value is not None:
            self.move_rot_abs_callback(value)

    def on_move_rot_rel_neg(self):
        value = self._read_float(self.entry_rot_rel)
        if value is not None:
            self.move_rot_rel_callback(value, -1)

    def on_move_rot_rel_pos(self):
        value = self._read_float(self.entry_rot_rel)
        if value is not None:
            self.move_rot_rel_callback(value, 1)

    @staticmethod
    def _read_float(entry: ctk.CTkEntry):
        raw = entry.get().strip()
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    @staticmethod
    def _get_ports():
        devices = [port.device for port in serial.tools.list_ports.comports()]
        devices = sorted(set(devices), key=ControlPanel._port_sort_key)
        return ["MOCK"] + devices

    @staticmethod
    def _port_sort_key(port_name: str):
        match = re.match(r"^COM(\d+)$", port_name.upper())
        if match:
            return (0, int(match.group(1)))
        return (1, port_name.upper())

    def refresh_ports(self):
        """Called externally to refresh the port list in the top bar."""
        pass  # Port combo is now in app.py top bar

    def _browse_save_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.save_dir, title="Select save folder")
        if chosen:
            self.save_dir = chosen
            self.lbl_save_path.configure(text=self._shorten_path(chosen))

    @staticmethod
    def _shorten_path(path: str, max_len: int = 35) -> str:
        if len(path) <= max_len:
            return path
        parts = path.replace("\\", "/").split("/")
        return ".../" + "/".join(parts[-2:])

    def get_sample_name(self) -> str:
        name = self.sample_var.get().strip()
        return name if name else "untitled"

    def get_save_dir(self) -> str:
        return self.save_dir

    def set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for widget in [
            self.btn_measure,
            self.btn_initialize,
            self.btn_home_lin,
            self.btn_home_rot,
            self.btn_move_lin_abs,
            self.btn_move_rot_abs,
            self.btn_lin_left,
            self.btn_lin_right,
            self.btn_rot_left,
            self.btn_rot_right,
            self.entry_lin_abs,
            self.entry_lin_rel,
            self.entry_rot_abs,
            self.entry_rot_rel,
        ]:
            widget.configure(state=state)
