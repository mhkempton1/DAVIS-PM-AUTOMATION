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

        try:
            # Dynamically get the QuickBooksIntegrator from the already instantiated integration module
            # The 'module_instance' passed to __init__ should be the backend 'Integration' module instance
            if self.module and hasattr(self.module, 'qb_integrator'):
                 # This assumes the main Integration backend module instantiates QuickBooksIntegrator
                 # and makes it available as an attribute, e.g., self.module.qb_integrator
                 # This is a change from direct instantiation here.
                 # If the backend Integration module doesn't have qb_integrator, this will fail.
                 # Alternative: self.qb_integrator = QuickBooksIntegrator(self.app.db_manager) if it needs db_manager

                # Let's assume for now the backend module instance (`self.module`) IS the QuickBooksIntegrator
                # or provides access to it. If `self.module` is the main `Integration` class instance,
                # and `QuickBooksIntegrator` is a helper class within `integration.py`,
                # the `Integration` class would need to expose it.
                # For simplicity of refactoring this UI frame, let's assume QuickBooksIntegrator is directly available
                # or self.module has a way to get it.
                # The original code did: from integration import QuickBooksIntegrator; self.qb_integrator = QuickBooksIntegrator()
                # This implies QuickBooksIntegrator doesn't need specific args or gets them globally.

                # To keep this frame's logic similar to original during move:
                from integration import QuickBooksIntegrator # This still assumes integration.py is accessible
                self.qb_integrator = QuickBooksIntegrator() # Potential issue: if QBIntegrator needs db_manager

            else: # Fallback or if self.module is not the right object
                logger.warning("QuickBooksIntegrator not found via module instance. Attempting direct import.")
                from integration import QuickBooksIntegrator
                self.qb_integrator = QuickBooksIntegrator()


            self.qb_status_label_var = tk.StringVar(value="QB Status: Disconnected")
            tk.Label(qb_frame, textvariable=self.qb_status_label_var).grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")

            ttk.Button(qb_frame, text="Connect to QB", command=self.connect_qb_action).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
            ttk.Button(qb_frame, text="Disconnect QB", command=self.disconnect_qb_action).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

            tk.Label(qb_frame, text="QB Project ID:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
            self.qb_project_id_entry = tk.Entry(qb_frame)
            self.qb_project_id_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
            ttk.Button(qb_frame, text="Fetch SOV from QB", command=self.fetch_sov_action).grid(row=2, column=2, padx=5, pady=5, sticky="ew")

            tk.Label(qb_frame, text="Internal Project ID:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
            self.internal_project_id_entry = tk.Entry(qb_frame)
            self.internal_project_id_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
            ttk.Button(qb_frame, text="Link QB SOV to Internal", command=self.link_sov_action).grid(row=3, column=2, padx=5, pady=5, sticky="ew")

            self.current_sov_data = None
        except ImportError:
            logger.error("QuickBooksIntegrator class not found in integration.py. QB Integration disabled.")
            tk.Label(qb_frame, text="QuickBooksIntegrator class not found. Integration disabled.").grid(row=0, column=0, padx=5, pady=5)
            self.qb_integrator = None
        except Exception as e:
            logger.error(f"Error setting up QuickBooks integration UI: {e}")
            tk.Label(qb_frame, text=f"Error initializing QB UI: {e}").grid(row=0, column=0, padx=5, pady=5)
            self.qb_integrator = None


    # browse_csv and import_csv_action have been moved to IntegrationDataProcessingModuleFrame

    def connect_qb_action(self):
        if self.qb_integrator:
            success, message = self.qb_integrator.connect()
            self.show_message("QuickBooks Connection", message, not success)
            self.qb_status_label_var.set(f"QB Status: {'Connected' if success else 'Disconnected - Error'}")
        else:
            self.show_message("Error", "QuickBooks Integrator not available.", True)

    def disconnect_qb_action(self):
        if self.qb_integrator:
            success, message = self.qb_integrator.disconnect()
            self.show_message("QuickBooks Connection", message, not success)
            self.qb_status_label_var.set("QB Status: Disconnected")
        else:
            self.show_message("Error", "QuickBooks Integrator not available.", True)

    def fetch_sov_action(self):
        if not self.qb_integrator or not self.qb_integrator.is_connected: # Assumes is_connected attribute
            self.show_message("Error", "Not connected to QuickBooks.", True)
            return

        qb_project_id_external = self.qb_project_id_entry.get().strip()
        if not qb_project_id_external:
            self.show_message("Input Error", "Please enter the QuickBooks Project ID.", True)
            return

        # Assumes fetch_sov_wbs_data returns (success_boolean, data_or_message)
        success, data_or_msg = self.qb_integrator.fetch_sov_wbs_data(qb_project_id_external)
        if success:
            self.current_sov_data = data_or_msg
            self.show_message("Fetch SOV", f"Successfully fetched SOV data for QB Project '{qb_project_id_external}'. ({len(data_or_msg) if isinstance(data_or_msg, list) else '1 item' if data_or_msg else '0 items'} items)\nReady to link.")
            if isinstance(data_or_msg, list) and data_or_msg:
                try:
                    df_sov = pd.DataFrame(data_or_msg)
                    self.display_dataframe(df_sov, f"Fetched SOV for QB Project {qb_project_id_external}")
                except Exception as e:
                    logger.error(f"Could not convert SOV data to DataFrame for display: {e}")
            elif data_or_msg: # If it's not a list but some other truthy data structure
                logger.info(f"SOV data fetched but not in list format: {type(data_or_msg)}")


        else:
            self.current_sov_data = None
            self.show_message("Fetch SOV Failed", data_or_msg, True)

    def link_sov_action(self):
        if not self.qb_integrator:
            self.show_message("Error", "QuickBooks Integrator not available.", True)
            return
        if not self.current_sov_data:
            self.show_message("Error", "No SOV data fetched. Please fetch SOV data first.", True)
            return

        internal_project_id_str = self.internal_project_id_entry.get().strip()
        if not internal_project_id_str:
            if self.app.active_project_id:
                if messagebox.askyesno("Confirm Project", f"Link SOV to active project ID {self.app.active_project_id} ({self.app.active_project_name})?", parent=self):
                    internal_project_id_str = str(self.app.active_project_id)
                else:
                    self.show_message("Input Error", "Please enter the Internal Project ID to link SOV data.", True)
                    return
            else:
                self.show_message("Input Error", "Please enter the Internal Project ID to link SOV data.", True)
                return
        try:
            internal_project_id = int(internal_project_id_str)
        except ValueError:
            self.show_message("Input Error", "Internal Project ID must be a number.", True)
            return

        # Assumes link_sov_to_internal_project takes (internal_id, sov_data)
        success, message = self.qb_integrator.link_sov_to_internal_project(internal_project_id, self.current_sov_data)
        self.show_message("Link SOV", message, not success)
        if success:
            self.current_sov_data = None
            self.internal_project_id_entry.delete(0, tk.END)
            # Potentially refresh UI if needed
            if hasattr(self.app, 'load_project_list_data'):
                self.app.load_project_list_data()
