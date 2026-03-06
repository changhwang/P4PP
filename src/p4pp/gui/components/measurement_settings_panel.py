import math
import customtkinter as ctk


# ---------------------------------------------------------------------------
# Correction factor lookup tables (F.M. Smits, NBS Technical Note 199)
# ---------------------------------------------------------------------------

# Circular sample, probes at center: (d/s, factor)
_CIRCULAR_TABLE = [
    (1.0, 0.0000), (1.5, 0.3468), (2.0, 0.4892), (3.0, 0.6462),
    (4.0, 0.7725), (5.0, 0.8408), (7.5, 0.9204), (10.0, 0.9510),
    (20.0, 0.9876), (40.0, 0.9945), (100.0, 0.9991),
]

# Rectangular sample, probes parallel to longer side, center measurement.
# Rows: a/s values.  Columns: d/a = 1, 2, 3, >=4
_RECT_AS_VALS = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 40.0]
_RECT_TABLE = {
    1.0:  [0.2492, 0.3185, 0.3232, 0.3246],
    1.5:  [0.4036, 0.5039, 0.5083, 0.5098],
    2.0:  [0.4893, 0.5932, 0.5978, 0.5994],
    3.0:  [0.5708, 0.6554, 0.6586, 0.6594],
    5.0:  [0.6378, 0.6988, 0.7004, 0.7008],
    10.0: [0.6832, 0.7192, 0.7196, 0.7197],
    40.0: [0.6931, 0.6931, 0.6931, 0.6931],
}

PI_LN2 = math.pi / math.log(2)  # 4.53236...


def _lerp(x, x0, x1, y0, y1):
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def correction_factor_circular(d_over_s: float) -> float:
    """Return the geometry correction factor for a circular sample."""
    if d_over_s <= _CIRCULAR_TABLE[0][0]:
        return _CIRCULAR_TABLE[0][1]
    for i in range(1, len(_CIRCULAR_TABLE)):
        if d_over_s <= _CIRCULAR_TABLE[i][0]:
            x0, y0 = _CIRCULAR_TABLE[i - 1]
            x1, y1 = _CIRCULAR_TABLE[i]
            return _lerp(d_over_s, x0, x1, y0, y1)
    return 1.0  # infinite


def correction_factor_rectangular(a_over_s: float, d_over_a: float) -> float:
    """Return the geometry correction factor for a rectangular sample."""
    # Clamp d/a to column index (1,2,3,>=4)
    if d_over_a >= 4:
        col = 3
    elif d_over_a >= 3:
        col = 2
    elif d_over_a >= 2:
        col = 1
    else:
        col = 0

    keys = _RECT_AS_VALS
    if a_over_s <= keys[0]:
        return _RECT_TABLE[keys[0]][col]
    for i in range(1, len(keys)):
        if a_over_s <= keys[i]:
            y0 = _RECT_TABLE[keys[i - 1]][col]
            y1 = _RECT_TABLE[keys[i]][col]
            return _lerp(a_over_s, keys[i - 1], keys[i], y0, y1)
    return _RECT_TABLE[keys[-1]][col]


