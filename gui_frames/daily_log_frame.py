import tkinter as tk
from tkinter import ttk, messagebox
from .base_frame import BaseModuleFrame

# Logger setup
import logging
logger = logging.getLogger(__name__)

class DailyLogModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        # module_instance for DailyLog might be data_processing or a dedicated daily log backend
        # The original main.py uses self.app.modules.get('data_processing')
        # So, module_instance here might not be directly used if actions always call app.modules.get.
        self.log_text_input = None # Initialize attribute
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Journeyman Daily Log", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        log_frame = ttk.LabelFrame(self, text="Submit Daily Log Entry")
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)

        tk.Label(log_frame, text="Paste your daily log entry here:").pack(pady=5)

        self.log_text_input = tk.Text(log_frame, height=20, width=80, wrap="word")
        self.log_text_input.pack(pady=5, padx=5, fill="both", expand=True) # Added padding

        submit_button = ttk.Button(log_frame, text="Submit Daily Log", command=self.submit_daily_log)
        submit_button.pack(pady=10)

    def submit_daily_log(self):
        log_content = self.log_text_input.get("1.0", tk.END).strip()
        if not log_content:
            self.show_message("Input Error", "Daily log entry cannot be empty.", True)
            return

        # Get employee ID of the current user
        # This assumes user_manager.get_user_id_by_username returns an ID compatible with
        # what process_daily_log_entry expects for employee_id.
        # (e.g., Employees.EmployeeID)
        employee_id = self.app.user_manager.get_user_id_by_username(self.app.current_username)
        if not employee_id:
            self.show_message("Error", "Could not identify current user's Employee ID. Please ensure your user is linked to an employee record.", True)
            # This is a critical point: if app users are not linked to Employees table records, this will fail.
            return

        # Get active project ID
        project_id = self.app.active_project_id
        if not project_id:
            self.show_message("Error", "No active project selected. Please select a project first.", True)
            return

        # The backend logic is in DataProcessing module as per original main.py
        data_processing_module = self.app.modules.get('data_processing')
        if data_processing_module and hasattr(data_processing_module, 'process_daily_log_entry'):
            success, message = data_processing_module.process_daily_log_entry(log_content, employee_id, project_id)
            self.show_message("Daily Log Submission", message, not success)
            if success:
                self.log_text_input.delete("1.0", tk.END) # Clear input on success
        else:
            self.show_message("Error", "Data Processing module or 'process_daily_log_entry' method not available.", True)

# Example usage (for context):
# from gui_frames.daily_log_frame import DailyLogModuleFrame
# ...
# # In ProjectManagementApp.populate_navigation_menu:
# module_buttons_data = [
#     ...,
#     ('Daily Log', 'daily_log', DailyLogModuleFrame), # 'daily_log' is conceptual name for UI
#     ...
# ]
# The 'daily_log' module_name for the button might not map directly to a backend module
# if its functionality resides within another (like data_processing).
# The `module_instance` passed to __init__ would be None or the related backend module
# if specific methods from it were to be called directly via `self.module`.
# Here, it correctly uses `self.app.modules.get('data_processing')`.
