import tkinter as tk
from tkinter import ttk
from .base_frame import BaseModuleFrame

# Logger setup (assuming main app configures root logger)
import logging
logger = logging.getLogger(__name__)

class DataProcessingModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Data Processing Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # Note indicating that the functionality has been moved
        tk.Label(self,
                 text="This module's UI has been consolidated into 'Integration & Data Processing'.",
                 font=("Arial", 10, "italic"),
                 wraplength=400 # Ensure text wraps if window is narrow
                ).pack(pady=20, padx=20)

        # Placeholder for any specific data processing tasks that might not fit elsewhere,
        # or this frame could be entirely removed if all functionality is covered.
        # For now, it serves as a clear indicator of the consolidation.

        # Example: If there were other specific, non-consolidated actions:
        # other_actions_frame = ttk.LabelFrame(self, text="Other Data Tasks")
        # other_actions_frame.pack(pady=10, padx=20, fill="x")
        # ttk.Button(other_actions_frame, text="Perform Special Cleanup", command=self.perform_special_cleanup_placeholder).pack(pady=5)

    # def perform_special_cleanup_placeholder(self):
    #     self.show_message("Placeholder", "Special data cleanup action would be performed here.")

    # process_data_action has been moved to IntegrationDataProcessingModuleFrame as process_data_action_consolidated.
    # If there was a direct method call here like:
    # ttk.Button(self, text="Process Data (Old)", command=self.process_data_action).pack()
    # it would now be obsolete. The consolidated frame handles the UI and action.

# Example usage (for context):
# from gui_frames.data_processing_frame import DataProcessingModuleFrame
# ...
# # In ProjectManagementApp.populate_navigation_menu (if it were still separate):
# module_buttons_data = [
#     ...,
#     ('Data Processing', 'data_processing', DataProcessingModuleFrame), # This entry would be removed due to consolidation
#     ...
# ]
# The 'data_processing' module instance (backend) is still used by IntegrationDataProcessingModuleFrame.