class MeasurementSettingsPanel(ctk.CTkFrame):
    """Cycle count, shape, and geometry correction factor settings."""

    PROBE_SPACING_DEFAULT = 1.016  # mm, Signatone SP4 standard

    def __init__(self, master, on_settings_changed=None):
        super().__init__(master)
        self.on_settings_changed = on_settings_changed

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Measurement Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(12, 8))

        # --- Cycle count ---
        cyc_frame = ctk.CTkFrame(self, fg_color="transparent")
        cyc_frame.grid(row=1, column=0, padx=20, pady=4, sticky="ew")
        cyc_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(cyc_frame, text="Cycles:").grid(row=0, column=0, sticky="w")
        self.cycles_var = ctk.StringVar(value="5")
        self.entry_cycles = ctk.CTkEntry(cyc_frame, textvariable=self.cycles_var, width=60)
        self.entry_cycles.grid(row=0, column=1, sticky="e")

        # --- Shape selection ---
        shape_frame = ctk.CTkFrame(self, fg_color="transparent")
        shape_frame.grid(row=2, column=0, padx=20, pady=4, sticky="ew")
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

        # --- Probe spacing ---
        spacing_frame = ctk.CTkFrame(self, fg_color="transparent")
        spacing_frame.grid(row=3, column=0, padx=20, pady=4, sticky="ew")
        spacing_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(spacing_frame, text="Probe spacing (mm):").grid(row=0, column=0, sticky="w")
        self.spacing_var = ctk.StringVar(value=str(self.PROBE_SPACING_DEFAULT))
        self.entry_spacing = ctk.CTkEntry(spacing_frame, textvariable=self.spacing_var, width=70)
        self.entry_spacing.grid(row=0, column=1, sticky="e")
        self.entry_spacing.bind("<FocusOut>", lambda e: self._recalc())
        self.entry_spacing.bind("<Return>", lambda e: self._recalc())

        # --- Dimension inputs (hidden by default) ---
        self.dim_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dim_frame.grid(row=4, column=0, padx=20, pady=4, sticky="ew")
        self.dim_frame.grid_columnconfigure(1, weight=1)

        self.lbl_dim1 = ctk.CTkLabel(self.dim_frame, text="Diameter (mm):")
        self.dim1_var = ctk.StringVar(value="25.0")
        self.entry_dim1 = ctk.CTkEntry(self.dim_frame, textvariable=self.dim1_var, width=70)
        self.entry_dim1.bind("<FocusOut>", lambda e: self._recalc())
        self.entry_dim1.bind("<Return>", lambda e: self._recalc())

        self.lbl_dim2 = ctk.CTkLabel(self.dim_frame, text="Length (mm) ∥ probe:")
        self.dim2_var = ctk.StringVar(value="20.0")
        self.entry_dim2 = ctk.CTkEntry(self.dim_frame, textvariable=self.dim2_var, width=70)
        self.entry_dim2.bind("<FocusOut>", lambda e: self._recalc())
        self.entry_dim2.bind("<Return>", lambda e: self._recalc())

        # --- Correction factor preview ---
        self.lbl_factor = ctk.CTkLabel(
            self,
            text="Correction: 1.0000 (∞ sheet)",
            font=ctk.CTkFont(size=12),
            text_color="#9CB5D9",
        )
        self.lbl_factor.grid(row=5, column=0, padx=20, pady=(4, 12), sticky="w")

        # Initial state
        self._on_shape_changed("Infinite Sheet")

    def _on_shape_changed(self, choice: str):
        # Clear dim frame
        for w in self.dim_frame.winfo_children():
            w.grid_forget()

        if choice == "Circular":
            self.lbl_dim1.configure(text="Diameter (mm):")
            self.lbl_dim1.grid(row=0, column=0, sticky="w")
            self.entry_dim1.grid(row=0, column=1, sticky="e")
        elif choice == "Rectangular":
            self.lbl_dim1.configure(text="Width (mm) ⊥ probe:")
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
            txt = f"Correction: {factor:.4f} (∞ sheet)"
        elif shape == "Circular":
            txt = f"Correction: {factor:.4f} (circular)"
        else:
            txt = f"Correction: {factor:.4f} (rectangular)"
        self.lbl_factor.configure(text=txt)

        if self.on_settings_changed:
            self.on_settings_changed()

    def get_cycles(self) -> int:
        try:
            val = int(self.cycles_var.get())
            return max(1, min(val, 20))
        except ValueError:
            return 5

    def get_correction_factor(self) -> float:
        shape = self.shape_var.get()
        if shape == "Infinite Sheet":
            return 1.0

        try:
            s = float(self.spacing_var.get())
        except ValueError:
            return 1.0
        if s <= 0:
            return 1.0

        if shape == "Circular":
            try:
                d = float(self.dim1_var.get())
            except ValueError:
                return 1.0
            if d <= 0:
                return 1.0
            raw_factor = correction_factor_circular(d / s)
            return (raw_factor * PI_LN2) / PI_LN2  # = raw_factor itself
        elif shape == "Rectangular":
            try:
                a = float(self.dim1_var.get())  # width
                length = float(self.dim2_var.get())
            except ValueError:
                return 1.0
            if a <= 0 or length <= 0:
                return 1.0
            d_over_a = length / a
            a_over_s = a / s
            raw_factor = correction_factor_rectangular(a_over_s, d_over_a)
            # raw_factor is C where Rs = (V/I) * C * (pi/ln2)
            # Since firmware already applies 4.532, we normalize:
            return raw_factor / (math.log(2) / math.pi)  # = raw_factor * PI_LN2
        return 1.0
