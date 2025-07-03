import tkinter as tk
from tkinter import ttk
from .base_frame import BaseModuleFrame

# Logger setup
import logging
logger = logging.getLogger(__name__)

class CloseoutModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Closeout Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # Note indicating that the functionality has been moved
        tk.Label(self,
                 text="This module's UI has been consolidated into 'Reporting & Closeout'.",
                 font=("Arial", 10, "italic"),
                 wraplength=400 # Ensure text wraps
                ).pack(pady=20, padx=20)

        # Original methods like on_active_project_changed, initiate_closeout_action
        # are now obsolete for this specific frame class as their UI is in ReportingCloseoutModuleFrame.

    # All specific methods (on_active_project_changed, initiate_closeout_action) removed.
    # If this frame were to be kept for some unique purpose, its methods would go here.

# Example usage (for context):
# This frame class would typically not be directly used anymore.
# If it were, it would be:
# from gui_frames.closeout_frame import CloseoutModuleFrame
# ...
# # In ProjectManagementApp.populate_navigation_menu (if it were still separate):
# module_buttons_data = [
#     ...,
#     # ('Closeout', 'closeout', CloseoutModuleFrame), # This entry would be removed
#     ('Reporting & Closeout', 'reporting_closeout', ReportingCloseoutModuleFrame), # Consolidated one
#     ...
# ]
# The backend 'closeout' module instance is still crucial and used by ReportingCloseoutModuleFrame.
