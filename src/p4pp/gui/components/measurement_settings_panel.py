import math

import customtkinter as ctk

_CIRCULAR_TABLE = [
    (1.0, 0.0000), (1.5, 0.3468), (2.0, 0.4892), (3.0, 0.6462),
    (4.0, 0.7725), (5.0, 0.8408), (7.5, 0.9204), (10.0, 0.9510),
    (20.0, 0.9876), (40.0, 0.9945), (100.0, 0.9991),
]
_RECT_AS_VALS = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 40.0]
_RECT_TABLE = {
    1.0: [0.2492, 0.3185, 0.3232, 0.3246],
    1.5: [0.4036, 0.5039, 0.5083, 0.5098],
    2.0: [0.4893, 0.5932, 0.5978, 0.5994],
    3.0: [0.5708, 0.6554, 0.6586, 0.6594],
    5.0: [0.6378, 0.6988, 0.7004, 0.7008],
    10.0: [0.6832, 0.7192, 0.7196, 0.7197],
    40.0: [0.6931, 0.6931, 0.6931, 0.6931],
}
PI_LN2 = math.pi / math.log(2)


def _lerp(x, x0, x1, y0, y1):
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def correction_factor_circular(d_over_s: float) -> float:
    if d_over_s <= _CIRCULAR_TABLE[0][0]:
        return _CIRCULAR_TABLE[0][1]
    for i in range(1, len(_CIRCULAR_TABLE)):
        if d_over_s <= _CIRCULAR_TABLE[i][0]:
            x0, y0 = _CIRCULAR_TABLE[i - 1]
            x1, y1 = _CIRCULAR_TABLE[i]
            return _lerp(d_over_s, x0, x1, y0, y1)
    return 1.0


def correction_factor_rectangular(a_over_s: float, d_over_a: float) -> float:
    if d_over_a >= 4:
        col = 3
    elif d_over_a >= 3:
        col = 2
    elif d_over_a >= 2:
        col = 1
    else:
        col = 0

    if a_over_s <= _RECT_AS_VALS[0]:
        return _RECT_TABLE[_RECT_AS_VALS[0]][col]
    for i in range(1, len(_RECT_AS_VALS)):
        if a_over_s <= _RECT_AS_VALS[i]:
            y0 = _RECT_TABLE[_RECT_AS_VALS[i - 1]][col]
            y1 = _RECT_TABLE[_RECT_AS_VALS[i]][col]
            return _lerp(a_over_s, _RECT_AS_VALS[i - 1], _RECT_AS_VALS[i], y0, y1)
    return _RECT_TABLE[_RECT_AS_VALS[-1]][col]


