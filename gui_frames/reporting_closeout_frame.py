import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime # Ensure datetime is imported
from .base_frame import BaseModuleFrame
# Assuming configuration.py is accessible for Config, though not directly used in this snippet
# from configuration import Config

class ReportingCloseoutModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        # Initialize attributes that are conditionally configured in on_active_project_changed
        self.eva_report_button = None
        self.perf_report_button = None
        self.final_report_button = None
        self.closeout_button = None
        self.info_label_reporting = None
        self.info_label_closeout = None
        self.foreman_daily_summary_button = None # Initialize new button
        self.create_widgets() # Create widgets after initializing attributes

    def create_widgets(self):
        tk.Label(self, text="Reporting & Closeout", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        reporting_frame = ttk.LabelFrame(self, text="Reporting Actions")
        reporting_frame.pack(pady=10, padx=20, fill="x", expand=True)

        self.info_label_reporting = tk.Label(reporting_frame, text="Select an active project for reporting actions.", font=("Arial", 10, "italic"))
        self.info_label_reporting.pack(pady=5)

        report_buttons_frame = ttk.Frame(reporting_frame)
        report_buttons_frame.pack(pady=5)

        self.eva_report_button = ttk.Button(report_buttons_frame, text="Generate WIP Estimate vs. Actual Report", command=self.generate_eva_action_consolidated)
        self.eva_report_button.pack(pady=5, fill='x')

        self.perf_report_button = ttk.Button(report_buttons_frame, text="Generate WIP Performance Summary Report", command=self.generate_perf_action_consolidated)
        self.perf_report_button.pack(pady=5, fill='x')

        self.final_report_button = ttk.Button(report_buttons_frame, text="Generate Final Closeout Report Package (Placeholder)", command=self.generate_final_closeout_reports_placeholder)
        self.final_report_button.pack(pady=5, fill='x')

        # New button for Foreman Daily Summary
        self.foreman_daily_summary_button = ttk.Button(report_buttons_frame, text="Generate Foreman Daily Summary", command=self.generate_foreman_daily_summary_action)
        self.foreman_daily_summary_button.pack(pady=5, fill='x')

        closeout_frame = ttk.LabelFrame(self, text="Project Closeout Actions")
        closeout_frame.pack(pady=10, padx=20, fill="x", expand=True)

        self.info_label_closeout = tk.Label(closeout_frame, text="Select an active project for closeout actions.", font=("Arial", 10, "italic"))
        self.info_label_closeout.pack(pady=5)

        self.closeout_button = ttk.Button(closeout_frame, text="Initiate Project Closeout", command=self.initiate_closeout_action_consolidated)
        self.closeout_button.pack(pady=10)

        self.on_active_project_changed() # Set initial state of buttons

    def on_active_project_changed(self):
        is_project_active = bool(self.app.active_project_id)
        button_state = "normal" if is_project_active else "disabled"

        if self.eva_report_button: self.eva_report_button.config(state=button_state)
        if self.perf_report_button: self.perf_report_button.config(state=button_state)
        if self.final_report_button: self.final_report_button.config(state=button_state)
        if self.closeout_button: self.closeout_button.config(state=button_state)
        if self.foreman_daily_summary_button: self.foreman_daily_summary_button.config(state=button_state) # Enable/disable new button

        reporting_info_text = f"Reports will be for: {self.app.active_project_name} (ID: {self.app.active_project_id})" if is_project_active else "No active project for reporting."
        closeout_info_text = f"Closeout will apply to: {self.app.active_project_name} (ID: {self.app.active_project_id})" if is_project_active else "No active project for closeout."

        if self.info_label_reporting: self.info_label_reporting.config(text=reporting_info_text)
        if self.info_label_closeout: self.info_label_closeout.config(text=closeout_info_text)

    def generate_eva_action_consolidated(self):
        reporting_module = self.app.modules.get('reporting')
        if not reporting_module:
            self.show_message("Error", "Reporting module not available.", True)
            return
        if not self.app.active_project_id:
            self.show_message("Error", "No active project selected for reporting.", True)
            return

        proj_id, proj_name = self.app.active_project_id, self.app.active_project_name
        df, success_gen, msg_gen = reporting_module.generate_estimate_vs_actual_report(proj_id)

        if success_gen:
            # Assuming export_report can handle DataFrame or text and determines type by 'excel'/'text'
            export_success, export_msg = reporting_module.export_report(df, f'{proj_name}_WIP_Estimate_vs_Actual', proj_id, 'excel')
            self.show_message(f"Report Export for {proj_name}", export_msg, not export_success)
        else:
            self.show_message(f"Report Generation Failed for {proj_name}", msg_gen, True)

    def generate_perf_action_consolidated(self):
        reporting_module = self.app.modules.get('reporting')
        if not reporting_module:
            self.show_message("Error", "Reporting module not available.", True)
            return
        if not self.app.active_project_id:
            self.show_message("Error", "No active project selected for reporting.", True)
            return

        proj_id, proj_name = self.app.active_project_id, self.app.active_project_name
        text_report, success_gen, msg_gen = reporting_module.generate_performance_report(proj_id)

        if success_gen:
            export_success, export_msg = reporting_module.export_report(text_report, f'{proj_name}_WIP_Performance_Summary', proj_id, 'text')
            self.show_message(f"Report Export for {proj_name}", export_msg, not export_success)
        else:
            self.show_message(f"Report Generation Failed for {proj_name}", msg_gen, True)

    def generate_final_closeout_reports_placeholder(self):
        self.show_message("Placeholder", "Logic for generating final closeout report package will be implemented here.")

    def initiate_closeout_action_consolidated(self):
        requirements_window = tk.Toplevel(self.app)
        requirements_window.title("Project Closeout Requirements")
        requirements_window.geometry("500x300")
        requirements_window.transient(self.app) # Make it a child of the main app
        requirements_window.grab_set() # Make it modal

        tk.Label(requirements_window, text="Project Closeout Requirements Checklist:", font=("Arial", 12, "bold")).pack(pady=10)
        requirements_text = (
            "Ensure the following are completed before proceeding:\n\n"
            "1. All final reports generated and verified.\n"
            "2. All project documentation archived.\n"
            "3. All cost codes reviewed and financial reconciliation done.\n"
            "4. Final stakeholder approvals obtained.\n\n"
            "(This is a conceptual checklist. Details to be implemented.)"
        )
        tk.Label(requirements_window, text=requirements_text, justify=tk.LEFT, wraplength=480).pack(pady=10, padx=10)

        def proceed_with_actual_closeout():
            requirements_window.destroy() # Close checklist window first
            closeout_module = self.app.modules.get('closeout')
            if not closeout_module:
                self.show_message("Error", "Closeout module not available.", True)
                return
            if not self.app.active_project_id:
                self.show_message("Error", "No active project selected for closeout.", True)
                return

            proj_id, proj_name = self.app.active_project_id, self.app.active_project_name
            if messagebox.askyesno("Confirm Closeout",
                                   f"Are you sure you want to proceed with closing out project '{proj_name}' (ID: {proj_id})?\n"
                                   "This action is typically final and will archive the project.", parent=self.app): # Parent to main app
                success, msg = closeout_module.closeout_project(proj_id)
                self.show_message(f"Project Closeout for {proj_name}", msg, not success)
                if success:
                    self.app.clear_active_project()
                    if hasattr(self.app, 'load_project_list_data'): # Ensure main app has this method
                        self.app.load_project_list_data() # Refresh project list
            else:
                self.show_message("Closeout Cancelled", f"Project closeout for '{proj_name}' cancelled by user.")

        button_frame_req = ttk.Frame(requirements_window)
        button_frame_req.pack(pady=10)
        ttk.Button(button_frame_req, text="Proceed with Closeout", command=proceed_with_actual_closeout).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame_req, text="Cancel", command=requirements_window.destroy).pack(side=tk.LEFT, padx=5)

    def generate_foreman_daily_summary_action(self):
        if not self.app.active_project_id:
            self.show_message("Error", "No active project selected. Please select a project first.", True)
            return

        reporting_module = self.app.modules.get('reporting')
        if not reporting_module:
            self.show_message("Error", "Reporting module not available.", True)
            return

        user_details = self.app.user_manager.get_user_details_by_username(self.app.current_username)
        employee_db_id = user_details.get('employee_db_id') if user_details else None

        if not employee_db_id:
            self.show_message("User Error", "Current user not linked to an Employee record. Cannot generate Foreman Daily Summary.", True, parent=self)
            logger.warning(f"Foreman daily summary generation blocked for app user {self.app.current_username} due to missing EmployeeID link.")
            return

        summary_text, success, msg = reporting_module.generate_foreman_daily_summary(
            project_id=self.app.active_project_id,
            employee_id=employee_db_id, # Pass the actual EmployeeID
            log_date=datetime.now().strftime("%Y-%m-%d")
        )

        if success:
            report_window = tk.Toplevel(self.app)
            report_window.title("Foreman Daily Summary")
            report_window.geometry("800x600")

            text_widget = tk.Text(report_window, wrap="word")
            text_widget.pack(expand=True, fill="both")
            text_widget.insert(tk.END, summary_text)
            text_widget.config(state="disabled") # Read-only

            ttk.Button(report_window, text="Close", command=report_window.destroy).pack(pady=10)
            report_window.transient(self.app)
            report_window.grab_set()
        else:
            self.show_message("Report Generation Failed", msg, True)
