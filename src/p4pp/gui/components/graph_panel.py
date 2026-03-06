import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import os
from datetime import datetime

class GraphPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Data storage
        self.x_data = []
        self.y_data = []
        self.e_data = []
        self.s_data = []  # sample names
        self.counter = 0
        
        # Setup Matplotlib Figure (Dark Theme)
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor('#2B2B2B')
        self.ax.set_facecolor('#2B2B2B')
        self.ax.set_title('Measurement History', color='white')
        self.ax.set_xlabel('Measurement #', color='gray')
        self.ax.set_ylabel('Rs (Ω/sq)', color='gray')
        self.ax.tick_params(colors='gray')
        for spine in self.ax.spines.values():
            spine.set_color('#555555')
            
        self.line, = self.ax.plot([], [], marker='o', color='#2ECC71', linestyle='-', markersize=6)
        
        # Embed in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Export Button
        self.btn_export = ctk.CTkButton(self, text="Export History CSV", command=self.export_csv, fg_color="#1F538D")
        self.btn_export.grid(row=1, column=0, pady=(0, 10))

    def add_data_point(self, result: float, std: float = None, sample_name: str = ""):
        if result is None:
            return
            
        self.counter += 1
        self.x_data.append(self.counter)
        self.y_data.append(result)
        self.e_data.append(std if std else 0)
        self.s_data.append(sample_name or "untitled")
        
        self.ax.clear()
        self.ax.set_facecolor('#2B2B2B')
        self.ax.set_title('Measurement History', color='white')
        self.ax.set_xlabel('Measurement #', color='gray')
        self.ax.set_ylabel('Rs (Ω/sq)', color='gray')
        self.ax.tick_params(colors='gray')
        for spine in self.ax.spines.values():
            spine.set_color('#555555')

        has_errors = any(e > 0 for e in self.e_data)
        if has_errors:
            self.ax.errorbar(
                self.x_data, self.y_data, yerr=self.e_data,
                marker='o', color='#2ECC71', linestyle='-', markersize=6,
                ecolor='#F1C40F', elinewidth=1.5, capsize=4,
            )
        else:
            self.ax.plot(
                self.x_data, self.y_data,
                marker='o', color='#2ECC71', linestyle='-', markersize=6,
            )
        
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def export_csv(self):
        if not self.x_data:
            return
            
        os.makedirs("data/exported", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/exported/measurement_history_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Sample", "Rs_Mean (Ohm/sq)", "Std_Dev (Ohm/sq)"])
            for x, y, e, s in zip(self.x_data, self.y_data, self.e_data, self.s_data):
                writer.writerow([x, s, f"{y:.6f}", f"{e:.6f}"])
                
        print(f"Exported history to {filename}")

