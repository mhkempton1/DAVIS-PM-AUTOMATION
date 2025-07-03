import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import sys # Ensure sys is imported for sys.exit()

try:
    import PyPDF2
except ImportError:
    # We need to ensure Tk root is created for messagebox if it's the first GUI element used.
    # However, for a critical missing dependency, exiting is fine.
    # If Tk isn't ready, this messagebox might not show, but error will go to console.
    root = tk.Tk()
    root.withdraw() # Hide the root window
    messagebox.showerror("Missing Dependency", "PyPDF2 is required for PDF functionality. Please install it using: pip install PyPDF2")
    root.destroy()
    sys.exit(1)
import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta # Added timedelta just in case, though not directly used in create_project_action

# Ensure the project_management_system directory is in sys.path
# This helps with importing sibling modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import core utilities
from configuration import Config
from database_manager import db_manager
from user_management import UserManagement
from plugins.plugin_registry import PluginRegistry
from tkPDFViewer import tkPDFViewer # Added for PDF viewing
import logging.handlers # For RotatingFileHandler

# Set up logging for the Main Application
def setup_logging():
    log_directory = Config.get_logs_dir()
    log_file_path = os.path.join(log_directory, 'davinci_app.log')

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Set root logger level

    # Clear existing handlers from the root logger, if any (to avoid duplicates if script is re-run in some contexts)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console Handler (explicitly add one for consistent behavior)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Create a rotating file handler
    # Rotates when log reaches 5MB, keeps up to 5 backup logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    # Add the handler to the root logger
    logging.getLogger().addHandler(file_handler)
    # logging.getLogger().propagate = False # Optional: to prevent double logging to console if basicConfig also sets a console handler

setup_logging() # Initialize logging setup
logger = logging.getLogger(__name__) # Get logger for the current module (main.py)

# --- Test log and exit ---
# logger.info("This is a direct test log message after setup_logging.")
# import sys; sys.exit(0) # Uncomment to test logging before Tkinter starts
# --- End test log and exit ---

