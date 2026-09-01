import customtkinter as ctk

_CIRCULAR_TABLE = [
    (1.0, 0.0000),
    (1.5, 0.3468),
    (2.0, 0.4892),
    (3.0, 0.6462),
    (4.0, 0.7725),
    (5.0, 0.8408),
    (7.5, 0.9204),
    (10.0, 0.9510),
    (20.0, 0.9876),
    (40.0, 0.9945),
    (100.0, 0.9991),
]
_SMITS_SQUARE_TABLE = [
    (3.0, 0.5419),
    (4.0, 0.6869),
    (5.0, 0.7744),
    (7.5, 0.8845),
    (10.0, 0.9313),
    (15.0, 0.9681),
    (20.0, 0.9818),
    (40.0, 0.9954),
]


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


def _natural_cubic_second_derivatives(points):
    """Return second derivatives for a natural cubic spline table."""
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    intervals = [x_values[i + 1] - x_values[i] for i in range(len(points) - 1)]
    secants = [
        (y_values[i + 1] - y_values[i]) / intervals[i]
        for i in range(len(points) - 1)
    ]
    interior_count = len(points) - 2
    lower = [0.0] * interior_count
    diagonal = [0.0] * interior_count
    upper = [0.0] * interior_count
    rhs = [0.0] * interior_count

    for row in range(interior_count):
        i = row + 1
        lower[row] = intervals[i - 1] if row > 0 else 0.0
        diagonal[row] = 2 * (intervals[i - 1] + intervals[i])
        upper[row] = intervals[i] if row < interior_count - 1 else 0.0
        rhs[row] = 6 * (secants[i] - secants[i - 1])

    for row in range(1, interior_count):
        multiplier = lower[row] / diagonal[row - 1]
        diagonal[row] -= multiplier * upper[row - 1]
        rhs[row] -= multiplier * rhs[row - 1]

    second_derivatives = [0.0] * len(points)
    second_derivatives[-2] = rhs[-1] / diagonal[-1]
    for row in range(interior_count - 2, -1, -1):
        second_derivatives[row + 1] = (
            rhs[row] - upper[row] * second_derivatives[row + 2]
        ) / diagonal[row]
    return second_derivatives


_SMITS_SQUARE_SECOND_DERIVATIVES = _natural_cubic_second_derivatives(
    _SMITS_SQUARE_TABLE
)


def correction_factor_square(d_over_s: float) -> float:
    """Smits finite-size factor F for centered probes on a square sample."""
    if d_over_s <= _SMITS_SQUARE_TABLE[0][0]:
        return _SMITS_SQUARE_TABLE[0][1]
    if d_over_s > _SMITS_SQUARE_TABLE[-1][0]:
        last_ratio, last_factor = _SMITS_SQUARE_TABLE[-1]
        return 1.0 - (1.0 - last_factor) * last_ratio / d_over_s

    for i in range(1, len(_SMITS_SQUARE_TABLE)):
        x1, y1 = _SMITS_SQUARE_TABLE[i]
        if d_over_s <= x1:
            x0, y0 = _SMITS_SQUARE_TABLE[i - 1]
            interval = x1 - x0
            weight_0 = (x1 - d_over_s) / interval
            weight_1 = (d_over_s - x0) / interval
            return (
                weight_0 * y0
                + weight_1 * y1
                + (
                    (weight_0**3 - weight_0)
                    * _SMITS_SQUARE_SECOND_DERIVATIVES[i - 1]
                    + (weight_1**3 - weight_1)
                    * _SMITS_SQUARE_SECOND_DERIVATIVES[i]
                )
                * interval**2
                / 6
            )

    return 1.0


def correction_factor_rectangular(d_over_s: float, aspect_ratio: float = 1.0) -> float:
    """Compatibility wrapper using the verified Smits square-sample table."""
    del aspect_ratio
    return correction_factor_square(d_over_s)


def correction_factor(width_mm: float, length_mm: float, spacing_mm: float) -> float:
    """Return F using the shorter sample side as the square-table dimension d."""
    if width_mm <= 0 or length_mm <= 0 or spacing_mm <= 0:
        raise ValueError("Sample dimensions and probe spacing must be positive")
    return correction_factor_square(min(width_mm, length_mm) / spacing_mm)


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
        self.resistor_var = ctk.StringVar(value="681 ohm")
        self.combo_resistor = ctk.CTkComboBox(
            res_frame,
            values=["681 ohm", "68.1 ohm"],
            variable=self.resistor_var,
            command=self._on_resistor_changed,
            state="readonly",
            width=100,
        )
        self.combo_resistor.grid(row=0, column=1, sticky="e")
        self.lbl_range = ctk.CTkLabel(
            self,
            text="Range: 1 kOhm/sq - 100 kOhm/sq  (I ~= 0.1 mA)",
            font=ctk.CTkFont(size=11),
        )
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
            try:
                spacing = float(self.spacing_var.get())
                width = float(self.dim1_var.get())
                length = float(self.dim2_var.get())
                d_over_s = min(width, length) / spacing
                text = f"Smits F: {factor:.4f} (d/s={d_over_s:.3f})"
            except (ValueError, ZeroDivisionError):
                text = f"Smits F: {factor:.4f} (square table)"
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
            return {"R_set": 68.1, "label": "68.1 ohm", "range": "<= 10 kOhm/sq"}
        return {"R_set": 681, "label": "681 ohm", "range": "1 kOhm/sq - 100 kOhm/sq"}

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
            return correction_factor_circular(diameter / spacing)

        try:
            width = float(self.dim1_var.get())
            length = float(self.dim2_var.get())
        except ValueError:
            return 1.0
        if width <= 0 or length <= 0:
            return 1.0
        return correction_factor(width, length, spacing)

    def get_correction_note(self) -> str:
        shape = self.shape_var.get()
        factor = self.get_correction_factor()
        if shape == "Infinite Sheet":
            return "Firmware infinite-sheet value retained; F=1.000000"

        try:
            spacing = float(self.spacing_var.get())
        except ValueError:
            return "Invalid probe spacing; F defaults to 1"
        if spacing <= 0:
            return "Invalid probe spacing; F defaults to 1"

        if shape == "Circular":
            try:
                diameter = float(self.dim1_var.get())
            except ValueError:
                return "Invalid diameter; F defaults to 1"
            return (
                f"Centered circular-sample correction; F={factor:.6f}; "
                f"diameter/s={diameter / spacing:.6f}"
            )

        try:
            width = float(self.dim1_var.get())
            length = float(self.dim2_var.get())
        except ValueError:
            return "Invalid sample dimensions; F defaults to 1"
        d_over_s = min(width, length) / spacing
        if abs(width - length) <= 1e-9:
            return (
                f"Smits finite-square correction (natural cubic spline); F={factor:.6f}; "
                f"d/s={d_over_s:.6f}"
            )
        return (
            "Smits square-table approximation using shorter side; "
            f"F={factor:.6f}; d/s={d_over_s:.6f}"
        )
