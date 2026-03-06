import customtkinter as ctk


class SerialLogPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Serial Log", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 6), sticky="w"
        )

        self.textbox = ctk.CTkTextbox(self, height=170)
        self.textbox.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="nsew")
        self.textbox.insert("end", "Waiting for serial data...\n")
        self.textbox.configure(state="disabled")

    def append_lines(self, lines):
        if not lines:
            return
        self.textbox.configure(state="normal")
        for line in lines:
            self.textbox.insert("end", f"{line}\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("end", "Waiting for serial data...\n")
        self.textbox.configure(state="disabled")
