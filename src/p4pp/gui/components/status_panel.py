import customtkinter as ctk
from src.p4pp.driver import P4PPController, Command, State


class StatusPanel(ctk.CTkFrame):
    """Compact status panel designed for the top bar layout."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=1)

        # Subsystem status indicators (compact inline with text)
        indicator_frame = ctk.CTkFrame(self, fg_color="transparent")
        indicator_frame.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.dot_lin, self.txt_lin = self._make_indicator(indicator_frame, "LIN", row=0, col=0)
        self.dot_rot, self.txt_rot = self._make_indicator(indicator_frame, "ROT", row=0, col=1)
        self.dot_meas, self.txt_meas = self._make_indicator(indicator_frame, "MEAS", row=0, col=2)

        # Position label
        self.lbl_pos = ctk.CTkLabel(
            self,
            text="LIN: 0.00mm | ROT: 0.00°",
            font=ctk.CTkFont(size=12),
            text_color="#A0A0A0",
        )
        self.lbl_pos.grid(row=0, column=1, padx=(0, 12), sticky="w")

        # Sheet Resistance result (large, right-aligned)
        self.lbl_result = ctk.CTkLabel(
            self,
            text="--- Ω/sq",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#2ECC71",
        )
        self.lbl_result.grid(row=0, column=3, padx=(0, 4), sticky="e")

        self.update_subsystems(None)

    def _make_indicator(self, parent, label: str, row: int, col: int):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=(0, 10))
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=(0, 2))
        dot = ctk.CTkLabel(frame, text="●", font=ctk.CTkFont(size=11), text_color="#A31C2D")
        dot.grid(row=0, column=1, padx=(0, 2))
        txt = ctk.CTkLabel(frame, text="OFF", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A31C2D")
        txt.grid(row=0, column=2)
        return dot, txt

    @staticmethod
    def _status_color(status_text: str):
        if status_text in ("IDLE", "READY"):
            return "#2ECC71"
        if status_text in ("RUNNING", "HOMING", "MEASURING", "MOVING"):
            return "#F1C40F"
        if status_text in ("CONNECTED",):
            return "#5DADE2"
        return "#A31C2D"

    def _set_indicator(self, dot, txt, status_text: str):
        color = self._status_color(status_text)
        dot.configure(text_color=color)
        txt.configure(text=status_text, text_color=color)

    def update_subsystems(self, controller):
        if controller is None or controller.state == State.DISCONNECTED:
            self._set_indicator(self.dot_lin, self.txt_lin, "OFF")
            self._set_indicator(self.dot_rot, self.txt_rot, "OFF")
            self._set_indicator(self.dot_meas, self.txt_meas, "OFF")
            return

        if controller.state == State.ERROR:
            self._set_indicator(self.dot_lin, self.txt_lin, "ERROR")
            self._set_indicator(self.dot_rot, self.txt_rot, "ERROR")
            self._set_indicator(self.dot_meas, self.txt_meas, "ERROR")
            return

        lin_status = "CONNECTED"
        rot_status = "CONNECTED"
        meas_status = "READY"

        if controller.has_homed_lin:
            lin_status = "IDLE"
        if controller.has_homed_rot:
            rot_status = "IDLE"

        if controller.active_task == Command.HOME_LIN and controller.state == State.HOMING:
            lin_status = "HOMING"
        elif controller.active_task == Command.MOVE_LIN and controller.state == State.MOVING:
            lin_status = "MOVING"

        if controller.active_task == Command.HOME_ROT and controller.state == State.HOMING:
            rot_status = "HOMING"
        elif controller.active_task == Command.MOVE_ROT and controller.state == State.MOVING:
            rot_status = "MOVING"

        if controller.active_task == Command.MEASURE and controller.state == State.MEASURING:
            meas_status = "MEASURING"

        self._set_indicator(self.dot_lin, self.txt_lin, lin_status)
        self._set_indicator(self.dot_rot, self.txt_rot, rot_status)
        self._set_indicator(self.dot_meas, self.txt_meas, meas_status)

    def update_result(self, result: float, std: float = None):
        if result is None:
            self.lbl_result.configure(text="--- Ω/sq")
        elif std is not None and std > 0:
            self.lbl_result.configure(text=f"{result:.3f} ± {std:.3f} Ω/sq")
        else:
            self.lbl_result.configure(text=f"{result:.3f} Ω/sq")

    def update_position(self, pos_lin: int, pos_rot: int):
        lin_mm = P4PPController.lin_steps_to_mm(pos_lin)
        rot_deg = P4PPController.rot_steps_to_deg(pos_rot)
        self.lbl_pos.configure(text=f"LIN: {lin_mm:.2f}mm | ROT: {rot_deg:.1f}°")
