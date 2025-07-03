import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd # For display_dataframe and potentially handling backend data
from .base_frame import BaseModuleFrame

# Logger setup
import logging
logger = logging.getLogger(__name__)

class MonitoringControlModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        # Initialize attributes for widgets that are configured in on_active_project_changed
        self.info_label = None
        self.cost_variance_button = None
        self.schedule_variance_button = None
        self.summary_button = None

        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Monitoring & Control Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        self.info_label = tk.Label(self, text="Select an active project.", font=("Arial", 10, "italic"))
        self.info_label.pack(pady=5)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        self.cost_variance_button = ttk.Button(button_frame, text="Analyze Cost Variance", command=self.analyze_cost_action)
        self.cost_variance_button.pack(side="left", padx=10, pady=5)

        self.schedule_variance_button = ttk.Button(button_frame, text="Analyze Schedule Variance", command=self.analyze_schedule_action)
        self.schedule_variance_button.pack(side="left", padx=10, pady=5)

        self.summary_button = ttk.Button(button_frame, text="Get Project Summary Performance", command=self.get_summary_action)
        self.summary_button.pack(side="left", padx=10, pady=5)

        self.on_active_project_changed() # Set initial state

    def on_active_project_changed(self):
        is_project_active = bool(self.app.active_project_id)
        state = "normal" if is_project_active else "disabled"

        if self.info_label:
            self.info_label.config(text=f"Actions apply to: {self.app.active_project_name} (ID: {self.app.active_project_id})" if is_project_active else "No active project. Select in 'Project Startup'.")

        if self.cost_variance_button: self.cost_variance_button.config(state=state)
        if self.schedule_variance_button: self.schedule_variance_button.config(state=state)
        if self.summary_button: self.summary_button.config(state=state)

    def _handle_analysis_action(self, action_method_name_str, title_prefix):
        if not self.module:
            self.show_message("Error", "Monitoring & Control module not available.", True)
            return
        if not hasattr(self.module, action_method_name_str):
            self.show_message("Error", f"Action '{action_method_name_str}' not found in module.", True)
            return
        if not self.app.active_project_id:
            self.show_message("Error", "No active project selected.", True)
            return

        proj_id = self.app.active_project_id
        proj_name = self.app.active_project_name

        action_method = getattr(self.module, action_method_name_str)
        # Backend methods (e.g., analyze_cost_variance) are expected to return: (data, message)
        # where data can be a DataFrame for detailed views or a dict for summaries.
        data, msg = action_method(proj_id)

        # Determine if the operation was an error based on msg or data content
        # This heuristic might need refinement based on how backend methods signal errors.
        # For now, assume empty DataFrame or empty/None dict for data means no significant result or error.
        is_error_result = False
        if isinstance(data, pd.DataFrame) and data.empty:
            is_error_result = True # Or if msg indicates an error
        elif isinstance(data, dict) and not data:
            is_error_result = True
        elif data is None: # Explicit None might also mean an issue or no data
             is_error_result = True

        # If msg clearly indicates an error, prioritize that.
        if "error" in msg.lower() or "failed" in msg.lower():
            is_error_result = True

        self.show_message(f"{title_prefix} for {proj_name}", msg, is_error_result)

        if isinstance(data, pd.DataFrame) and not data.empty:
            self.display_dataframe(data, f"{title_prefix} for Project {proj_name} (ID: {proj_id})")
        elif isinstance(data, dict) and data:
            summary_text = f"Project {proj_name} (ID: {proj_id}) {title_prefix}:\n\n"
            for k, v in data.items():
                if k == 'suggestions' and isinstance(v, list): # Special formatting for suggestions
                    summary_text += f"\n{k.replace('_', ' ').title()}:\n"
                    for s_item in v: summary_text += f"  - {s_item}\n"
                else:
                    formatted_v = f"{v:.2f}" if isinstance(v, (int, float)) else v
                    summary_text += f"{k.replace('_', ' ').title()}: {formatted_v}\n"
            messagebox.showinfo(f"{proj_name} {title_prefix}", summary_text, parent=self)
        # If data is None or empty but msg was positive, it's already shown by show_message.

    def analyze_cost_action(self):
        self._handle_analysis_action("analyze_cost_variance", "Cost Variance")

    def analyze_schedule_action(self):
        self._handle_analysis_action("analyze_schedule_variance", "Schedule Variance")

    def get_summary_action(self):
        self._handle_analysis_action("get_project_summary_performance", "Summary Performance")
