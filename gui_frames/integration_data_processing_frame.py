import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
from .base_frame import BaseModuleFrame
from configuration import Config # Assuming Config is accessible
# from utils import calculate_end_date # Assuming utils.py is in the parent directory

# To resolve calculate_end_date, we might need to adjust sys.path or ensure utils is importable
# For now, let's assume it becomes available or is moved/refactored.
# If utils.py is in the same directory as main.py (one level up from gui_frames),
# we might need:
# import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import calculate_end_date


class IntegrationDataProcessingModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_widgets() # Ensure widgets are created

    def create_widgets(self):
        tk.Label(self, text="Integration & Data Processing", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # --- Project Creation Section (Moved from ProjectStartupModuleFrame) ---
        project_frame = ttk.LabelFrame(self, text="Create New Project")
        project_frame.pack(pady=10, padx=20, fill="x")
        project_frame.columnconfigure(1, weight=1)

        tk.Label(project_frame, text="Project Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.project_name_entry = tk.Entry(project_frame)
        self.project_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(project_frame, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.start_date_entry = tk.Entry(project_frame)
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(project_frame, text="Duration (in days):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.duration_days_entry = tk.Entry(project_frame)
        self.duration_days_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        create_project_button = ttk.Button(project_frame, text="Create Project & Set Active", command=self.create_project_action_consolidated)
        create_project_button.grid(row=3, column=0, columnspan=2, pady=10)

        # --- Integration Section (from IntegrationModuleFrame) ---
        import_frame = ttk.LabelFrame(self, text="Import Estimate Data (CSV)")
        import_frame.pack(pady=10, padx=20, fill="x")

        self.csv_path_label_var = tk.StringVar(value="No file selected")
        tk.Label(import_frame, textvariable=self.csv_path_label_var).pack(side="left", padx=5, pady=5)
        ttk.Button(import_frame, text="Browse CSV", command=self.browse_csv_consolidated).pack(side="left", padx=5, pady=5)
        ttk.Button(import_frame, text="Import", command=self.import_csv_action_consolidated).pack(side="right", padx=5, pady=5)
        self.selected_csv_path = None

        # --- Data Processing Section (from DataProcessingModuleFrame) ---
        data_proc_part_frame = ttk.LabelFrame(self, text="Data Processing Actions")
        data_proc_part_frame.pack(pady=10, padx=20, fill="x")
        ttk.Button(data_proc_part_frame, text="Process Raw Estimate Data", command=self.process_data_action_consolidated).pack(pady=10)

        # --- Placeholder for Quote/PO ---
        quote_po_frame = ttk.LabelFrame(self, text="Quote/PO Information")
        quote_po_frame.pack(pady=10, padx=20, fill="x")
        ttk.Button(quote_po_frame, text="Add Quote/PO (Placeholder)").pack(pady=5)

    def create_project_action_consolidated(self):
        # from utils import calculate_end_date # Already imported at the top

        name = self.project_name_entry.get().strip()
        start_date_str = self.start_date_entry.get().strip()
        duration_str = self.duration_days_entry.get().strip()

        if not name or not start_date_str or not duration_str:
            self.show_message("Input Error", "Project Name, Start Date, and Duration are required.", True)
            return
        try:
            datetime.strptime(start_date_str, "%Y-%m-%d")
            duration_days_int = int(duration_str)
            if duration_days_int < 0: raise ValueError("Duration must be non-negative.")
        except ValueError as e:
            self.show_message("Input Error", f"Invalid date or duration: {e}", True)
            return

        calculated_end_date_str = calculate_end_date(start_date_str, duration_days_int)
        if "Error:" in calculated_end_date_str: # Assuming calculate_end_date returns "Error: ..." on failure
            self.show_message("Date Calculation Error", calculated_end_date_str, True)
            return

        project_startup_module = self.app.modules.get('project_startup')
        if project_startup_module:
            # Assuming create_project signature is (name, start_date, end_date_calculated, duration_days)
            project_id, msg = project_startup_module.create_project(name, start_date_str, calculated_end_date_str, duration_days_int)
            if project_id: # Assuming create_project returns (id, msg) and id is non-None on success
                self.app.set_active_project(project_id, name)
                self.show_message("Project Creation", f"{msg}\nProject ID: {project_id}\n'{name}' is now the active project.")
                self.project_name_entry.delete(0, tk.END)
                self.start_date_entry.delete(0, tk.END)
                self.duration_days_entry.delete(0, tk.END)
                if hasattr(self.app, 'load_project_list_data'): # Ensure main app has this method
                    self.app.load_project_list_data()
            else:
                self.show_message("Project Creation Failed", msg, True)
        else:
            self.show_message("Error", "Project Startup module not available.", True)

    def browse_csv_consolidated(self):
        file_path = filedialog.askopenfilename(
            initialdir=Config.get_data_dir(), # Use Config for path
            title="Select CSV File",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            parent=self # For proper modality
        )
        if file_path:
            self.csv_path_label_var.set(os.path.basename(file_path))
            self.selected_csv_path = file_path
        else:
            self.csv_path_label_var.set("No file selected")
            self.selected_csv_path = None

    def import_csv_action_consolidated(self):
        if self.selected_csv_path:
            active_project_id = self.app.active_project_id # Get from app instance
            if active_project_id:
                if not messagebox.askyesno("Confirm Project Link", f"Link this CSV import to active project ID {active_project_id} ({self.app.active_project_name})?", parent=self):
                    active_project_id = None # User chose not to link

            integration_module = self.app.modules.get('integration')
            if integration_module and hasattr(integration_module, 'import_estimate_from_csv'):
                success, message = integration_module.import_estimate_from_csv(self.selected_csv_path, project_id=active_project_id)
                self.show_message("Import Result", message, not success)
            else:
                self.show_message("Error", "Integration module not available or method missing.", True)
        else:
            self.show_message("Error", "Please select a CSV file first.", True)

    def process_data_action_consolidated(self):
        data_processing_module = self.app.modules.get('data_processing')
        if data_processing_module:
            # Assuming process_estimate_data does not require project_id directly,
            # or handles it internally if needed (e.g. processing all unlinked)
            success, message = data_processing_module.process_estimate_data()
            self.show_message("Data Processing Result", message, not success)
        else:
            self.show_message("Error", "Data Processing module not available.", True)

# Note: Ensure this file is saved as pm_system-main/project-management_system/gui_frames/integration_data_processing_frame.py
# And that utils.py and configuration.py are correctly importable from this location.
# If utils.py is in the parent directory of gui_frames, the import `from utils import calculate_end_date`
# might require sys.path modification or making `project_management_system` a package that's properly on the path.
# A common way is to run main.py from the root of `project_management_system` and ensure all imports are relative
# to that root or use absolute package imports if `project_management_system` itself is treated as a package.
# The current structure with `sys.path.insert(0, current_dir)` in main.py helps with this.
# So, `from utils import calculate_end_date` should work if `utils.py` is in the same directory as `main.py`.
# And `from .base_frame import BaseModuleFrame` is correct for sibling modules within the `gui_frames` package.
# `from configuration import Config` should also work if `configuration.py` is in the same dir as `main.py`.