class LoginWindow(tk.Toplevel):
    """
    Separate window for user login.
    """
    def __init__(self, master, app_instance):
        super().__init__(master)
        self.master = master
        self.app = app_instance
        self.title("Login")
        self.geometry("300x200")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle window close

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        # --- Add Show Password Checkbutton ---
        self.show_password_var = tk.BooleanVar()
        self.show_password_checkbutton = tk.Checkbutton(
            self,
            text="Show Password",
            variable=self.show_password_var,
            command=self._toggle_password_visibility # Connect the command
        )
        self.show_password_checkbutton.pack(pady=2) # Adjusted padding for visual spacing
        # --- End of addition ---

        self.login_button = tk.Button(self, text="Login", command=self.attempt_login)
        self.login_button.pack(pady=10)

        # Pre-fill for quick testing (remove in production)
        self.username_entry.insert(0, Config.DEFAULT_ADMIN_USERNAME)
        self.password_entry.insert(0, Config.DEFAULT_ADMIN_PASSWORD)

        # Instructions Button
        self.instructions_button = tk.Button(self, text="Instructions for Use", command=self.show_instructions)
        self.instructions_button.pack(pady=5)

        # Logo Placeholder
        self.logo_label = tk.Label(self, text="Davinci Logo Placeholder", font=("Arial", 10, "italic"), fg="grey")
        self.logo_label.pack(pady=10, side="bottom")

    def show_instructions(self):
        messagebox.showinfo("Instructions for Use",
                            "User Manual/Instructions Content Here.\n\n"
                            "1. Enter your username and password.\n"
                            "2. Click Login.\n"
                            "3. If login is successful, the main application will open.\n"
                            "4. For issues, contact support.",
                            parent=self)

    def attempt_login(self):
        self.login_button.config(state="disabled") # Prevent double click
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        role = self.app.user_manager.authenticate_user(username, password)
        if role:
            self.app.current_user_role = role
            self.app.current_username = username
            logger.info(f"User '{username}' logged in successfully.")

            # Flashing success message
            success_window = tk.Toplevel(self)
            success_window.title("Success")
            success_window.geometry("250x100")
            success_window.resizable(False, False)

            # Center the success window relative to the login window
            # x = self.winfo_x() + (self.winfo_width() - 250) // 2
            # y = self.winfo_y() + (self.winfo_height() - 100) // 2
            # success_window.geometry(f"+{x}+{y}")

            # Simpler centering: center on screen, or let window manager decide
            # For now, let window manager place it, or use transient + grab_set to keep focus

            tk.Label(success_window, text=f"Welcome, {username}!\nLogin Successful!", font=("Arial", 12), pady=10).pack(expand=True)
            success_window.transient(self.master) # Keep it on top of the main app that will appear
            success_window.grab_set() # Make it modal briefly

            # Automatically close the success window and then the login window
            success_window.after(1500, lambda: [
                success_window.destroy(),
                self.destroy(), # Close login window
                self.master.deiconify(), # Show main window
                self.app.show_main_application() # Update main app GUI
            ])
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.", parent=self) # Make error dialog child of login window
            logger.warning(f"Login attempt failed for username: {username}")
            self.login_button.config(state="normal") # Re-enable login button on failure

    def _toggle_password_visibility(self):
        """Toggles the visibility of the password in the password entry field."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
            self.master.destroy() # Close the main Tkinter root window

# Import BaseModuleFrame from its new location
from gui_frames.base_frame import BaseModuleFrame

# Import all other specific frame classes from the gui_frames package
from gui_frames.integration_data_processing_frame import IntegrationDataProcessingModuleFrame
from gui_frames.reporting_closeout_frame import ReportingCloseoutModuleFrame
from gui_frames.scheduling_frame import SchedulingModuleFrame
from gui_frames.welcome_frame import WelcomeFrame
from gui_frames.project_startup_frame import ProjectStartupModuleFrame
from gui_frames.execution_management_frame import ExecutionManagementModuleFrame
from gui_frames.monitoring_control_frame import MonitoringControlModuleFrame
from gui_frames.daily_log_frame import DailyLogModuleFrame
from gui_frames.user_management_frame import UserManagementModuleFrame

# Note: The definitions for IntegrationModuleFrame, DataProcessingModuleFrame,
# ReportingModuleFrame, and CloseoutModuleFrame are intentionally removed
# from this file and NOT imported from gui_frames if they are fully obsolete.
# If their placeholder files in gui_frames are still referenced by module_buttons_data,
# they would need to be imported. However, the plan is to remove them from module_buttons_data.

# --- All Frame Class Definitions Below This Line Are Now MOVED to gui_frames/ ---
# --- The comments below are just placeholders indicating where they were. ---

# class IntegrationDataProcessingModuleFrame(BaseModuleFrame): # MOVED
# class ReportingCloseoutModuleFrame(BaseModuleFrame): # MOVED
# class SchedulingModuleFrame(BaseModuleFrame): # MOVED
# class WelcomeFrame(BaseModuleFrame): # MOVED
# class ProjectStartupModuleFrame(BaseModuleFrame): # MOVED
# class ExecutionManagementModuleFrame(BaseModuleFrame): # MOVED
# class MonitoringControlModuleFrame(BaseModuleFrame): # MOVED
# class DailyLogModuleFrame(BaseModuleFrame): # MOVED
# class UserManagementModuleFrame(BaseModuleFrame): # MOVED


class PurchasingLogisticsModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.app = app # Store the app instance
        self.module_instance = module_instance # Should be ProjectStartup instance

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Purchasing & Logistics Management", style='Header.TLabel').pack(pady=10)

        # --- Material Request Section ---
        request_frame = ttk.LabelFrame(self, text="Request Material (Internal Log)")
        request_frame.pack(padx=10, pady=10, fill="x")

        # Project ID (Optional, could be linked to active project)
        ttk.Label(request_frame, text="Project ID (Optional):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.req_project_id_entry = ttk.Entry(request_frame, width=40)
        self.req_project_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Material Description
        ttk.Label(request_frame, text="Material Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.req_material_desc_entry = ttk.Entry(request_frame, width=40)
        self.req_material_desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Quantity Requested
        ttk.Label(request_frame, text="Quantity Requested:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.req_quantity_entry = ttk.Entry(request_frame, width=40)
        self.req_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Unit of Measure
        ttk.Label(request_frame, text="Unit of Measure:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.req_uom_entry = ttk.Entry(request_frame, width=40)
        self.req_uom_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Urgency Level
        ttk.Label(request_frame, text="Urgency (Standard, Urgent, Critical):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.req_urgency_combobox = ttk.Combobox(request_frame, values=['Standard', 'Urgent', 'Critical'], width=38)
        self.req_urgency_combobox.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.req_urgency_combobox.set('Standard')

        # Required By Date
        ttk.Label(request_frame, text="Required By Date (YYYY-MM-DD):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.req_date_entry = ttk.Entry(request_frame, width=40)
        self.req_date_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Notes
        ttk.Label(request_frame, text="Notes:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.req_notes_entry = ttk.Entry(request_frame, width=40)
        self.req_notes_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        submit_req_button = ttk.Button(request_frame, text="Submit Material Request", command=self.submit_material_request)
        submit_req_button.grid(row=7, column=0, columnspan=2, pady=10)

        # --- Display Area for Pending Requests ---
        display_frame = ttk.LabelFrame(self, text="Pending Internal Material Requests (Purchasing_Log)")
        display_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.requests_tree = ttk.Treeview(display_frame, columns=("LogID", "ProjectID", "Material", "Qty", "UoM", "Urgency", "ReqDate", "Status", "Created"), show="headings")
        self.requests_tree.heading("LogID", text="Log ID")
        self.requests_tree.heading("ProjectID", text="Project ID")
        self.requests_tree.heading("Material", text="Material Desc.")
        self.requests_tree.heading("Qty", text="Qty Req.")
        self.requests_tree.heading("UoM", text="UoM")
        self.requests_tree.heading("Urgency", text="Urgency")
        self.requests_tree.heading("ReqDate", text="Required Date")
        self.requests_tree.heading("Status", text="Status")
        self.requests_tree.heading("Created", text="Date Created")

        self.requests_tree.column("LogID", width=60, anchor="center")
        self.requests_tree.column("ProjectID", width=70, anchor="center")
        self.requests_tree.column("Material", width=200)
        self.requests_tree.column("Qty", width=80, anchor="e")
        self.requests_tree.column("UoM", width=70)
        self.requests_tree.column("Urgency", width=80)
        self.requests_tree.column("ReqDate", width=100)
        self.requests_tree.column("Status", width=100)
        self.requests_tree.column("Created", width=120)

        vsb = ttk.Scrollbar(display_frame, orient="vertical", command=self.requests_tree.yview)
        hsb = ttk.Scrollbar(display_frame, orient="horizontal", command=self.requests_tree.xview)
        self.requests_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.requests_tree.pack(fill="both", expand=True)

        refresh_button = ttk.Button(display_frame, text="Refresh List", command=self.load_pending_requests)
        refresh_button.pack(pady=5)

        self.load_pending_requests() # Initial load

    def submit_material_request(self):
        project_id_str = self.req_project_id_entry.get().strip()
        project_id = int(project_id_str) if project_id_str else self.app.active_project_id # Use active project ID if field is empty

        material_description = self.req_material_desc_entry.get().strip()
        quantity_str = self.req_quantity_entry.get().strip()
        unit_of_measure = self.req_uom_entry.get().strip()
        urgency_level = self.req_urgency_combobox.get().strip()
        required_by_date = self.req_date_entry.get().strip() if self.req_date_entry.get().strip() else None
        notes = self.req_notes_entry.get().strip()

        if not material_description or not quantity_str:
            messagebox.showerror("Input Error", "Material Description and Quantity are required.", parent=self)
            return

        try:
            quantity_requested = float(quantity_str)
        except ValueError:
            messagebox.showerror("Input Error", "Quantity must be a valid number.", parent=self)
            return

        # Get current user's EmployeeID
        requested_by_employee_id = self.app.user_manager.get_user_id_by_username(self.app.current_username)
        if requested_by_employee_id is None:
            logger.warning(f"Could not find EmployeeID for username {self.app.current_username}. Defaulting to 1.")
            requested_by_employee_id = 1 # Fallback

        if self.module_instance and hasattr(self.module_instance, 'add_material_request'):
            success, msg, log_id = self.module_instance.add_material_request(
                project_id=project_id,
                requested_by_employee_id=requested_by_employee_id,
                material_description=material_description,
                quantity_requested=quantity_requested,
                unit_of_measure=unit_of_measure,
                urgency_level=urgency_level,
                required_by_date=required_by_date,
                notes=notes
            )
            if success:
                messagebox.showinfo("Success", f"{msg} (Log ID: {log_id})", parent=self)
                self.load_pending_requests() # Refresh list
                # Clear input fields
                self.req_project_id_entry.delete(0, tk.END)
                self.req_material_desc_entry.delete(0, tk.END)
                self.req_quantity_entry.delete(0, tk.END)
                self.req_uom_entry.delete(0, tk.END)
                self.req_urgency_combobox.set('Standard')
                self.req_date_entry.delete(0, tk.END)
                self.req_notes_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", msg, parent=self)
        else:
            messagebox.showerror("Error", "Project Startup module not available for material request.", parent=self)
            logger.error("ProjectStartup module instance or add_material_request method not found in PurchasingLogisticsModuleFrame.")

    def load_pending_requests(self):
        for i in self.requests_tree.get_children():
            self.requests_tree.delete(i)

        # Fetch data from Purchasing_Log table (status != 'Received Full' or 'Cancelled')
        # This requires a method in a backend module, e.g., project_startup or a new purchasing module.
        # For now, we'll assume db_manager can be used directly for simplicity, though not ideal.
        query = "SELECT InternalLogID, ProjectID, MaterialDescription, QuantityRequested, UnitOfMeasure, UrgencyLevel, RequiredByDate, Status, DateCreated FROM Purchasing_Log WHERE Status NOT IN ('Received Full', 'Cancelled') ORDER BY DateCreated DESC"
        try:
            requests = db_manager.execute_query(query, fetch_all=True)
            if requests:
                for req in requests:
                    self.requests_tree.insert("", "end", values=(
                        req['InternalLogID'],
                        req['ProjectID'] if req['ProjectID'] is not None else "N/A",
                        req['MaterialDescription'],
                        req['QuantityRequested'],
                        req['UnitOfMeasure'],
                        req['UrgencyLevel'],
                        req['RequiredByDate'] if req['RequiredByDate'] else "N/A",
                        req['Status'],
                        req['DateCreated']
                    ))
        except Exception as e:
            logger.error(f"Error loading pending material requests: {e}", exc_info=True)
            messagebox.showerror("Load Error", f"Failed to load pending requests: {e}", parent=self)

    def on_active_project_changed(self):
        """Called when the global active project changes."""
        logger.info("PurchasingLogisticsModuleFrame: Active project changed. Refreshing relevant views if needed.")
        if self.app.active_project_id:
            self.req_project_id_entry.delete(0, tk.END)
            self.req_project_id_entry.insert(0, str(self.app.active_project_id))
        else:
            self.req_project_id_entry.delete(0, tk.END)
        self.load_pending_requests() # Refresh list based on potentially new global context


class ProductionPrefabModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.app = app
        self.module_instance = module_instance # Should be ProjectStartup instance
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Production & Prefabrication Management", style='Header.TLabel').pack(pady=10)

        # --- Create Production Order Section ---
        order_frame = ttk.LabelFrame(self, text="Create Production Order")
        order_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(order_frame, text="Assembly ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prod_assembly_id_entry = ttk.Entry(order_frame, width=40)
        self.prod_assembly_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Project ID (Optional):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.prod_project_id_entry = ttk.Entry(order_frame, width=40)
        self.prod_project_id_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Quantity to Produce:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.prod_quantity_entry = ttk.Entry(order_frame, width=40)
        self.prod_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Assigned To Employee ID (Optional):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.prod_assigned_emp_id_entry = ttk.Entry(order_frame, width=40)
        self.prod_assigned_emp_id_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Start Date (YYYY-MM-DD, Optional):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.prod_start_date_entry = ttk.Entry(order_frame, width=40)
        self.prod_start_date_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Completion Date (YYYY-MM-DD, Optional):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.prod_completion_date_entry = ttk.Entry(order_frame, width=40)
        self.prod_completion_date_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Notes:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.prod_notes_entry = ttk.Entry(order_frame, width=40)
        self.prod_notes_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        submit_order_button = ttk.Button(order_frame, text="Create Production Order", command=self.submit_production_order)
        submit_order_button.grid(row=7, column=0, columnspan=2, pady=10)

        # --- Display Area for Active Production Orders ---
        prod_display_frame = ttk.LabelFrame(self, text="Active Production Orders (Production_Assembly_Tracking)")
        prod_display_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.orders_tree = ttk.Treeview(prod_display_frame, columns=("ProdID", "AssemblyID", "ProjectID", "Qty", "Status", "StartDate", "EndDate", "AssignedTo", "Created"), show="headings")
        self.orders_tree.heading("ProdID", text="Prod ID")
        self.orders_tree.heading("AssemblyID", text="Assembly ID")
        self.orders_tree.heading("ProjectID", text="Project ID")
        self.orders_tree.heading("Qty", text="Qty")
        self.orders_tree.heading("Status", text="Status")
        self.orders_tree.heading("StartDate", text="Start Date")
        self.orders_tree.heading("EndDate", text="End Date")
        self.orders_tree.heading("AssignedTo", text="Assigned Emp ID")
        self.orders_tree.heading("Created", text="Date Created")

        self.orders_tree.column("ProdID", width=60, anchor="center")
        self.orders_tree.column("AssemblyID", width=80, anchor="center")
        self.orders_tree.column("ProjectID", width=70, anchor="center")
        self.orders_tree.column("Qty", width=60, anchor="e")
        self.orders_tree.column("Status", width=100)
        self.orders_tree.column("StartDate", width=100)
        self.orders_tree.column("EndDate", width=100)
        self.orders_tree.column("AssignedTo", width=100)
        self.orders_tree.column("Created", width=120)

        prod_vsb = ttk.Scrollbar(prod_display_frame, orient="vertical", command=self.orders_tree.yview)
        prod_hsb = ttk.Scrollbar(prod_display_frame, orient="horizontal", command=self.orders_tree.xview)
        self.orders_tree.configure(yscrollcommand=prod_vsb.set, xscrollcommand=prod_hsb.set)

        prod_vsb.pack(side='right', fill='y')
        prod_hsb.pack(side='bottom', fill='x')
        self.orders_tree.pack(fill="both", expand=True)

        prod_refresh_button = ttk.Button(prod_display_frame, text="Refresh List", command=self.load_production_orders)
        prod_refresh_button.pack(pady=5)

        self.load_production_orders() # Initial load

    def submit_production_order(self):
        assembly_id_str = self.prod_assembly_id_entry.get().strip()
        project_id_str = self.prod_project_id_entry.get().strip()
        quantity_str = self.prod_quantity_entry.get().strip()
        assigned_emp_id_str = self.prod_assigned_emp_id_entry.get().strip()
        start_date = self.prod_start_date_entry.get().strip() if self.prod_start_date_entry.get().strip() else None
        completion_date = self.prod_completion_date_entry.get().strip() if self.prod_completion_date_entry.get().strip() else None
        notes = self.prod_notes_entry.get().strip()

        if not assembly_id_str or not quantity_str:
            messagebox.showerror("Input Error", "Assembly ID and Quantity are required.", parent=self)
            return

        try:
            assembly_id = int(assembly_id_str)
            quantity_to_produce = float(quantity_str)
            project_id = int(project_id_str) if project_id_str else self.app.active_project_id

            assigned_to_employee_id = None
            if assigned_emp_id_str:
                assigned_to_employee_id = int(assigned_emp_id_str)
            else: # Default to current user if field is empty
                current_user_id = self.app.user_manager.get_user_id_by_username(self.app.current_username)
                assigned_to_employee_id = current_user_id if current_user_id is not None else 1 # Fallback to 1
                logger.info(f"AssignedToEmployeeID not provided for production order, defaulting to current user ID: {assigned_to_employee_id}")

        except ValueError:
            messagebox.showerror("Input Error", "Assembly ID, Project ID (if provided), Quantity, and Assigned Employee ID (if provided) must be valid numbers.", parent=self)
            return

        if self.module_instance and hasattr(self.module_instance, 'create_production_assembly_order'):
            success, msg, prod_id = self.module_instance.create_production_assembly_order(
                assembly_id=assembly_id,
                project_id=project_id,
                quantity_to_produce=quantity_to_produce,
                assigned_to_employee_id=assigned_to_employee_id,
                start_date=start_date,
                completion_date=completion_date,
                notes=notes
            )
            if success:
                messagebox.showinfo("Success", f"{msg} (Production ID: {prod_id})", parent=self)
                self.load_production_orders() # Refresh list
                # Clear input fields
                self.prod_assembly_id_entry.delete(0, tk.END)
                self.prod_project_id_entry.delete(0, tk.END)
                self.prod_quantity_entry.delete(0, tk.END)
                self.prod_assigned_emp_id_entry.delete(0, tk.END)
                self.prod_start_date_entry.delete(0, tk.END)
                self.prod_completion_date_entry.delete(0, tk.END)
                self.prod_notes_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", msg, parent=self)
        else:
            messagebox.showerror("Error", "Project Startup module not available for production order.", parent=self)
            logger.error("ProjectStartup module instance or create_production_assembly_order method not found in ProductionPrefabModuleFrame.")

    def load_production_orders(self):
        for i in self.orders_tree.get_children():
            self.orders_tree.delete(i)

        query = "SELECT ProductionID, AssemblyID, ProjectID, QuantityToProduce, Status, StartDate, CompletionDate, AssignedToEmployeeID, DateCreated FROM Production_Assembly_Tracking WHERE Status NOT IN ('Completed', 'Shipped', 'Cancelled') ORDER BY DateCreated DESC"
        try:
            orders = db_manager.execute_query(query, fetch_all=True)
            if orders:
                for order in orders:
                    self.orders_tree.insert("", "end", values=(
                        order['ProductionID'],
                        order['AssemblyID'],
                        order['ProjectID'] if order['ProjectID'] is not None else "N/A",
                        order['QuantityToProduce'],
                        order['Status'],
                        order['StartDate'] if order['StartDate'] else "N/A",
                        order['CompletionDate'] if order['CompletionDate'] else "N/A",
                        order['AssignedToEmployeeID'] if order['AssignedToEmployeeID'] is not None else "N/A",
                        order['DateCreated']
                    ))
        except Exception as e:
            logger.error(f"Error loading production orders: {e}", exc_info=True)
            messagebox.showerror("Load Error", f"Failed to load production orders: {e}", parent=self)

    def on_active_project_changed(self):
        """Called when the global active project changes."""
        logger.info("ProductionPrefabModuleFrame: Active project changed. Refreshing relevant views if needed.")
        if self.app.active_project_id:
            self.prod_project_id_entry.delete(0, tk.END)
            self.prod_project_id_entry.insert(0, str(self.app.active_project_id))
        else:
            self.prod_project_id_entry.delete(0, tk.END)
        self.load_production_orders()


class PurchasingLogisticsModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.app = app # Store the app instance
        self.module_instance = module_instance # Should be ProjectStartup instance

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Purchasing & Logistics Management", style='Header.TLabel').pack(pady=10)

        # --- Material Request Section ---
        request_frame = ttk.LabelFrame(self, text="Request Material (Internal Log)")
        request_frame.pack(padx=10, pady=10, fill="x")

        # Project ID (Optional, could be linked to active project)
        ttk.Label(request_frame, text="Project ID (Optional):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.req_project_id_entry = ttk.Entry(request_frame, width=40)
        self.req_project_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Material Description
        ttk.Label(request_frame, text="Material Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.req_material_desc_entry = ttk.Entry(request_frame, width=40)
        self.req_material_desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Quantity Requested
        ttk.Label(request_frame, text="Quantity Requested:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.req_quantity_entry = ttk.Entry(request_frame, width=40)
        self.req_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Unit of Measure
        ttk.Label(request_frame, text="Unit of Measure:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.req_uom_entry = ttk.Entry(request_frame, width=40)
        self.req_uom_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Urgency Level
        ttk.Label(request_frame, text="Urgency (Standard, Urgent, Critical):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.req_urgency_combobox = ttk.Combobox(request_frame, values=['Standard', 'Urgent', 'Critical'], width=38)
        self.req_urgency_combobox.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.req_urgency_combobox.set('Standard')

        # Required By Date
        ttk.Label(request_frame, text="Required By Date (YYYY-MM-DD):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.req_date_entry = ttk.Entry(request_frame, width=40)
        self.req_date_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Notes
        ttk.Label(request_frame, text="Notes:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.req_notes_entry = ttk.Entry(request_frame, width=40)
        self.req_notes_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        submit_req_button = ttk.Button(request_frame, text="Submit Material Request", command=self.submit_material_request)
        submit_req_button.grid(row=7, column=0, columnspan=2, pady=10)

        # --- Display Area for Pending Requests ---
        display_frame = ttk.LabelFrame(self, text="Pending Internal Material Requests (Purchasing_Log)")
        display_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.requests_tree = ttk.Treeview(display_frame, columns=("LogID", "ProjectID", "Material", "Qty", "UoM", "Urgency", "ReqDate", "Status", "Created"), show="headings")
        self.requests_tree.heading("LogID", text="Log ID")
        self.requests_tree.heading("ProjectID", text="Project ID")
        self.requests_tree.heading("Material", text="Material Desc.")
        self.requests_tree.heading("Qty", text="Qty Req.")
        self.requests_tree.heading("UoM", text="UoM")
        self.requests_tree.heading("Urgency", text="Urgency")
        self.requests_tree.heading("ReqDate", text="Required Date")
        self.requests_tree.heading("Status", text="Status")
        self.requests_tree.heading("Created", text="Date Created")

        self.requests_tree.column("LogID", width=60, anchor="center")
        self.requests_tree.column("ProjectID", width=70, anchor="center")
        self.requests_tree.column("Material", width=200)
        self.requests_tree.column("Qty", width=80, anchor="e")
        self.requests_tree.column("UoM", width=70)
        self.requests_tree.column("Urgency", width=80)
        self.requests_tree.column("ReqDate", width=100)
        self.requests_tree.column("Status", width=100)
        self.requests_tree.column("Created", width=120)

        vsb = ttk.Scrollbar(display_frame, orient="vertical", command=self.requests_tree.yview)
        hsb = ttk.Scrollbar(display_frame, orient="horizontal", command=self.requests_tree.xview)
        self.requests_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.requests_tree.pack(fill="both", expand=True)

        refresh_button = ttk.Button(display_frame, text="Refresh List", command=self.load_pending_requests)
        refresh_button.pack(pady=5)

        self.load_pending_requests() # Initial load

    def submit_material_request(self):
        project_id_str = self.req_project_id_entry.get().strip()
        project_id = int(project_id_str) if project_id_str else self.app.active_project_id # Use active project ID if field is empty

        material_description = self.req_material_desc_entry.get().strip()
        quantity_str = self.req_quantity_entry.get().strip()
        unit_of_measure = self.req_uom_entry.get().strip()
        urgency_level = self.req_urgency_combobox.get().strip()
        required_by_date = self.req_date_entry.get().strip() if self.req_date_entry.get().strip() else None
        notes = self.req_notes_entry.get().strip()

        if not material_description or not quantity_str:
            messagebox.showerror("Input Error", "Material Description and Quantity are required.", parent=self)
            return

        try:
            quantity_requested = float(quantity_str)
        except ValueError:
            messagebox.showerror("Input Error", "Quantity must be a valid number.", parent=self)
            return

        # Get current user's EmployeeID
        requested_by_employee_id = self.app.user_manager.get_user_id_by_username(self.app.current_username)
        if requested_by_employee_id is None:
            logger.warning(f"Could not find EmployeeID for username {self.app.current_username}. Defaulting to 1.")
            requested_by_employee_id = 1 # Fallback

        if self.module_instance and hasattr(self.module_instance, 'add_material_request'):
            success, msg, log_id = self.module_instance.add_material_request(
                project_id=project_id,
                requested_by_employee_id=requested_by_employee_id,
                material_description=material_description,
                quantity_requested=quantity_requested,
                unit_of_measure=unit_of_measure,
                urgency_level=urgency_level,
                required_by_date=required_by_date,
                notes=notes
            )
            if success:
                messagebox.showinfo("Success", f"{msg} (Log ID: {log_id})", parent=self)
                self.load_pending_requests() # Refresh list
                # Clear input fields
                self.req_project_id_entry.delete(0, tk.END)
                self.req_material_desc_entry.delete(0, tk.END)
                self.req_quantity_entry.delete(0, tk.END)
                self.req_uom_entry.delete(0, tk.END)
                self.req_urgency_combobox.set('Standard')
                self.req_date_entry.delete(0, tk.END)
                self.req_notes_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", msg, parent=self)
        else:
            messagebox.showerror("Error", "Project Startup module not available for material request.", parent=self)
            logger.error("ProjectStartup module instance or add_material_request method not found in PurchasingLogisticsModuleFrame.")

    def load_pending_requests(self):
        for i in self.requests_tree.get_children():
            self.requests_tree.delete(i)

        # Fetch data from Purchasing_Log table (status != 'Received Full' or 'Cancelled')
        # This requires a method in a backend module, e.g., project_startup or a new purchasing module.
        # For now, we'll assume db_manager can be used directly for simplicity, though not ideal.
        query = "SELECT InternalLogID, ProjectID, MaterialDescription, QuantityRequested, UnitOfMeasure, UrgencyLevel, RequiredByDate, Status, DateCreated FROM Purchasing_Log WHERE Status NOT IN ('Received Full', 'Cancelled') ORDER BY DateCreated DESC"
        try:
            requests = db_manager.execute_query(query, fetch_all=True)
            if requests:
                for req in requests:
                    self.requests_tree.insert("", "end", values=(
                        req['InternalLogID'],
                        req['ProjectID'] if req['ProjectID'] is not None else "N/A",
                        req['MaterialDescription'],
                        req['QuantityRequested'],
                        req['UnitOfMeasure'],
                        req['UrgencyLevel'],
                        req['RequiredByDate'] if req['RequiredByDate'] else "N/A",
                        req['Status'],
                        req['DateCreated']
                    ))
        except Exception as e:
            logger.error(f"Error loading pending material requests: {e}", exc_info=True)
            messagebox.showerror("Load Error", f"Failed to load pending requests: {e}", parent=self)

    def on_active_project_changed(self):
        """Called when the global active project changes."""
        logger.info("PurchasingLogisticsModuleFrame: Active project changed. Refreshing relevant views if needed.")
        if self.app.active_project_id:
            self.req_project_id_entry.delete(0, tk.END)
            self.req_project_id_entry.insert(0, str(self.app.active_project_id))
        else:
            self.req_project_id_entry.delete(0, tk.END)
        self.load_pending_requests() # Refresh list based on potentially new global context


class ProductionPrefabModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.app = app
        self.module_instance = module_instance # Should be ProjectStartup instance
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Production & Prefabrication Management", style='Header.TLabel').pack(pady=10)

        # --- Create Production Order Section ---
        order_frame = ttk.LabelFrame(self, text="Create Production Order")
        order_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(order_frame, text="Assembly ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prod_assembly_id_entry = ttk.Entry(order_frame, width=40)
        self.prod_assembly_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Project ID (Optional):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.prod_project_id_entry = ttk.Entry(order_frame, width=40)
        self.prod_project_id_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Quantity to Produce:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.prod_quantity_entry = ttk.Entry(order_frame, width=40)
        self.prod_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Assigned To Employee ID (Optional):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.prod_assigned_emp_id_entry = ttk.Entry(order_frame, width=40)
        self.prod_assigned_emp_id_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Start Date (YYYY-MM-DD, Optional):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.prod_start_date_entry = ttk.Entry(order_frame, width=40)
        self.prod_start_date_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Completion Date (YYYY-MM-DD, Optional):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.prod_completion_date_entry = ttk.Entry(order_frame, width=40)
        self.prod_completion_date_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Notes:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.prod_notes_entry = ttk.Entry(order_frame, width=40)
        self.prod_notes_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        submit_order_button = ttk.Button(order_frame, text="Create Production Order", command=self.submit_production_order)
        submit_order_button.grid(row=7, column=0, columnspan=2, pady=10)

        # --- Display Area for Active Production Orders ---
        prod_display_frame = ttk.LabelFrame(self, text="Active Production Orders (Production_Assembly_Tracking)")
        prod_display_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.orders_tree = ttk.Treeview(prod_display_frame, columns=("ProdID", "AssemblyID", "ProjectID", "Qty", "Status", "StartDate", "EndDate", "AssignedTo", "Created"), show="headings")
        self.orders_tree.heading("ProdID", text="Prod ID")
        self.orders_tree.heading("AssemblyID", text="Assembly ID")
        self.orders_tree.heading("ProjectID", text="Project ID")
        self.orders_tree.heading("Qty", text="Qty")
        self.orders_tree.heading("Status", text="Status")
        self.orders_tree.heading("StartDate", text="Start Date")
        self.orders_tree.heading("EndDate", text="End Date")
        self.orders_tree.heading("AssignedTo", text="Assigned Emp ID")
        self.orders_tree.heading("Created", text="Date Created")

        self.orders_tree.column("ProdID", width=60, anchor="center")
        self.orders_tree.column("AssemblyID", width=80, anchor="center")
        self.orders_tree.column("ProjectID", width=70, anchor="center")
        self.orders_tree.column("Qty", width=60, anchor="e")
        self.orders_tree.column("Status", width=100)
        self.orders_tree.column("StartDate", width=100)
        self.orders_tree.column("EndDate", width=100)
        self.orders_tree.column("AssignedTo", width=100)
        self.orders_tree.column("Created", width=120)

        prod_vsb = ttk.Scrollbar(prod_display_frame, orient="vertical", command=self.orders_tree.yview)
        prod_hsb = ttk.Scrollbar(prod_display_frame, orient="horizontal", command=self.orders_tree.xview)
        self.orders_tree.configure(yscrollcommand=prod_vsb.set, xscrollcommand=prod_hsb.set)

        prod_vsb.pack(side='right', fill='y')
        prod_hsb.pack(side='bottom', fill='x')
        self.orders_tree.pack(fill="both", expand=True)

        prod_refresh_button = ttk.Button(prod_display_frame, text="Refresh List", command=self.load_production_orders)
        prod_refresh_button.pack(pady=5)

        self.load_production_orders() # Initial load

    def submit_production_order(self):
        assembly_id_str = self.prod_assembly_id_entry.get().strip()
        project_id_str = self.prod_project_id_entry.get().strip()
        quantity_str = self.prod_quantity_entry.get().strip()
        assigned_emp_id_str = self.prod_assigned_emp_id_entry.get().strip()
        start_date = self.prod_start_date_entry.get().strip() if self.prod_start_date_entry.get().strip() else None
        completion_date = self.prod_completion_date_entry.get().strip() if self.prod_completion_date_entry.get().strip() else None
        notes = self.prod_notes_entry.get().strip()

        if not assembly_id_str or not quantity_str:
            messagebox.showerror("Input Error", "Assembly ID and Quantity are required.", parent=self)
            return

        try:
            assembly_id = int(assembly_id_str)
            quantity_to_produce = float(quantity_str)
            project_id = int(project_id_str) if project_id_str else self.app.active_project_id

            assigned_to_employee_id = None
            if assigned_emp_id_str:
                assigned_to_employee_id = int(assigned_emp_id_str)
            else: # Default to current user if field is empty
                current_user_id = self.app.user_manager.get_user_id_by_username(self.app.current_username)
                assigned_to_employee_id = current_user_id if current_user_id is not None else 1 # Fallback to 1
                logger.info(f"AssignedToEmployeeID not provided for production order, defaulting to current user ID: {assigned_to_employee_id}")

        except ValueError:
            messagebox.showerror("Input Error", "Assembly ID, Project ID (if provided), Quantity, and Assigned Employee ID (if provided) must be valid numbers.", parent=self)
            return

        if self.module_instance and hasattr(self.module_instance, 'create_production_assembly_order'):
            success, msg, prod_id = self.module_instance.create_production_assembly_order(
                assembly_id=assembly_id,
                project_id=project_id,
                quantity_to_produce=quantity_to_produce,
                assigned_to_employee_id=assigned_to_employee_id,
                start_date=start_date,
                completion_date=completion_date,
                notes=notes
            )
            if success:
                messagebox.showinfo("Success", f"{msg} (Production ID: {prod_id})", parent=self)
                self.load_production_orders() # Refresh list
                # Clear input fields
                self.prod_assembly_id_entry.delete(0, tk.END)
                self.prod_project_id_entry.delete(0, tk.END)
                self.prod_quantity_entry.delete(0, tk.END)
                self.prod_assigned_emp_id_entry.delete(0, tk.END)
                self.prod_start_date_entry.delete(0, tk.END)
                self.prod_completion_date_entry.delete(0, tk.END)
                self.prod_notes_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", msg, parent=self)
        else:
            messagebox.showerror("Error", "Project Startup module not available for production order.", parent=self)
            logger.error("ProjectStartup module instance or create_production_assembly_order method not found in ProductionPrefabModuleFrame.")

    def load_production_orders(self):
        for i in self.orders_tree.get_children():
            self.orders_tree.delete(i)

        query = "SELECT ProductionID, AssemblyID, ProjectID, QuantityToProduce, Status, StartDate, CompletionDate, AssignedToEmployeeID, DateCreated FROM Production_Assembly_Tracking WHERE Status NOT IN ('Completed', 'Shipped', 'Cancelled') ORDER BY DateCreated DESC"
        try:
            orders = db_manager.execute_query(query, fetch_all=True)
            if orders:
                for order in orders:
                    self.orders_tree.insert("", "end", values=(
                        order['ProductionID'],
                        order['AssemblyID'],
                        order['ProjectID'] if order['ProjectID'] is not None else "N/A",
                        order['QuantityToProduce'],
                        order['Status'],
                        order['StartDate'] if order['StartDate'] else "N/A",
                        order['CompletionDate'] if order['CompletionDate'] else "N/A",
                        order['AssignedToEmployeeID'] if order['AssignedToEmployeeID'] is not None else "N/A",
                        order['DateCreated']
                    ))
        except Exception as e:
            logger.error(f"Error loading production orders: {e}", exc_info=True)
            messagebox.showerror("Load Error", f"Failed to load production orders: {e}", parent=self)

    def on_active_project_changed(self):
        """Called when the global active project changes."""
        logger.info("ProductionPrefabModuleFrame: Active project changed. Refreshing relevant views if needed.")
        if self.app.active_project_id:
            self.prod_project_id_entry.delete(0, tk.END)
            self.prod_project_id_entry.insert(0, str(self.app.active_project_id))
        else:
            self.prod_project_id_entry.delete(0, tk.END)
        self.load_production_orders()


class PurchasingLogisticsModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.app = app # Store the app instance
        self.module_instance = module_instance # Should be ProjectStartup instance

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Purchasing & Logistics Management", style='Header.TLabel').pack(pady=10)

        # --- Material Request Section ---
        request_frame = ttk.LabelFrame(self, text="Request Material (Internal Log)")
        request_frame.pack(padx=10, pady=10, fill="x")

        # Project ID (Optional, could be linked to active project)
        ttk.Label(request_frame, text="Project ID (Optional):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.req_project_id_entry = ttk.Entry(request_frame, width=40)
        self.req_project_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Material Description
        ttk.Label(request_frame, text="Material Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.req_material_desc_entry = ttk.Entry(request_frame, width=40)
        self.req_material_desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Quantity Requested
        ttk.Label(request_frame, text="Quantity Requested:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.req_quantity_entry = ttk.Entry(request_frame, width=40)
        self.req_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Unit of Measure
        ttk.Label(request_frame, text="Unit of Measure:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.req_uom_entry = ttk.Entry(request_frame, width=40)
        self.req_uom_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Urgency Level
        ttk.Label(request_frame, text="Urgency (Standard, Urgent, Critical):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.req_urgency_combobox = ttk.Combobox(request_frame, values=['Standard', 'Urgent', 'Critical'], width=38)
        self.req_urgency_combobox.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.req_urgency_combobox.set('Standard')

        # Required By Date
        ttk.Label(request_frame, text="Required By Date (YYYY-MM-DD):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.req_date_entry = ttk.Entry(request_frame, width=40)
        self.req_date_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Notes
        ttk.Label(request_frame, text="Notes:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.req_notes_entry = ttk.Entry(request_frame, width=40)
        self.req_notes_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        submit_req_button = ttk.Button(request_frame, text="Submit Material Request", command=self.submit_material_request)
        submit_req_button.grid(row=7, column=0, columnspan=2, pady=10)

        # --- Display Area for Pending Requests ---
        display_frame = ttk.LabelFrame(self, text="Pending Internal Material Requests (Purchasing_Log)")
        display_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.requests_tree = ttk.Treeview(display_frame, columns=("LogID", "ProjectID", "Material", "Qty", "UoM", "Urgency", "ReqDate", "Status", "Created"), show="headings")
        self.requests_tree.heading("LogID", text="Log ID")
        self.requests_tree.heading("ProjectID", text="Project ID")
        self.requests_tree.heading("Material", text="Material Desc.")
        self.requests_tree.heading("Qty", text="Qty Req.")
        self.requests_tree.heading("UoM", text="UoM")
        self.requests_tree.heading("Urgency", text="Urgency")
        self.requests_tree.heading("ReqDate", text="Required Date")
        self.requests_tree.heading("Status", text="Status")
        self.requests_tree.heading("Created", text="Date Created")

        self.requests_tree.column("LogID", width=60, anchor="center")
        self.requests_tree.column("ProjectID", width=70, anchor="center")
        self.requests_tree.column("Material", width=200)
        self.requests_tree.column("Qty", width=80, anchor="e")
        self.requests_tree.column("UoM", width=70)
        self.requests_tree.column("Urgency", width=80)
        self.requests_tree.column("ReqDate", width=100)
        self.requests_tree.column("Status", width=100)
        self.requests_tree.column("Created", width=120)

        vsb = ttk.Scrollbar(display_frame, orient="vertical", command=self.requests_tree.yview)
        hsb = ttk.Scrollbar(display_frame, orient="horizontal", command=self.requests_tree.xview)
        self.requests_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.requests_tree.pack(fill="both", expand=True)

        refresh_button = ttk.Button(display_frame, text="Refresh List", command=self.load_pending_requests)
        refresh_button.pack(pady=5)

        self.load_pending_requests() # Initial load

    def submit_material_request(self):
        project_id_str = self.req_project_id_entry.get().strip()
        project_id = int(project_id_str) if project_id_str else self.app.active_project_id # Use active project ID if field is empty

        material_description = self.req_material_desc_entry.get().strip()
        quantity_str = self.req_quantity_entry.get().strip()
        unit_of_measure = self.req_uom_entry.get().strip()
        urgency_level = self.req_urgency_combobox.get().strip()
        required_by_date = self.req_date_entry.get().strip() if self.req_date_entry.get().strip() else None
        notes = self.req_notes_entry.get().strip()

        if not material_description or not quantity_str:
            messagebox.showerror("Input Error", "Material Description and Quantity are required.", parent=self)
            return

        try:
            quantity_requested = float(quantity_str)
        except ValueError:
            messagebox.showerror("Input Error", "Quantity must be a valid number.", parent=self)
            return

        # Get current user's EmployeeID
        requested_by_employee_id = self.app.user_manager.get_user_id_by_username(self.app.current_username)
        if requested_by_employee_id is None:
            logger.warning(f"Could not find EmployeeID for username {self.app.current_username}. Defaulting to 1.")
            requested_by_employee_id = 1 # Fallback

        if self.module_instance and hasattr(self.module_instance, 'add_material_request'):
            success, msg, log_id = self.module_instance.add_material_request(
                project_id=project_id,
                requested_by_employee_id=requested_by_employee_id,
                material_description=material_description,
                quantity_requested=quantity_requested,
                unit_of_measure=unit_of_measure,
                urgency_level=urgency_level,
                required_by_date=required_by_date,
                notes=notes
            )
            if success:
                messagebox.showinfo("Success", f"{msg} (Log ID: {log_id})", parent=self)
                self.load_pending_requests() # Refresh list
                # Clear input fields
                self.req_project_id_entry.delete(0, tk.END)
                self.req_material_desc_entry.delete(0, tk.END)
                self.req_quantity_entry.delete(0, tk.END)
                self.req_uom_entry.delete(0, tk.END)
                self.req_urgency_combobox.set('Standard')
                self.req_date_entry.delete(0, tk.END)
                self.req_notes_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", msg, parent=self)
        else:
            messagebox.showerror("Error", "Project Startup module not available for material request.", parent=self)
            logger.error("ProjectStartup module instance or add_material_request method not found in PurchasingLogisticsModuleFrame.")

    def load_pending_requests(self):
        for i in self.requests_tree.get_children():
            self.requests_tree.delete(i)

        # Fetch data from Purchasing_Log table (status != 'Received Full' or 'Cancelled')
        # This requires a method in a backend module, e.g., project_startup or a new purchasing module.
        # For now, we'll assume db_manager can be used directly for simplicity, though not ideal.
        query = "SELECT InternalLogID, ProjectID, MaterialDescription, QuantityRequested, UnitOfMeasure, UrgencyLevel, RequiredByDate, Status, DateCreated FROM Purchasing_Log WHERE Status NOT IN ('Received Full', 'Cancelled') ORDER BY DateCreated DESC"
        try:
            requests = db_manager.execute_query(query, fetch_all=True)
            if requests:
                for req in requests:
                    self.requests_tree.insert("", "end", values=(
                        req['InternalLogID'],
                        req['ProjectID'] if req['ProjectID'] is not None else "N/A",
                        req['MaterialDescription'],
                        req['QuantityRequested'],
                        req['UnitOfMeasure'],
                        req['UrgencyLevel'],
                        req['RequiredByDate'] if req['RequiredByDate'] else "N/A",
                        req['Status'],
                        req['DateCreated']
                    ))
        except Exception as e:
            logger.error(f"Error loading pending material requests: {e}", exc_info=True)
            messagebox.showerror("Load Error", f"Failed to load pending requests: {e}", parent=self)

    def on_active_project_changed(self):
        """Called when the global active project changes."""
        logger.info("PurchasingLogisticsModuleFrame: Active project changed. Refreshing relevant views if needed.")
        if self.app.active_project_id:
            self.req_project_id_entry.delete(0, tk.END)
            self.req_project_id_entry.insert(0, str(self.app.active_project_id))
        else:
            self.req_project_id_entry.delete(0, tk.END)
        self.load_pending_requests() # Refresh list based on potentially new global context


class ProductionPrefabModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.app = app
        self.module_instance = module_instance # Should be ProjectStartup instance
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Production & Prefabrication Management", style='Header.TLabel').pack(pady=10)

        # --- Create Production Order Section ---
        order_frame = ttk.LabelFrame(self, text="Create Production Order")
        order_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(order_frame, text="Assembly ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prod_assembly_id_entry = ttk.Entry(order_frame, width=40)
        self.prod_assembly_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Project ID (Optional):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.prod_project_id_entry = ttk.Entry(order_frame, width=40)
        self.prod_project_id_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Quantity to Produce:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.prod_quantity_entry = ttk.Entry(order_frame, width=40)
        self.prod_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Assigned To Employee ID (Optional):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.prod_assigned_emp_id_entry = ttk.Entry(order_frame, width=40)
        self.prod_assigned_emp_id_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Start Date (YYYY-MM-DD, Optional):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.prod_start_date_entry = ttk.Entry(order_frame, width=40)
        self.prod_start_date_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Completion Date (YYYY-MM-DD, Optional):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.prod_completion_date_entry = ttk.Entry(order_frame, width=40)
        self.prod_completion_date_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(order_frame, text="Notes:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.prod_notes_entry = ttk.Entry(order_frame, width=40)
        self.prod_notes_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        submit_order_button = ttk.Button(order_frame, text="Create Production Order", command=self.submit_production_order)
        submit_order_button.grid(row=7, column=0, columnspan=2, pady=10)

        # --- Display Area for Active Production Orders ---
        prod_display_frame = ttk.LabelFrame(self, text="Active Production Orders (Production_Assembly_Tracking)")
        prod_display_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.orders_tree = ttk.Treeview(prod_display_frame, columns=("ProdID", "AssemblyID", "ProjectID", "Qty", "Status", "StartDate", "EndDate", "AssignedTo", "Created"), show="headings")
        self.orders_tree.heading("ProdID", text="Prod ID")
        self.orders_tree.heading("AssemblyID", text="Assembly ID")
        self.orders_tree.heading("ProjectID", text="Project ID")
        self.orders_tree.heading("Qty", text="Qty")
        self.orders_tree.heading("Status", text="Status")
        self.orders_tree.heading("StartDate", text="Start Date")
        self.orders_tree.heading("EndDate", text="End Date")
        self.orders_tree.heading("AssignedTo", text="Assigned Emp ID")
        self.orders_tree.heading("Created", text="Date Created")

        self.orders_tree.column("ProdID", width=60, anchor="center")
        self.orders_tree.column("AssemblyID", width=80, anchor="center")
        self.orders_tree.column("ProjectID", width=70, anchor="center")
        self.orders_tree.column("Qty", width=60, anchor="e")
        self.orders_tree.column("Status", width=100)
        self.orders_tree.column("StartDate", width=100)
        self.orders_tree.column("EndDate", width=100)
        self.orders_tree.column("AssignedTo", width=100)
        self.orders_tree.column("Created", width=120)

        prod_vsb = ttk.Scrollbar(prod_display_frame, orient="vertical", command=self.orders_tree.yview)
        prod_hsb = ttk.Scrollbar(prod_display_frame, orient="horizontal", command=self.orders_tree.xview)
        self.orders_tree.configure(yscrollcommand=prod_vsb.set, xscrollcommand=prod_hsb.set)

        prod_vsb.pack(side='right', fill='y')
        prod_hsb.pack(side='bottom', fill='x')
        self.orders_tree.pack(fill="both", expand=True)

        prod_refresh_button = ttk.Button(prod_display_frame, text="Refresh List", command=self.load_production_orders)
        prod_refresh_button.pack(pady=5)

        self.load_production_orders() # Initial load

    def submit_production_order(self):
        assembly_id_str = self.prod_assembly_id_entry.get().strip()
        project_id_str = self.prod_project_id_entry.get().strip()
        quantity_str = self.prod_quantity_entry.get().strip()
        assigned_emp_id_str = self.prod_assigned_emp_id_entry.get().strip()
        start_date = self.prod_start_date_entry.get().strip() if self.prod_start_date_entry.get().strip() else None
        completion_date = self.prod_completion_date_entry.get().strip() if self.prod_completion_date_entry.get().strip() else None
        notes = self.prod_notes_entry.get().strip()

        if not assembly_id_str or not quantity_str:
            messagebox.showerror("Input Error", "Assembly ID and Quantity are required.", parent=self)
            return

        try:
            assembly_id = int(assembly_id_str)
            quantity_to_produce = float(quantity_str)
            project_id = int(project_id_str) if project_id_str else self.app.active_project_id

            assigned_to_employee_id = None
            if assigned_emp_id_str:
                assigned_to_employee_id = int(assigned_emp_id_str)
            else: # Default to current user if field is empty
                current_user_id = self.app.user_manager.get_user_id_by_username(self.app.current_username)
                assigned_to_employee_id = current_user_id if current_user_id is not None else 1 # Fallback to 1
                logger.info(f"AssignedToEmployeeID not provided for production order, defaulting to current user ID: {assigned_to_employee_id}")

        except ValueError:
            messagebox.showerror("Input Error", "Assembly ID, Project ID (if provided), Quantity, and Assigned Employee ID (if provided) must be valid numbers.", parent=self)
            return

        if self.module_instance and hasattr(self.module_instance, 'create_production_assembly_order'):
            success, msg, prod_id = self.module_instance.create_production_assembly_order(
                assembly_id=assembly_id,
                project_id=project_id,
                quantity_to_produce=quantity_to_produce,
                assigned_to_employee_id=assigned_to_employee_id,
                start_date=start_date,
                completion_date=completion_date,
                notes=notes
            )
            if success:
                messagebox.showinfo("Success", f"{msg} (Production ID: {prod_id})", parent=self)
                self.load_production_orders() # Refresh list
                # Clear input fields
                self.prod_assembly_id_entry.delete(0, tk.END)
                self.prod_project_id_entry.delete(0, tk.END)
                self.prod_quantity_entry.delete(0, tk.END)
                self.prod_assigned_emp_id_entry.delete(0, tk.END)
                self.prod_start_date_entry.delete(0, tk.END)
                self.prod_completion_date_entry.delete(0, tk.END)
                self.prod_notes_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", msg, parent=self)
        else:
            messagebox.showerror("Error", "Project Startup module not available for production order.", parent=self)
            logger.error("ProjectStartup module instance or create_production_assembly_order method not found in ProductionPrefabModuleFrame.")

    def load_production_orders(self):
        for i in self.orders_tree.get_children():
            self.orders_tree.delete(i)

        query = "SELECT ProductionID, AssemblyID, ProjectID, QuantityToProduce, Status, StartDate, CompletionDate, AssignedToEmployeeID, DateCreated FROM Production_Assembly_Tracking WHERE Status NOT IN ('Completed', 'Shipped', 'Cancelled') ORDER BY DateCreated DESC"
        try:
            orders = db_manager.execute_query(query, fetch_all=True)
            if orders:
                for order in orders:
                    self.orders_tree.insert("", "end", values=(
                        order['ProductionID'],
                        order['AssemblyID'],
                        order['ProjectID'] if order['ProjectID'] is not None else "N/A",
                        order['QuantityToProduce'],
                        order['Status'],
                        order['StartDate'] if order['StartDate'] else "N/A",
                        order['CompletionDate'] if order['CompletionDate'] else "N/A",
                        order['AssignedToEmployeeID'] if order['AssignedToEmployeeID'] is not None else "N/A",
                        order['DateCreated']
                    ))
        except Exception as e:
            logger.error(f"Error loading production orders: {e}", exc_info=True)
            messagebox.showerror("Load Error", f"Failed to load production orders: {e}", parent=self)

    def on_active_project_changed(self):
        """Called when the global active project changes."""
        logger.info("ProductionPrefabModuleFrame: Active project changed. Refreshing relevant views if needed.")
        if self.app.active_project_id:
            self.prod_project_id_entry.delete(0, tk.END)
            self.prod_project_id_entry.insert(0, str(self.app.active_project_id))
        else:
            self.prod_project_id_entry.delete(0, tk.END)
        self.load_production_orders()


class ProjectManagementApp(tk.Tk):
    """
    Main application window for the Construction Project Management System.
    """
    def __init__(self):
        super().__init__()
        self.title("Davinci")
        self.geometry("1200x800")
        self.withdraw() # Hide main window until login is successful

        self.user_manager = UserManagement(db_manager) # Pass db_manager instance
        self.current_user_role = None
        self.current_username = None
        self.modules = {} # To store instantiated module objects
        self.active_project_id = None 
        self.active_project_name = None 

        self._setup_styles()
        self._initialize_modules()
        self.create_login_window()
        self.create_main_layout()

    def _setup_styles(self):
        self.colors = {
            'bg_primary': '#1e1e1e',
            'bg_secondary': '#252526',
            'bg_tertiary': '#333333',
            'accent': '#007acc',
            'fg_primary': '#cccccc',
            'fg_secondary': '#8c8c8c',
            'border': '#444444',
            'input_bg': '#3c3c3c',
        }
        self.configure(bg=self.colors['bg_primary'])

        style = ttk.Style(self)
        style.theme_use('clam')

        # General widget styling
        style.configure('.', background=self.colors['bg_secondary'], foreground=self.colors['fg_primary'], borderwidth=0, focusthickness=0)
        style.map('.', background=[('active', self.colors['bg_tertiary'])])

        # Frame
        style.configure('TFrame', background=self.colors['bg_secondary'])
        style.configure('Status.TFrame', background=self.colors['accent'])

        # Label
        style.configure('TLabel', background=self.colors['bg_secondary'], foreground=self.colors['fg_primary'], font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), background=self.colors['bg_secondary'])
        style.configure('Status.TLabel', background=self.colors['accent'], foreground='#ffffff')

        # Button
        style.configure('TButton', background=self.colors['input_bg'], foreground=self.colors['fg_primary'], font=('Segoe UI', 10), borderwidth=1)
        style.map('TButton',
                  background=[('pressed', self.colors['accent']), ('active', self.colors['bg_tertiary'])],
                  foreground=[('pressed', '#ffffff'), ('active', self.colors['fg_primary'])],
                  bordercolor=[('active', self.colors['accent'])])
        
        # Activity Bar Button Style
        style.configure('Activity.TButton', background=self.colors['bg_tertiary'], relief='flat', font=('Segoe UI', 12))
        style.map('Activity.TButton', background=[('active', self.colors['accent'])], foreground=[('active', '#ffffff')])

        # Entry
        style.configure('TEntry', fieldbackground=self.colors['input_bg'], foreground=self.colors['fg_primary'], bordercolor=self.colors['border'], insertcolor=self.colors['fg_primary'])
        style.map('TEntry', bordercolor=[('focus', self.colors['accent'])])

        # Treeview
        style.configure('Treeview', background=self.colors['input_bg'], fieldbackground=self.colors['input_bg'], foreground=self.colors['fg_primary'], bordercolor=self.colors['border'])
        style.configure('Treeview.Heading', background=self.colors['bg_tertiary'], font=('Segoe UI', 10, 'bold'), relief='flat')
        style.map('Treeview.Heading', background=[('active', self.colors['bg_secondary'])])
        
        # PanedWindow
        style.configure('TPanedwindow', background=self.colors['bg_primary'])
        
        # LabelFrame
        style.configure('TLabelFrame', background=self.colors['bg_secondary'], bordercolor=self.colors['border'])
        style.configure('TLabelFrame.Label', background=self.colors['bg_secondary'], foreground=self.colors['fg_primary'])

    def _initialize_modules(self):
        """
        Initializes and registers all functional modules using the PluginRegistry.
        """
        # Import module classes directly
        from integration import Integration
        from data_processing import DataProcessing
        from project_startup import ProjectStartup
        from execution_management import ExecutionManagement
        from monitoring_control import MonitoringControl
        from reporting import Reporting
        from closeout import Closeout
        # UserManagement instance (self.user_manager) is already created.
        # Config is used directly.

        # Instantiate modules, passing db_manager (which is self.db_manager from App's perspective,
        # but db_manager is the global singleton instance also used by tests now)
        # Note: If other modules also need db_manager, they should be refactored like ProjectStartup
        # For now, assume only ProjectStartup needs explicit db_manager injection for main app.
        # Other modules might still be importing the global db_manager directly.
        # For consistency, it would be better if all modules that use db_manager take it as a constructor argument.
        # All modules that use db_manager will now take it as a constructor argument.

        # Instantiate modules, passing db_manager
        integration_module = Integration(db_manager)
        data_processing_module = DataProcessing(db_manager)
        project_startup_module = ProjectStartup(db_manager)
        execution_management_module = ExecutionManagement(db_manager)
        monitoring_control_module = MonitoringControl(db_manager)

        # Reporting and Closeout have dependencies on other modules
        reporting_module = Reporting(db_m_instance=db_manager, monitor_control_instance=monitoring_control_module)
        closeout_module = Closeout(db_m_instance=db_manager, reporting_instance=reporting_module, monitor_control_instance=monitoring_control_module)

        self.modules = {
            'integration': integration_module,
            'data_processing': data_processing_module,
            'project_startup': project_startup_module,
            'execution_management': execution_management_module,
            'monitoring_control': monitoring_control_module,
            'reporting': reporting_module,
            'closeout': closeout_module,
            'user_management': self.user_manager, # UserManagement uses global db_manager internally for now
            'configuration': Config
        }

        # Register instantiated modules with PluginRegistry
        for name, instance in self.modules.items():
            if name != 'configuration': # Config is not a typical module instance to be registered
                PluginRegistry.register_module(name, instance)

        logger.info("All core modules instantiated and registered directly in main.py.")

    def create_login_window(self):
        LoginWindow(self, self)

    def create_main_layout(self):
        # Main container
        main_container = tk.Frame(self, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True)

        # Status Bar (at the bottom)
        self.status_bar = ttk.Frame(main_container, style='Status.TFrame', height=25)
        self.status_bar.pack(side='bottom', fill='x')
        self.status_label = ttk.Label(self.status_bar, text="Ready", style='Status.TLabel')
        self.status_label.pack(side='left', padx=10)

        # Activity Bar (far left)
        self.activity_bar = ttk.Frame(main_container, width=50, style='TFrame')
        self.activity_bar.pack(side='left', fill='y')

        # Main content area (PanedWindow)
        self.main_pane = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL, style='TPanedwindow')
        self.main_pane.pack(fill='both', expand=True)

        # Side Bar (for lists, trees, etc.)
        self.side_bar = ttk.Frame(self.main_pane, width=250, style='TFrame')
        self.main_pane.add(self.side_bar, weight=1)

        # Editor Area (for module content)
        self.editor_area = ttk.Frame(self.main_pane, style='TFrame')
        self.main_pane.add(self.editor_area, weight=4)

        self.module_frames = {}
        self.side_bar_frames = {}

        # Top Frame for User Info and Logout (will be placed within the editor area or a header bar)
        self.top_frame = ttk.Frame(self.editor_area, style='TFrame')
        self.top_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.user_info_label = ttk.Label(self.top_frame, text="Not Logged In", style='TLabel')
        self.user_info_label.pack(side="left", padx=10, pady=5)

        self.active_project_label = ttk.Label(self.top_frame, text="No Active Project", style='TLabel')
        self.active_project_label.pack(side="left", padx=10, pady=5)

        self.logout_button = ttk.Button(self.top_frame, text="Logout", command=self.logout, style='TButton')
        self.logout_button.pack(side="right", padx=10, pady=5)

    # --- Base Module Frame for common functionality ---
    # Moved EARLIER to be defined before ProjectManagementApp.populate_navigation_menu
    # class BaseModuleFrame(tk.Frame): ...

    # --- Consolidated and New Module Frames ---
    # Moved EARLIER: IntegrationDataProcessingModuleFrame, ReportingCloseoutModuleFrame, SchedulingModuleFrame

    def show_main_application(self):
        """Updates the main GUI after successful login."""
        if hasattr(self, 'user_info_label') and self.user_info_label.winfo_exists():
            self.user_info_label.config(text=f"Logged in as: {self.current_username} ({self.current_user_role})")
        self.update_active_project_display() # NEW
        self.populate_navigation_menu()
        # self.show_module_frame('overview') # Show a default overview or welcome frame
        # Directly show the ProjectStartupModuleFrame
        # Need to find the class for 'project_startup' module. It's ProjectStartupModuleFrame.
        # We also need to ensure it's correctly registered or passed if not using the simple name.
        # The module_buttons_data has ('Project Startup', 'project_startup', ProjectStartupModuleFrame)
        # Ensure ProjectStartupModuleFrame is defined before this call if not already.
        # It is defined later, so this direct reference is okay as it's a runtime call.
        self.show_module_frame('project_startup', ProjectStartupModuleFrame)


    def update_active_project_display(self):
        """Updates the active project label in the top frame."""
        if hasattr(self, 'active_project_label') and self.active_project_label.winfo_exists():
            if self.active_project_id and self.active_project_name:
                self.active_project_label.config(text=f"Active Project: {self.active_project_name} (ID: {self.active_project_id})")
            else:
                self.active_project_label.config(text="No Active Project Selected")

    def set_active_project(self, project_id, project_name):
        """Sets the active project for the application."""
        self.active_project_id = project_id
        self.active_project_name = project_name
        self.update_active_project_display()
        logger.info(f"Active project set to: ID {project_id}, Name: {project_name}")
        # Potentially refresh current module frame if it depends on active project
        self.refresh_current_module_if_needed()

    def clear_active_project(self):
        """Clears the active project."""
        self.active_project_id = None
        self.active_project_name = None
        self.update_active_project_display()
        logger.info("Active project cleared.")
        self.refresh_current_module_if_needed()

    def refresh_current_module_if_needed(self):
        """Refreshes the currently visible module frame if it's active project aware."""
        for frame in self.module_frames.values():
            if frame.winfo_ismapped() and hasattr(frame, 'on_active_project_changed'):
                frame.on_active_project_changed()
                break

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.current_user_role = None
            self.current_username = None
            self.clear_active_project() # NEW: Clear active project on logout
            logger.info("User logged out.")
            messagebox.showinfo("Logout", "You have been logged out.")
            # Clear navigation menu (activity bar)
            for widget in list(self.activity_bar.winfo_children()): # Iterate over a copy
                widget.destroy()
            # Clear side bar
            for widget in list(self.side_bar.winfo_children()): # Iterate over a copy
                widget.destroy()
            # Clear editor area
            for widget in list(self.editor_area.winfo_children()): # Iterate over a copy
                widget.destroy()
            self.module_frames = {} # Clear cached frames
            self.side_bar_frames = {} # Clear cached side bar frames
            self.withdraw() # Hide main window
            self.create_login_window() # Show login window again

    def populate_navigation_menu(self):
        """
        Populates the activity bar with buttons for accessible modules.
        """
        for widget in self.activity_bar.winfo_children():
            widget.destroy() # Clear existing buttons

        # Note: IntegrationDataProcessingModuleFrame, ReportingCloseoutModuleFrame, 
        # and SchedulingModuleFrame definitions are now moved globally, before ProjectManagementApp class.

        module_buttons_data = [
            # ('Integration', 'integration', IntegrationModuleFrame), # Replaced
            # ('Data Processing', 'data_processing', DataProcessingModuleFrame), # Replaced
            ('Integration & Data Proc.', 'integration_data_processing', IntegrationDataProcessingModuleFrame),
            ('Project Startup', 'project_startup', ProjectStartupModuleFrame),
            ('Execution Management', 'execution_management', ExecutionManagementModuleFrame),
            ('Monitoring & Control', 'monitoring_control', MonitoringControlModuleFrame),
            # ('Reporting', 'reporting', ReportingModuleFrame), # Replaced
            # ('Closeout', 'closeout', CloseoutModuleFrame), # Replaced
            ('Reporting & Closeout', 'reporting_closeout', ReportingCloseoutModuleFrame),
            ('Project Scheduling', 'project_scheduling', SchedulingModuleFrame), # New Scheduling Module
            ('Daily Log', 'daily_log', DailyLogModuleFrame), # New Daily Log Module
            ('Purchasing & Logistics', 'purchasing_logistics', PurchasingLogisticsModuleFrame), # New
            ('Production & Prefab', 'production_prefab', ProductionPrefabModuleFrame), # New
            ('User Management', 'user_management', UserManagementModuleFrame),
        ]

        # Note: ReportingCloseoutModuleFrame and SchedulingModuleFrame definitions
        # are now moved globally, before ProjectManagementApp class.

        for text, module_name, frame_class in module_buttons_data:
            if self.user_manager.check_access(self.current_user_role, module_name):
                btn = ttk.Button(self.activity_bar, text=text, style='Activity.TButton',
                                 command=lambda m=module_name, fc=frame_class: self.show_module_frame(m, fc))
                btn.pack(fill="x", pady=5, padx=5)

    def show_module_frame(self, module_name, frame_class=None):
        """
        Hides all module frames and shows the selected one in the editor area.
        Instantiates if not already present.
        """
        # Hide current frame if one is visible
        for frame in self.module_frames.values():
            if frame.winfo_ismapped():
                frame.pack_forget()

        if module_name not in self.module_frames:
            if frame_class:
                # Specific handling for new UI modules that use ProjectStartup as their backend
                if module_name in ['purchasing_logistics', 'production_prefab']:
                    module_instance_to_pass = self.modules.get('project_startup')
                    if not module_instance_to_pass:
                        logger.error(f"ProjectStartup module instance not found for {module_name}. Cannot initialize frame.")
                        messagebox.showerror("Initialization Error", f"Backend for {module_name} is not available.", parent=self)
                        return
                else:
                    module_instance_to_pass = self.modules.get(module_name)

                self.module_frames[module_name] = frame_class(self.editor_area, self, module_instance_to_pass)
            else:
                messagebox.showerror("Error", f"Could not load frame for module: {module_name}")
                return

        self.module_frames[module_name].pack(fill="both", expand=True)
        logger.info(f"Displayed {module_name} module frame.")

        # Show the project list in the side bar if the project startup or new consolidated module is active
        if module_name == 'project_startup' or module_name == 'integration_data_processing':
            self.show_project_list_in_sidebar()
        else:
            self.hide_project_list_in_sidebar()

    def show_project_list_in_sidebar(self):
        # Ensure the project list is associated with the main app instance for consistent access
        if not hasattr(self, 'project_tree_frame') or self.project_tree_frame is None: # Changed self.app to self
            self.project_tree_frame = ttk.LabelFrame(self.side_bar, text="Project List") # Changed self.app to self

            self.project_tree = ttk.Treeview(self.project_tree_frame) # Changed self.app to self
            self.project_tree["columns"] = ("ProjectID", "ProjectName", "EstimateDocsComplete", "WBSComplete", "Status")

            self.project_tree.column("#0", width=0, stretch=tk.NO) # Changed self.app to self
            self.project_tree.column("ProjectID", anchor=tk.W, width=80) # Changed self.app to self
            self.project_tree.column("ProjectName", anchor=tk.W, width=200) # Changed self.app to self
            self.project_tree.column("EstimateDocsComplete", anchor=tk.CENTER, width=150) # Changed self.app to self
            self.project_tree.column("WBSComplete", anchor=tk.CENTER, width=120) # Changed self.app to self
            self.project_tree.column("Status", anchor=tk.W, width=100) # Changed self.app to self

            self.project_tree.heading("ProjectID", text="Project ID", anchor=tk.W) # Changed self.app to self
            self.project_tree.heading("ProjectName", text="Project Name", anchor=tk.W) # Changed self.app to self
            self.project_tree.heading("EstimateDocsComplete", text="Estimate Docs Complete", anchor=tk.W) # Changed self.app to self
            self.project_tree.heading("WBSComplete", text="WBS Complete", anchor=tk.W) # Changed self.app to self
            self.project_tree.heading("Status", text="Status", anchor=tk.W) # Changed self.app to self

            scrollbar = ttk.Scrollbar(self.project_tree_frame, orient="vertical", command=self.project_tree.yview) # Changed self.app to self
            self.project_tree.configure(yscrollcommand=scrollbar.set) # Changed self.app to self
            scrollbar.pack(side="right", fill="y")
            self.project_tree.pack(side="left", fill="both", expand=True) # Changed self.app to self

            # The refresh button should call a method on the app instance
            refresh_button = ttk.Button(self.project_tree_frame, text="Refresh List", command=self.load_project_list_data) # Changed self.app to self (twice)
            refresh_button.pack(side="bottom", pady=5)

            # Storing the frame in side_bar_frames for pack_forget logic
            self.side_bar_frames['project_list'] = self.project_tree_frame # Changed self.app to self

        if hasattr(self, 'project_tree_frame') and self.project_tree_frame.winfo_exists(): # Changed self.app to self
            self.project_tree_frame.pack(pady=10, padx=10, fill="both", expand=True) # Changed self.app to self
            self.load_project_list_data() # Call the method on the app instance # Changed self.app to self

    def hide_project_list_in_sidebar(self):
        if hasattr(self, 'project_tree_frame') and self.project_tree_frame is not None: # Changed self.app to self
            self.project_tree_frame.pack_forget() # Changed self.app to self

    def load_project_list_data(self): # New method in ProjectManagementApp
        """
        Fetches project data from the backend and populates the Project List Treeview in the sidebar.
        """
        if not hasattr(self, 'project_tree') or self.project_tree is None: # Changed self.app to self
            logger.error("Project tree in sidebar not initialized before loading data.")
            return

        # Clear existing items in the tree
        for item in self.project_tree.get_children(): # Changed self.app to self
            self.project_tree.delete(item) # Changed self.app to self

        project_startup_module = self.modules.get('project_startup')
        if project_startup_module and hasattr(project_startup_module, 'get_all_projects_with_status'):
            projects = project_startup_module.get_all_projects_with_status()
            if projects:
                for project in projects:
                    self.project_tree.insert("", tk.END, values=( # Changed self.app to self
                        project.get('ProjectID', 'N/A'),
                        project.get('ProjectName', 'N/A'),
                        project.get('EstimateDocsComplete', "N/A"),
                        project.get('WBSComplete', "N/A"),
                        project.get('StatusName', 'N/A')
                    ))
            else:
                self.project_tree.insert("", tk.END, values=("", "No projects found.", "", "", "")) # Changed self.app to self
        else:
            # If using a generic message box, ensure it's parented correctly or use app's status bar
            logger.error("Could not load projects. Project Startup module or required method not available.")
            # self.status_label.config(text="Error: Could not load projects.") # Example status update
            # Temporarily, show a messagebox if it's critical, but status bar is better for non-blocking
            messagebox.showerror("Error", "Could not load projects. Project Startup module or method not available.", parent=self)


    def show_project_list_in_sidebar_OLD(self): # Original method renamed for safety
        if 'project_list' not in self.side_bar_frames:
            project_list_frame = ttk.LabelFrame(self.side_bar, text="Project List")
            project_list_frame.pack(pady=10, padx=10, fill="both", expand=True)

            self.project_tree = ttk.Treeview(project_list_frame)
            self.project_tree["columns"] = ("ProjectID", "ProjectName", "EstimateDocsComplete", "WBSComplete", "Status")

            self.project_tree.column("#0", width=0, stretch=tk.NO)
            self.project_tree.column("ProjectID", anchor=tk.W, width=80)
            self.project_tree.column("ProjectName", anchor=tk.W, width=200)
            self.project_tree.column("EstimateDocsComplete", anchor=tk.CENTER, width=150)
            self.project_tree.column("WBSComplete", anchor=tk.CENTER, width=120)
            self.project_tree.column("Status", anchor=tk.W, width=100)

            self.project_tree.heading("ProjectID", text="Project ID", anchor=tk.W)
            self.project_tree.heading("ProjectName", text="Project Name", anchor=tk.W)
            self.project_tree.heading("EstimateDocsComplete", text="Estimate Docs Complete", anchor=tk.W)
            self.project_tree.heading("WBSComplete", text="WBS Complete", anchor=tk.W)
            self.project_tree.heading("Status", text="Status", anchor=tk.W)

            scrollbar = ttk.Scrollbar(project_list_frame, orient="vertical", command=self.project_tree.yview)
            self.project_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            self.project_tree.pack(side="left", fill="both", expand=True)

            refresh_button = ttk.Button(project_list_frame, text="Refresh List", command=self.load_project_list)
            refresh_button.pack(side="bottom", pady=5)

            self.side_bar_frames['project_list'] = project_list_frame

        self.side_bar_frames['project_list'].pack(pady=10, padx=10, fill="both", expand=True)
        self.load_project_list()

    def hide_project_list_in_sidebar(self):
        if 'project_list' in self.side_bar_frames:
            self.side_bar_frames['project_list'].pack_forget()

