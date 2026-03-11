import csv
import logging
import os
from datetime import datetime

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

logger = logging.getLogger(__name__)


class GraphPanel(ctk.CTkFrame):
    THEME_COLORS = {
        "Light": {
            "figure": "#FFFFFF",
            "axes": "#FFFFFF",
            "title": "#111827",
            "label": "#4B5563",
            "ticks": "#6B7280",
            "spine": "#D1D5DB",
            "line": "#1D4ED8",
            "error": "#B45309",
            "grid": "#E5E7EB",
        },
        "Dark": {
            "figure": "#2A2A2A",
            "axes": "#2A2A2A",
            "title": "#E5E7EB",
            "label": "#8B949E",
            "ticks": "#8B949E",
            "spine": "#565C63",
            "line": "#35D07F",
            "error": "#F1C40F",
            "grid": "#3A3F45",
        },
    }

    def __init__(self, master):
        super().__init__(master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.x_data = []
        self.y_data = []
        self.e_data = []
        self.s_data = []
        self.counter = 0
        self.current_theme = "Light"

        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self._redraw_plot()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.btn_export = ctk.CTkButton(
            self,
            text="Export History CSV",
            command=self.export_csv,
            fg_color="#1F538D",
        )
        self.btn_export.grid(row=1, column=0, pady=(0, 10))

    def add_data_point(self, result: float, std: float = None, sample_name: str = ""):
        if result is None:
            return

        self.counter += 1
        self.x_data.append(self.counter)
        self.y_data.append(result)
        self.e_data.append(std if std else 0)
        self.s_data.append(sample_name or "untitled")
        self._redraw_plot()

    def set_theme(self, theme: str):
        self.current_theme = theme if theme in self.THEME_COLORS else "Light"
        self._redraw_plot()

    def apply_theme(self, theme: str, palette: dict):
        self.configure(fg_color=palette["surface"])
        self.btn_export.configure(fg_color="#1F538D", hover_color="#163E6E", text_color="#F8FAFC")
        self.set_theme(theme)

    def _redraw_plot(self):
        colors = self.THEME_COLORS[self.current_theme]
        self.ax.clear()
        self.fig.patch.set_facecolor(colors["figure"])
        self.ax.set_facecolor(colors["axes"])
        self.ax.set_title("Measurement History", color=colors["title"])
        self.ax.set_xlabel("Measurement #", color=colors["label"])
        self.ax.set_ylabel("Rs (Ohm/sq)", color=colors["label"])
        self.ax.tick_params(colors=colors["ticks"])
        self.ax.grid(True, color=colors["grid"], linewidth=0.8, alpha=0.6)
        for spine in self.ax.spines.values():
            spine.set_color(colors["spine"])

        has_errors = any(e > 0 for e in self.e_data)
        if self.x_data:
            if has_errors:
                self.ax.errorbar(
                    self.x_data,
                    self.y_data,
                    yerr=self.e_data,
                    marker="o",
                    color=colors["line"],
                    linestyle="-",
                    markersize=6,
                    ecolor=colors["error"],
                    elinewidth=1.5,
                    capsize=4,
                )
            else:
                self.ax.plot(
                    self.x_data,
                    self.y_data,
                    marker="o",
                    color=colors["line"],
                    linestyle="-",
                    markersize=6,
                )

        self.ax.relim()
        self.ax.autoscale_view()
        if hasattr(self, "canvas"):
            self.canvas.draw_idle()

    def export_csv(self):
        if not self.x_data:
            return

        os.makedirs("data/exported", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/exported/measurement_history_{timestamp}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Sample", "Rs_Mean (Ohm/sq)", "Std_Dev (Ohm/sq)"])
            for x, y, e, s in zip(self.x_data, self.y_data, self.e_data, self.s_data):
                writer.writerow([x, s, f"{y:.6f}", f"{e:.6f}"])

        logger.info("Exported history to %s", filename)
