import tkinter as tk
from tkinter import ttk
from .base_frame import BaseModuleFrame

# Logger setup
import logging
logger = logging.getLogger(__name__)

class ReportingModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Reporting Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # Note indicating that the functionality has been moved
        tk.Label(self,
                 text="This module's UI has been consolidated into 'Reporting & Closeout'.",
                 font=("Arial", 10, "italic"),
                 wraplength=400
                ).pack(pady=20, padx=20)

        # Original methods like on_active_project_changed, generate_eva_action, generate_perf_action
        # are now obsolete for this specific frame class as their UI is in ReportingCloseoutModuleFrame.
        # If this frame were to have any unique, non-consolidated reporting functions, they would be here.
        # For now, it's a placeholder.

    # All specific methods (on_active_project_changed, generate_eva_action, generate_perf_action) removed
    # as their functionality is now part of ReportingCloseoutModuleFrame.
    # If this frame were to be kept for some unique purpose, its methods would go here.

# Example usage (for context):
# This frame class would typically not be directly used anymore if consolidated.
# If it were, it would be:
# from gui_frames.reporting_frame import ReportingModuleFrame
# ...
# # In ProjectManagementApp.populate_navigation_menu:
# module_buttons_data = [
#     ...,
#     # ('Reporting', 'reporting', ReportingModuleFrame), # This entry would be removed
#     ('Reporting & Closeout', 'reporting_closeout', ReportingCloseoutModuleFrame), # This is the consolidated one
#     ...
# ]
# The backend 'reporting' module instance is still crucial and used by ReportingCloseoutModuleFrame.