# --- Base Module Frame for common functionality ---
# Definition moved before ProjectManagementApp class
# class BaseModuleFrame(tk.Frame):
#     def __init__(self, parent, app, module_instance=None):
#         super().__init__(parent)
# ... (rest of BaseModuleFrame) ...

# --- Individual Module GUI Frames (some are now consolidated or placeholders) ---
# Definition of WelcomeFrame, IntegrationModuleFrame etc. also moved before ProjectManagementApp or are handled by consolidated frames.

# --- Consolidated and New Module Frames ---
# Definitions for IntegrationDataProcessingModuleFrame, ReportingCloseoutModuleFrame, SchedulingModuleFrame
# are also moved before ProjectManagementApp class.

# --- Welcome/Overview Frame ---
# class WelcomeFrame(BaseModuleFrame): ... # Moved

# --- Integration Module GUI ---
# class IntegrationModuleFrame(BaseModuleFrame): ... # Moved/Consolidated

# --- Data Processing Module GUI ---
# class DataProcessingModuleFrame(BaseModuleFrame): ... # Moved/Consolidated

# --- Project Startup Module GUI ---
# class ProjectStartupModuleFrame(BaseModuleFrame): ... # Defined later, but its usage in show_main_application is a runtime lookup.

# --- Execution Management Module GUI ---
# class ExecutionManagementModuleFrame(BaseModuleFrame): ... # Defined later

