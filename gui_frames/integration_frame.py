import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import pandas as pd # Added import for pd.DataFrame
from .base_frame import BaseModuleFrame
# from configuration import Config # Assuming Config is accessible if needed for paths
# from integration import QuickBooksIntegrator # Backend class

# Logger setup (assuming main app configures root logger)
import logging
logger = logging.getLogger(__name__)

class IntegrationModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        # Initialize attributes that might be accessed before/during create_widgets
        self.qb_integrator = None
        self.qb_status_label_var = tk.StringVar(value="QB Status: Initializing...")
        self.qb_project_id_entry = None
        self.internal_project_id_entry = None
        self.current_sov_data = None
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Integration Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # CSV Import UI has been moved to IntegrationDataProcessingModuleFrame
        # So, this section in the original IntegrationModuleFrame is effectively deprecated here.
        # We can leave a note or remove it if this frame is purely for other integrations now.

        # Note about CSV import being moved
        csv_note_frame = ttk.LabelFrame(self, text="CSV Import")
        csv_note_frame.pack(pady=10, padx=20, fill="x")
        tk.Label(csv_note_frame, text="CSV import functionality is now part of the 'Integration & Data Processing' module.").pack(pady=5, padx=5)

        export_frame = ttk.LabelFrame(self, text="Export Reports")
        export_frame.pack(pady=10, padx=20, fill="x")
        tk.Label(export_frame, text="Use the 'Reporting & Closeout' module for report generation and export.").pack(pady=5, padx=5)

        # --- QuickBooks Integration Frame ---
        qb_frame = ttk.LabelFrame(self, text="QuickBooks Integration (SOV-WBS Framework)")
        qb_frame.pack(pady=10, padx=20, fill="x")
        qb_frame.columnconfigure(1, weight=1) # Make entry fields expand

        # QuickBooks Integration section
        # self.module_instance is the backend Integration module

        self.qb_status_label_var = tk.StringVar(value="QB Status: Not checked")
        tk.Label(qb_frame, textvariable=self.qb_status_label_var).grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Button(qb_frame, text="Connect to QB", command=self.connect_qb_action).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(qb_frame, text="Disconnect QB", command=self.disconnect_qb_action).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(qb_frame, text="Check QB Status", command=self.check_qb_status_action).grid(row=1, column=2, padx=5, pady=5, sticky="ew")


        tk.Label(qb_frame, text="QB Project ID:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.qb_project_id_entry = tk.Entry(qb_frame)
        self.qb_project_id_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        ttk.Button(qb_frame, text="Fetch SOV from QB", command=self.fetch_sov_action).grid(row=2, column=2, padx=5, pady=5, sticky="ew")

        tk.Label(qb_frame, text="Internal Project ID:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.internal_project_id_entry = tk.Entry(qb_frame)
        self.internal_project_id_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        ttk.Button(qb_frame, text="Link QB SOV to Internal", command=self.link_sov_action).grid(row=3, column=2, padx=5, pady=5, sticky="ew")

        self.current_sov_data = None
        self.check_qb_status_action() # Initial status check


    # browse_csv and import_csv_action have been moved to IntegrationDataProcessingModuleFrame

    def _check_module_and_method(self, method_name):
        if not self.module_instance:
            self.show_message("Error", "Integration backend module not available.", True)
            return False
        if not hasattr(self.module_instance, method_name):
            self.show_message("Error", f"'{method_name}' not found in Integration module.", True)
            return False
        return True

    def check_qb_status_action(self):
        if not self._check_module_and_method('is_quickbooks_connected'):
            self.qb_status_label_var.set("QB Status: Error (backend missing)")
            return

        is_connected, status_msg = self.module_instance.is_quickbooks_connected()
        self.qb_status_label_var.set(f"QB Status: {status_msg}")


    def connect_qb_action(self):
        if not self._check_module_and_method('connect_quickbooks'): return
        success, message = self.module_instance.connect_quickbooks()
        self.show_message("QuickBooks Connection", message, not success)
        self.check_qb_status_action()


    def disconnect_qb_action(self):
        if not self._check_module_and_method('disconnect_quickbooks'): return
        success, message = self.module_instance.disconnect_quickbooks()
        self.show_message("QuickBooks Connection", message, not success)
        self.check_qb_status_action()


    def fetch_sov_action(self):
        if not self._check_module_and_method('fetch_quickbooks_sov'): return

        is_connected, _ = self.module_instance.is_quickbooks_connected() # Verify connection again
        if not is_connected:
            self.show_message("Error", "Not connected to QuickBooks. Please connect first.", True)
            return

        qb_project_id_external = self.qb_project_id_entry.get().strip()
        if not qb_project_id_external:
            self.show_message("Input Error", "Please enter the QuickBooks Project ID.", True)
            return

        success, data_or_msg = self.module_instance.fetch_quickbooks_sov(qb_project_id_external)
        if success:
            self.current_sov_data = data_or_msg
            display_msg = f"Successfully fetched SOV data for QB Project '{qb_project_id_external}'. "
            if isinstance(data_or_msg, list):
                display_msg += f"({len(data_or_msg)} items)\nReady to link."
                if data_or_msg:
                    try:
                        df_sov = pd.DataFrame(data_or_msg)
                        self.display_dataframe(df_sov, f"Fetched SOV for QB Project {qb_project_id_external}")
                    except Exception as e:
                        logger.error(f"Could not convert SOV data to DataFrame: {e}")
                        display_msg += "\n(Could not display preview as table)"
            elif data_or_msg:
                 display_msg += "(Data received, format not list for preview)"
            else:
                display_msg += "(No data items returned)"
            self.show_message("Fetch SOV", display_msg)
        else:
            self.current_sov_data = None
            self.show_message("Fetch SOV Failed", data_or_msg, True)

    def link_sov_action(self):
        if not self._check_module_and_method('link_quickbooks_sov_to_internal'): return

        if not self.current_sov_data:
            self.show_message("Error", "No SOV data fetched. Please fetch SOV data first.", True)
            return

        internal_project_id_str = self.internal_project_id_entry.get().strip()
        if not internal_project_id_str:
            if self.app.active_project_id:
                if messagebox.askyesno("Confirm Project", f"Link SOV to active project ID {self.app.active_project_id} ({self.app.active_project_name})?", parent=self):
                    internal_project_id_str = str(self.app.active_project_id)
                else:
                    self.show_message("Input Error", "Please enter or confirm Internal Project ID.", True)
                    return
            else:
                self.show_message("Input Error", "Internal Project ID required.", True)
                return
        try:
            internal_project_id = int(internal_project_id_str)
        except ValueError:
            self.show_message("Input Error", "Internal Project ID must be a number.", True)
            return

        success, message = self.module_instance.link_quickbooks_sov_to_internal(internal_project_id, self.current_sov_data)
        self.show_message("Link SOV", message, not success)
        if success:
            self.current_sov_data = None # Clear data after successful link
            self.internal_project_id_entry.delete(0, tk.END)
            if hasattr(self.app, 'load_project_list_data'):
                self.app.load_project_list_data()
