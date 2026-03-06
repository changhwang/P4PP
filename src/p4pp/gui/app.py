import re
import os
import csv
from datetime import datetime
import customtkinter as ctk
import serial.tools.list_ports
from PIL import Image
from src.p4pp.driver import P4PPController, State
from src.p4pp.gui.components.control_panel import ControlPanel
from src.p4pp.gui.components.status_panel import StatusPanel
from src.p4pp.gui.components.graph_panel import GraphPanel
from src.p4pp.gui.components.serial_log_panel import SerialLogPanel
from src.p4pp.gui.components.measurement_settings_panel import MeasurementSettingsPanel
import logging

logger = logging.getLogger(__name__)

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets")


class P4PPApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup Window
        self.title("P4PP - Precision 4-Point Probe Controller")
        self.geometry("1320x860")
        self.minsize(1100, 700)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # App Icon — Windows needs both iconbitmap (taskbar) and iconphoto (title bar)
        ico_path = os.path.join(_ASSETS_DIR, "P4PP_icon.ico")
        png_path = os.path.join(_ASSETS_DIR, "icon.png")
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("p4pp.controller.v1")
        except Exception:
            pass
        if os.path.exists(ico_path):
            self.iconbitmap(ico_path)
        if os.path.exists(png_path):
            from PIL import ImageTk
            icon_img = Image.open(png_path).convert("RGBA")
            self._icon_photos = []
            for size in [256, 128, 64, 48, 32, 16]:
                resized = icon_img.resize((size, size), Image.LANCZOS)
                photo = ImageTk.PhotoImage(resized)
                self._icon_photos.append(photo)
            self.iconphoto(True, *self._icon_photos)

        # Grid: row 0 = top bar, row 1 = main area (expandable)
        self.grid_columnconfigure(0, weight=0)  # left column (fixed)
        self.grid_columnconfigure(1, weight=1)  # right column (expand)
        self.grid_rowconfigure(0, weight=0)      # top bar
        self.grid_rowconfigure(1, weight=1)      # main area

        # Hardware Controller (starts disconnected)
        self.controller = None
        self.last_state = State.DISCONNECTED
        self.last_result_displayed = None
        self.init_sequence_active = False
        self.init_phase = None

        # =====================================================================
        # TOP BAR: Connection + Status (spans both columns)
        # =====================================================================
        self.top_bar = ctk.CTkFrame(self)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))
        self.top_bar.grid_columnconfigure(2, weight=1)  # status label expands

        # -- Connection section (left side of top bar) --
        ctk.CTkLabel(
            self.top_bar, text="P4PP",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=(16, 12), pady=10)

        conn_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        conn_frame.grid(row=0, column=1, pady=8)

        ports = self._get_ports()
        self.port_var = ctk.StringVar(value=ports[0])
        self.combo_port = ctk.CTkComboBox(
            conn_frame, values=ports, variable=self.port_var, width=140, height=32,
        )
        self.combo_port.grid(row=0, column=0, padx=(0, 4))

        self.btn_refresh = ctk.CTkButton(
            conn_frame, text="⟳", width=32, height=32, command=self._refresh_ports,
        )
        self.btn_refresh.grid(row=0, column=1, padx=(0, 4))

        self.btn_connect = ctk.CTkButton(
            conn_frame, text="Connect", width=100, height=32,
            command=self.cmd_connect, fg_color="#1F538D",
        )
        self.btn_connect.grid(row=0, column=2)

        # -- Status section (right side of top bar) --
        self.status_panel = StatusPanel(self.top_bar)
        self.status_panel.grid(row=0, column=2, sticky="ew", padx=(12, 16), pady=6)

        # =====================================================================
        # MAIN AREA LEFT: Scrollable controls + measurement settings
        # =====================================================================
        self.left_scroll = ctk.CTkScrollableFrame(self, width=350)
        self.left_scroll.grid(row=1, column=0, sticky="nsew", padx=(16, 0), pady=(0, 16))
        self.left_scroll.grid_columnconfigure(0, weight=1)

        self.control_panel = ControlPanel(
            self.left_scroll,
            initialize_callback=self.cmd_initialize,
            measure_callback=self.cmd_measure,
            move_lin_abs_callback=self.cmd_move_lin_abs,
            move_lin_rel_callback=self.cmd_move_lin_rel,
            move_rot_abs_callback=self.cmd_move_rot_abs,
            move_rot_rel_callback=self.cmd_move_rot_rel,
            home_lin_callback=self.cmd_home_lin,
            home_rot_callback=self.cmd_home_rot,
        )
        self.control_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        self.meas_settings = MeasurementSettingsPanel(
            self.left_scroll, on_settings_changed=self._on_meas_settings_changed,
        )
        self.meas_settings.grid(row=1, column=0, sticky="nsew")

        # =====================================================================
        # MAIN AREA RIGHT: Graph + Serial Log
        # =====================================================================
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=(0, 16))
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)

        self.graph_panel = GraphPanel(self.right_frame)
        self.graph_panel.grid(row=0, column=0, sticky="nsew")

        self.serial_log_panel = SerialLogPanel(self.right_frame)
        self.serial_log_panel.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

    # -----------------------------------------------------------------
    # Connection
    # -----------------------------------------------------------------
    def cmd_connect(self):
        port_choice = self.port_var.get()
        if self.controller and self.controller.state != State.DISCONNECTED:
            self.controller.disconnect()
            self.status_panel.update_subsystems(None)
            self.serial_log_panel.clear()
            self.btn_connect.configure(text="Connect", fg_color="#1F538D")
            self.controller = None
            self.last_result_displayed = None
            self.init_sequence_active = False
            self.init_phase = None
            return

        is_mock = (port_choice == "MOCK")
        self.controller = P4PPController(port=port_choice, mock=is_mock)

        if self.controller.connect():
            self.controller.correction_factor = self.meas_settings.get_correction_factor()
            self.btn_connect.configure(text="Disconnect", fg_color="#A31C2D")
            self.status_panel.update_subsystems(self.controller)
            self.status_panel.update_position(self.controller.pos_lin, self.controller.pos_rot)
            self.serial_log_panel.clear()
            self.serial_log_panel.append_lines(["[APP] Connected."])
            self.last_result_displayed = self.controller.latest_result
            self.last_state = self.controller.state
            self.after(100, self.poll_hardware)
        else:
            self.status_panel.update_subsystems(None)

    # -----------------------------------------------------------------
    # Commands
    # -----------------------------------------------------------------
    def cmd_initialize(self):
        if not self.controller or self.controller.state != State.IDLE:
            return
        self.init_sequence_active = True
        self.init_phase = "lin"
        if not self.controller.home_linear():
            self.init_sequence_active = False
            self.init_phase = None

    def _on_meas_settings_changed(self):
        if self.controller:
            self.controller.correction_factor = self.meas_settings.get_correction_factor()

    def cmd_measure(self):
        if self.controller:
            cycles = self.meas_settings.get_cycles()
            self.controller.measure(cycles=cycles)

    def cmd_home_lin(self):
        if self.controller:
            self.controller.home_linear()

    ROT_SAFETY_LIN_MM = 45.0  # Block rotation if linear position >= this

    def cmd_home_rot(self):
        if self.controller:
            if self._check_rotation_safe():
                self.controller.home_rotational()

    def cmd_move_lin_abs(self, mm_target: float):
        if self.controller:
            steps = self.controller.mm_to_lin_steps(mm_target)
            self.controller.move_linear(steps, relative=False)

    def cmd_move_lin_rel(self, delta_mm: float, direction: int):
        if self.controller:
            steps = self.controller.mm_to_lin_steps(abs(delta_mm)) * (1 if direction >= 0 else -1)
            self.controller.move_linear(steps, relative=True)

    def cmd_move_rot_abs(self, deg_target: float):
        if self.controller:
            if self._check_rotation_safe():
                steps = self.controller.deg_to_rot_steps(deg_target)
                self.controller.move_rotational(steps, relative=False)

    def cmd_move_rot_rel(self, delta_deg: float, direction: int):
        if self.controller:
            if self._check_rotation_safe():
                steps = self.controller.deg_to_rot_steps(abs(delta_deg)) * (1 if direction >= 0 else -1)
                self.controller.move_rotational(steps, relative=True)

    def _check_rotation_safe(self) -> bool:
        if not self.controller:
            return False
        lin_mm = P4PPController.lin_steps_to_mm(self.controller.pos_lin)
        if lin_mm >= self.ROT_SAFETY_LIN_MM:
            logger.warning("Rotation blocked: LIN=%.1fmm >= %.1fmm safety limit", lin_mm, self.ROT_SAFETY_LIN_MM)
            self.serial_log_panel.append_lines(
                [f"[SAFETY] Rotation blocked! LIN={lin_mm:.1f}mm >= {self.ROT_SAFETY_LIN_MM:.0f}mm. Retract probe first."]
            )
            return False
        return True

    # -----------------------------------------------------------------
    # Port helpers
    # -----------------------------------------------------------------
    def _refresh_ports(self):
        current = self.port_var.get()
        ports = self._get_ports()
        self.combo_port.configure(values=ports)
        self.port_var.set(current if current in ports else ports[0])

    @staticmethod
    def _get_ports():
        devices = [p.device for p in serial.tools.list_ports.comports()]
        devices = sorted(set(devices), key=P4PPApp._port_sort_key)
        return ["MOCK"] + devices

    @staticmethod
    def _port_sort_key(port_name: str):
        m = re.match(r"^COM(\d+)$", port_name.upper())
        if m:
            return (0, int(m.group(1)))
        return (1, port_name.upper())

    # -----------------------------------------------------------------
    # Main polling loop
    # -----------------------------------------------------------------
    def poll_hardware(self):
        """Called every 100ms via Tkinter main loop."""
        if not self.controller or self.controller.state == State.DISCONNECTED:
            return

        self.controller.tick()
        self.serial_log_panel.append_lines(self.controller.drain_recent_lines())
        self.status_panel.update_subsystems(self.controller)
        self.status_panel.update_position(self.controller.pos_lin, self.controller.pos_rot)

        current_state = self.controller.state
        if current_state != self.last_state:
            if current_state in [State.MEASURING, State.MOVING, State.HOMING]:
                self.control_panel.set_buttons_enabled(False)
            else:
                self.control_panel.set_buttons_enabled(True)

            if (
                self.init_sequence_active
                and self.last_state == State.HOMING
                and current_state == State.IDLE
            ):
                if self.init_phase == "lin":
                    self.init_phase = "rot"
                    if not self.controller.home_rotational():
                        self.init_sequence_active = False
                        self.init_phase = None
                elif self.init_phase == "rot":
                    self.init_sequence_active = False
                    self.init_phase = None

            self.last_state = current_state

        if (
            self.controller.latest_result is not None
            and self.controller.latest_result != self.last_result_displayed
            and self.controller.state == State.IDLE
        ):
            self.last_result_displayed = self.controller.latest_result
            sample_name = self.control_panel.get_sample_name()
            self.status_panel.update_result(
                self.controller.latest_result,
                std=self.controller.latest_std,
            )
            self.graph_panel.add_data_point(
                self.controller.latest_result,
                std=self.controller.latest_std,
                sample_name=sample_name,
            )
            self._auto_save_csv()

        self.after(100, self.poll_hardware)

    # -----------------------------------------------------------------
    # Auto-save CSV per measurement
    # -----------------------------------------------------------------
    def _auto_save_csv(self):
        """Save a detailed CSV report for each measurement."""
        if not self.controller or self.controller.latest_result is None:
            return

        sample_name = self.control_panel.get_sample_name()
        save_dir = self.control_panel.get_save_dir()
        os.makedirs(save_dir, exist_ok=True)

        ts = datetime.now()
        ts_str = ts.strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[^\w\-.]', '_', sample_name)
        filename = f"{safe_name}_{ts_str}.csv"
        filepath = os.path.join(save_dir, filename)

        # Gather settings
        cycles = self.meas_settings.get_cycles()
        shape = self.meas_settings.shape_var.get()
        spacing = self.meas_settings.spacing_var.get()
        corr_factor = self.meas_settings.get_correction_factor()
        resistor_info = self.meas_settings.get_resistor_info()

        dim_info = ""
        if shape == "Circular":
            dim_info = f"Diameter={self.meas_settings.dim1_var.get()}mm"
        elif shape == "Rectangular":
            dim_info = f"Width={self.meas_settings.dim1_var.get()}mm, Length={self.meas_settings.dim2_var.get()}mm"

        # Position
        lin_mm = P4PPController.lin_steps_to_mm(self.controller.pos_lin)
        rot_deg = P4PPController.rot_steps_to_deg(self.controller.pos_rot)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)

            # -- Header --
            w.writerow(["P4PP Measurement Report"])
            w.writerow(["Timestamp", ts.strftime("%Y-%m-%d %H:%M:%S")])
            w.writerow(["Sample Name", sample_name])
            w.writerow(["Position", f"LIN={lin_mm:.2f}mm  ROT={rot_deg:.1f}deg"])
            w.writerow([])

            # -- Settings --
            w.writerow(["Measurement Settings"])
            w.writerow(["Current Source R_set", resistor_info["label"]])
            w.writerow(["Measurement Range", resistor_info["range"]])
            w.writerow(["Cycles (N)", cycles])
            w.writerow(["Probe Spacing (mm)", spacing])
            w.writerow(["Sample Shape", shape])
            if dim_info:
                w.writerow(["Dimensions", dim_info])
            w.writerow(["Correction Factor", f"{corr_factor:.6f}"])
            w.writerow([])

            # -- Per-cycle raw data --
            w.writerow(["Cycle Data"])
            w.writerow(["Cycle", "Raw Rs (Ohm/sq)"])
            cycle_data = self.controller.cycle_results
            if cycle_data:
                for i, rs in enumerate(cycle_data, 1):
                    w.writerow([i, f"{rs:.6f}"])
            else:
                raw = self.controller.latest_raw_result
                w.writerow([1, f"{raw:.6f}" if raw else "N/A"])
            w.writerow([])

            # -- Summary --
            w.writerow(["Summary"])
            raw_mean = self.controller.latest_raw_result
            corrected = self.controller.latest_result
            std = self.controller.latest_std
            n = len(cycle_data) if cycle_data else 1
            w.writerow(["N", n])
            w.writerow(["Raw Rs Mean (Ohm/sq)", f"{raw_mean:.6f}" if raw_mean else "N/A"])
            w.writerow(["Std Dev (Ohm/sq)", f"{std:.6f}" if std else "0.000000"])
            w.writerow(["Correction Factor", f"{corr_factor:.6f}"])
            w.writerow(["Corrected Rs (Ohm/sq)", f"{corrected:.6f}" if corrected else "N/A"])

        logger.info("Measurement saved: %s", filepath)


def main():
    app = P4PPApp()
    app.mainloop()

if __name__ == "__main__":
    main()