# --- Monitoring & Control Module GUI ---
# class MonitoringControlModuleFrame(BaseModuleFrame): ... # Defined later

# --- Reporting Module GUI ---
# class ReportingModuleFrame(BaseModuleFrame): ... # Moved/Consolidated

# --- Closeout Module GUI ---
# class CloseoutModuleFrame(BaseModuleFrame): ... # Moved/Consolidated

# --- User Management Module GUI ---
# class UserManagementModuleFrame(BaseModuleFrame): ... # Defined later


# --- Main Application Class Definition Continues (methods like populate_navigation_menu are part of ProjectManagementApp) ---

# --- The following frame definitions are kept here as they are used by populate_navigation_menu,
# --- but their definitions are now logically placed *before* ProjectManagementApp in the file flow.
# --- For the diff tool, we are effectively moving their definitions from here to an earlier point.

# class IntegrationDataProcessingModuleFrame(BaseModuleFrame): ... # Actual definition moved
# class ReportingCloseoutModuleFrame(BaseModuleFrame): ... # Actual definition moved
# class SchedulingModuleFrame(BaseModuleFrame): ... # Actual definition moved


# --- Original positions of other frames that are still standalone or used:
# These are defined after ProjectManagementApp in the original code, which is fine for runtime instantiation
# as long as they are not directly referenced by type (e.g. ClassName without quotes) during class definition.
# The problematic ones were those in module_buttons_data which is constructed during ProjectManagementApp initialization.