class MeasurementSettingsPanel(ctk.CTkFrame):
    PROBE_SPACING_DEFAULT = 1.016

    def __init__(self, master, on_settings_changed=None):
        super().__init__(master)
        self.on_settings_changed = on_settings_changed
        self.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(self, text="Measurement Settings", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_title.grid(row=0, column=0, padx=20, pady=(12, 8))

        res_frame = ctk.CTkFrame(self, fg_color="transparent")
        res_frame.grid(row=1, column=0, padx=20, pady=4, sticky="ew")
        res_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(res_frame, text="R_set:").grid(row=0, column=0, sticky="w")
        self.resistor_var = ctk.StringVar(value="68.1 Ω")
        self.combo_resistor = ctk.CTkComboBox(
            res_frame, values=["68.1 Ω", "681 Ω"], variable=self.resistor_var,
            command=self._on_resistor_changed, state="readonly", width=100,
        )
        self.combo_resistor.grid(row=0, column=1, sticky="e")
        self.lbl_range = ctk.CTkLabel(self, text="Range: <= 10 kOhm/sq  (I ~= 1 mA)", font=ctk.CTkFont(size=11))
        self.lbl_range.grid(row=2, column=0, padx=20, pady=(0, 4), sticky="w")

        cyc_frame = ctk.CTkFrame(self, fg_color="transparent")
        cyc_frame.grid(row=3, column=0, padx=20, pady=4, sticky="ew")
        cyc_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(cyc_frame, text="Cycles:").grid(row=0, column=0, sticky="w")
        self.cycles_var = ctk.StringVar(value="5")
        self.entry_cycles = ctk.CTkEntry(cyc_frame, textvariable=self.cycles_var, width=60)
        self.entry_cycles.grid(row=0, column=1, sticky="e")

        shape_frame = ctk.CTkFrame(self, fg_color="transparent")
        shape_frame.grid(row=4, column=0, padx=20, pady=4, sticky="ew")
        shape_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(shape_frame, text="Shape:").grid(row=0, column=0, sticky="w")
        self.shape_var = ctk.StringVar(value="Infinite Sheet")
        self.combo_shape = ctk.CTkComboBox(
            shape_frame,
            values=["Infinite Sheet", "Circular", "Rectangular"],
            variable=self.shape_var,
            command=self._on_shape_changed,
            state="readonly",
        )
        self.combo_shape.grid(row=0, column=1, sticky="e")

        spacing_frame = ctk.CTkFrame(self, fg_color="transparent")
        spacing_frame.grid(row=5, column=0, padx=20, pady=4, sticky="ew")
        spacing_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(spacing_frame, text="Probe spacing (mm):").grid(row=0, column=0, sticky="w")
        self.spacing_var = ctk.StringVar(value=str(self.PROBE_SPACING_DEFAULT))
        self.entry_spacing = ctk.CTkEntry(spacing_frame, textvariable=self.spacing_var, width=70)
        self.entry_spacing.grid(row=0, column=1, sticky="e")
        self.entry_spacing.bind("<FocusOut>", lambda e: self._recalc())
        self.entry_spacing.bind("<Return>", lambda e: self._recalc())

        self.dim_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dim_frame.grid(row=6, column=0, padx=20, pady=4, sticky="ew")
        self.dim_frame.grid_columnconfigure(1, weight=1)

        self.lbl_dim1 = ctk.CTkLabel(self.dim_frame, text="Diameter (mm):")
        self.dim1_var = ctk.StringVar(value="25.0")
        self.entry_dim1 = ctk.CTkEntry(self.dim_frame, textvariable=self.dim1_var, width=70)
        self.entry_dim1.bind("<FocusOut>", lambda e: self._recalc())
        self.entry_dim1.bind("<Return>", lambda e: self._recalc())

        self.lbl_dim2 = ctk.CTkLabel(self.dim_frame, text="Length (mm) || probe:")
        self.dim2_var = ctk.StringVar(value="20.0")
        self.entry_dim2 = ctk.CTkEntry(self.dim_frame, textvariable=self.dim2_var, width=70)
        self.entry_dim2.bind("<FocusOut>", lambda e: self._recalc())
        self.entry_dim2.bind("<Return>", lambda e: self._recalc())

        self.lbl_factor = ctk.CTkLabel(self, text="Correction: 1.0000 (inf sheet)", font=ctk.CTkFont(size=12))
        self.lbl_factor.grid(row=7, column=0, padx=20, pady=(4, 12), sticky="w")

        self._on_shape_changed("Infinite Sheet")

    def apply_theme(self, palette: dict):
        self.configure(fg_color=palette["left_panel_bg"])
        self._apply_theme_recursive(self, palette)
        self.lbl_range.configure(text_color=palette["accent_info"])
        self.lbl_factor.configure(text_color=palette["accent_info"])

    def _apply_theme_recursive(self, widget, palette: dict):
        for child in widget.winfo_children():
            class_name = child.__class__.__name__
            if class_name in {"CTkFrame", "CTkScrollableFrame"} and child.cget("fg_color") != "transparent":
                child.configure(fg_color=palette["panel_card"])
            elif class_name == "CTkLabel":
                child.configure(text_color=palette["text"])
            elif class_name == "CTkEntry":
                child.configure(
                    fg_color=palette["entry_bg"],
                    border_color=palette["entry_border"],
                    text_color=palette["text"],
                    placeholder_text_color=palette["text_muted"],
                )
            elif class_name == "CTkComboBox":
                child.configure(
                    fg_color=palette["entry_bg"],
                    border_color=palette["entry_border"],
                    text_color=palette["text"],
                    button_color=palette["button_bg"],
                    button_hover_color=palette["button_hover"],
                    dropdown_fg_color=palette["surface"],
                    dropdown_hover_color=palette["surface_alt"],
                    dropdown_text_color=palette["text"],
                )
            self._apply_theme_recursive(child, palette)

    def _on_shape_changed(self, choice: str):
        for widget in self.dim_frame.winfo_children():
            widget.grid_forget()

        if choice == "Circular":
            self.lbl_dim1.configure(text="Diameter (mm):")
            self.lbl_dim1.grid(row=0, column=0, sticky="w")
            self.entry_dim1.grid(row=0, column=1, sticky="e")
        elif choice == "Rectangular":
            self.lbl_dim1.configure(text="Width (mm) _|_ probe:")
            self.dim1_var.set("20.0")
            self.lbl_dim1.grid(row=0, column=0, sticky="w")
            self.entry_dim1.grid(row=0, column=1, sticky="e")
            self.lbl_dim2.grid(row=1, column=0, sticky="w", pady=(4, 0))
            self.entry_dim2.grid(row=1, column=1, sticky="e", pady=(4, 0))

        self._recalc()

    def _recalc(self):
        factor = self.get_correction_factor()
        shape = self.shape_var.get()
        if shape == "Infinite Sheet":
            text = f"Correction: {factor:.4f} (inf sheet)"
        elif shape == "Circular":
            text = f"Correction: {factor:.4f} (circular)"
        else:
            text = f"Correction: {factor:.4f} (rectangular)"
        self.lbl_factor.configure(text=text)

        if self.on_settings_changed:
            self.on_settings_changed()

    def get_cycles(self) -> int:
        try:
            return max(1, min(int(self.cycles_var.get()), 20))
        except ValueError:
            return 5

    def _on_resistor_changed(self, choice: str):
        if "68.1" in choice:
            self.lbl_range.configure(text="Range: <= 10 kOhm/sq  (I ~= 1 mA)")
        else:
            self.lbl_range.configure(text="Range: 1 kOhm/sq - 100 kOhm/sq  (I ~= 0.1 mA)")
        if self.on_settings_changed:
            self.on_settings_changed()

    def get_resistor_info(self) -> dict:
        if "68.1" in self.resistor_var.get():
            return {"R_set": 68.1, "label": "68.1 Ω", "range": "<= 10 kOhm/sq"}
        return {"R_set": 681, "label": "681 Ω", "range": "1 kOhm/sq - 100 kOhm/sq"}

    def get_correction_factor(self) -> float:
        shape = self.shape_var.get()
        if shape == "Infinite Sheet":
            return 1.0

        try:
            spacing = float(self.spacing_var.get())
        except ValueError:
            return 1.0
        if spacing <= 0:
            return 1.0

        if shape == "Circular":
            try:
                diameter = float(self.dim1_var.get())
            except ValueError:
                return 1.0
            if diameter <= 0:
                return 1.0
            raw_factor = correction_factor_circular(diameter / spacing)
            return (raw_factor * PI_LN2) / PI_LN2

        try:
            width = float(self.dim1_var.get())
            length = float(self.dim2_var.get())
        except ValueError:
            return 1.0
        if width <= 0 or length <= 0:
            return 1.0
        raw_factor = correction_factor_rectangular(width / spacing, length / width)
        return raw_factor / (math.log(2) / math.pi)
