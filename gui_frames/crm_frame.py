import tkinter as tk
from .base_frame import BaseModuleFrame

class CrmModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="CRM Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)