# Example: ProjectStartupModuleFrame is used in self.show_module_frame('project_startup', ProjectStartupModuleFrame)
# This is a runtime call, so ProjectStartupModuleFrame just needs to be defined somewhere in the global scope
# before this line is executed. The original placement after ProjectManagementApp is okay for this.

# The classes that were problematic were IntegrationDataProcessingModuleFrame, ReportingCloseoutModuleFrame,
# and SchedulingModuleFrame because they were used as direct class references (not strings)
# inside `populate_navigation_menu`'s `module_buttons_data` list, and this method is called during app setup.




if __name__ == "__main__":
    os.makedirs(Config.DATABASE_DIR, exist_ok=True)
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.REPORTS_DIR, exist_ok=True)
    os.makedirs(Config.ARCHIVE_DIR, exist_ok=True) # Ensure ARCHIVE_DIR from closeout.py is created
    os.makedirs(Config.LOGS_DIR, exist_ok=True)

    _ = db_manager # Initialize DB Manager

    sample_csv_path = os.path.join(Config.get_data_dir(), 'sample_estimate.csv')
    if not os.path.exists(sample_csv_path):
        sample_data = {
            'Cost Code': ['01-010', '01-020', '02-100', '03-200', '03-210', '04-300', '05-400'],
            'Description': ['Mobilization', 'Project Supervision', 'Site Prep', 'Concrete Footings', 'Concrete Slab', 'Framing', 'Roofing'],
            'Quantity': [1.0, 40.0, 500.0, 15.0, 200.0, 5000.0, 20.0],
            'Unit': ['LS', 'HR', 'SY', 'CY', 'SF', 'BF', 'SQ'],
            'Unit Cost': [5000.00, 75.00, 15.00, 300.00, 5.00, 0.75, 150.00],
            'Total Cost': [5000.00, 3000.00, 7500.00, 4500.00, 1000.00, 3750.00, 3000.00],
            'Phase': ['Pre-Construction', 'Pre-Construction', 'Foundation', 'Foundation', 'Foundation', 'Structure', 'Exterior']
        }
        sample_df = pd.DataFrame(sample_data)
        sample_df.to_csv(sample_csv_path, index=False)
        logger.info(f"Created sample_estimate.csv at: {sample_csv_path}")

    app = ProjectManagementApp()
    app.mainloop()
