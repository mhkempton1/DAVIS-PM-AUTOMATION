import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import sys
import os
import logging
import logging.handlers  # For RotatingFileHandler
import pandas as pd
from datetime import datetime, timedelta

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
import constants # Added
from tkPDFViewer import tkPDFViewer

# Import GUI Frames
from gui_frames.base_frame import BaseModuleFrame
from gui_frames.integration_data_processing_frame import IntegrationDataProcessingModuleFrame
from gui_frames.reporting_closeout_frame import ReportingCloseoutModuleFrame
from gui_frames.scheduling_frame import SchedulingModuleFrame
from gui_frames.welcome_frame import WelcomeFrame
from gui_frames.project_startup_frame import ProjectStartupModuleFrame
from gui_frames.execution_management_frame import ExecutionManagementModuleFrame
from gui_frames.monitoring_control_frame import MonitoringControlModuleFrame
from gui_frames.daily_log_frame import DailyLogModuleFrame
from gui_frames.user_management_frame import UserManagementModuleFrame
from gui_frames.purchasing_logistics_frame import PurchasingLogisticsModuleFrame
from gui_frames.production_prefab_frame import ProductionPrefabModuleFrame
from gui_frames.crm_frame import CRMModuleFrame # Added CRM Frame import


# Set up logging for the Main Application
def setup_logging():
    log_directory = Config.get_logs_dir()
    log_file_path = os.path.join(log_directory, 'davinci_app.log')

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)


setup_logging()
logger = logging.getLogger(__name__)


class LoginWindow(tk.Toplevel):
    """Separate window for user login."""

    def __init__(self, master, app_instance):
        super().__init__(master)
        self.master = master
        self.app = app_instance
        self.title("Login")
        self.geometry("300x200")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        self.show_password_var = tk.BooleanVar()
        self.show_password_checkbutton = tk.Checkbutton(
            self,
            text="Show Password",
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        )
        self.show_password_checkbutton.pack(pady=2)

        self.login_button = tk.Button(self, text="Login", command=self.attempt_login)
        self.login_button.pack(pady=10)

        self.username_entry.insert(0, Config.DEFAULT_ADMIN_USERNAME)
        self.password_entry.insert(0, Config.DEFAULT_ADMIN_PASSWORD)

        self.instructions_button = tk.Button(
            self, text="Instructions for Use", command=self.show_instructions
        )
        self.instructions_button.pack(pady=5)

        self.logo_label = tk.Label(
            self, text="Davinci Logo Placeholder", font=("Arial", 10, "italic"), fg="grey"
        )
        self.logo_label.pack(pady=10, side="bottom")

    def show_instructions(self):
        messagebox.showinfo(
            "Instructions for Use",
            "User Manual/Instructions Content Here.\n\n"
            "1. Enter your username and password.\n"
            "2. Click Login.\n"
            "3. If login is successful, the main application will open.\n"
            "4. For issues, contact support.",
            parent=self
        )

    def attempt_login(self):
        self.login_button.config(state="disabled")
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        role = self.app.user_manager.authenticate_user(username, password)
        if role:
            self.app.current_user_role = role
            self.app.current_username = username
            logger.info(f"User '{username}' logged in successfully.")

            success_window = tk.Toplevel(self)
            success_window.title("Success")
            success_window.geometry("250x100")
            success_window.resizable(False, False)
            tk.Label(
                success_window,
                text=f"Welcome, {username}!\nLogin Successful!",
                font=("Arial", 12),
                pady=10
            ).pack(expand=True)
            success_window.transient(self.master)
            success_window.grab_set()

            success_window.after(1500, lambda: [
                success_window.destroy(),
                self.destroy(),
                self.master.deiconify(),
                self.app.show_main_application()
            ])
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.", parent=self)
            logger.warning(f"Login attempt failed for username: {username}")
            self.login_button.config(state="normal")

    def _toggle_password_visibility(self):
        """Toggles the visibility of the password in the password entry field."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
            self.master.destroy()


class ProjectManagementApp(tk.Tk):
    """Main application window for the Construction Project Management System."""

    def __init__(self):
        super().__init__()
        self.title("Davinci")
        self.geometry("1200x800")
        self.withdraw()  # Hide main window until login is successful

        self.user_manager = UserManagement(db_manager)
        self.current_user_role = None
        self.current_username = None
        self.modules = {}
        self.active_project_id = None
        self.active_project_name = None

        self._setup_styles()
        self._initialize_modules()
        self.create_login_window()
        self.create_main_layout()
        self.protocol("WM_DELETE_WINDOW", self.on_app_closing) # Graceful shutdown

    def on_app_closing(self):
        logger.info("Application is closing.")
        # Ensure db_manager and its connection are valid before trying to close
        if 'db_manager' in globals() and db_manager and hasattr(db_manager, 'conn') and db_manager.conn is not None:
            try:
                logger.info("Attempting to close database connection.")
                db_manager.close_connection()
                logger.info("Database connection closed via on_app_closing.")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}", exc_info=True)
        else:
            logger.info("Database manager or connection not available/valid for closing.")
        self.destroy()


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

        style.configure(
            '.',
            background=self.colors['bg_secondary'],
            foreground=self.colors['fg_primary'],
            borderwidth=0,
            focusthickness=0
        )
        style.map('.', background=[('active', self.colors['bg_tertiary'])])
        style.configure('TFrame', background=self.colors['bg_secondary'])
        style.configure('Status.TFrame', background=self.colors['accent'])
        style.configure(
            'TLabel',
            background=self.colors['bg_secondary'],
            foreground=self.colors['fg_primary'],
            font=('Segoe UI', 10)
        )
        style.configure(
            'Header.TLabel',
            font=('Segoe UI', 14, 'bold'),
            background=self.colors['bg_secondary']
        )
        style.configure(
            'Status.TLabel',
            background=self.colors['accent'],
            foreground='#ffffff'
        )
        style.configure(
            'TButton',
            background=self.colors['input_bg'],
            foreground=self.colors['fg_primary'],
            font=('Segoe UI', 10),
            borderwidth=1
        )
        style.map(
            'TButton',
            background=[('pressed', self.colors['accent']), ('active', self.colors['bg_tertiary'])],
            foreground=[('pressed', '#ffffff'), ('active', self.colors['fg_primary'])],
            bordercolor=[('active', self.colors['accent'])]
        )
        style.configure(
            'Activity.TButton',
            background=self.colors['bg_tertiary'],
            relief='flat',
            font=('Segoe UI', 12)
        )
        style.map(
            'Activity.TButton',
            background=[('active', self.colors['accent'])],
            foreground=[('active', '#ffffff')]
        )
        style.configure(
            'TEntry',
            fieldbackground=self.colors['input_bg'],
            foreground=self.colors['fg_primary'],
            bordercolor=self.colors['border'],
            insertcolor=self.colors['fg_primary']
        )
        style.map('TEntry', bordercolor=[('focus', self.colors['accent'])])
        style.configure(
            'Treeview',
            background=self.colors['input_bg'],
            fieldbackground=self.colors['input_bg'],
            foreground=self.colors['fg_primary'],
            bordercolor=self.colors['border']
        )
        style.configure(
            'Treeview.Heading',
            background=self.colors['bg_tertiary'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat'
        )
        style.map('Treeview.Heading', background=[('active', self.colors['bg_secondary'])])
        style.configure('TPanedwindow', background=self.colors['bg_primary'])
        style.configure('TLabelFrame', background=self.colors['bg_secondary'], bordercolor=self.colors['border'])
        style.configure(
            'TLabelFrame.Label',
            background=self.colors['bg_secondary'],
            foreground=self.colors['fg_primary']
        )

    def _initialize_modules(self):
        """Initializes and registers all functional modules."""
        from integration import Integration
        from data_processing import DataProcessing
        from project_startup import ProjectStartup
        from execution_management import ExecutionManagement
        from monitoring_control import MonitoringControl
        from reporting import Reporting
        from closeout import Closeout
        from crm import CRM # Added CRM backend module import

        integration_module = Integration(db_manager)
        data_processing_module = DataProcessing(db_manager)
        project_startup_module = ProjectStartup(db_manager)
        execution_management_module = ExecutionManagement(db_manager)
        monitoring_control_module = MonitoringControl(db_manager)
        reporting_module = Reporting(
            db_m_instance=db_manager, monitor_control_instance=monitoring_control_module
        )
        closeout_module = Closeout(
            db_m_instance=db_manager,
            reporting_instance=reporting_module,
            monitor_control_instance=monitoring_control_module
        )
        crm_module = CRM(db_manager) # Instantiated CRM module

        self.modules = {
            constants.MODULE_INTEGRATION: integration_module,
            constants.MODULE_DATA_PROCESSING: data_processing_module,
            constants.MODULE_PROJECT_STARTUP: project_startup_module,
            constants.MODULE_EXECUTION_MANAGEMENT: execution_management_module,
            constants.MODULE_MONITORING_CONTROL: monitoring_control_module,
            constants.MODULE_REPORTING: reporting_module,
            constants.MODULE_CLOSEOUT: closeout_module,
            constants.MODULE_USER_MANAGEMENT: self.user_manager,
            constants.MODULE_CONFIGURATION: Config,
            constants.MODULE_CRM: crm_module # Added CRM to modules dictionary
        }

        for name, instance in self.modules.items():
            if name != constants.MODULE_CONFIGURATION: # Check against constant
                PluginRegistry.register_module(name, instance)
        logger.info("All core modules instantiated and registered.")

    def create_login_window(self):
        LoginWindow(self, self)

    def create_main_layout(self):
        main_container = tk.Frame(self, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True)

        self.status_bar = ttk.Frame(main_container, style='Status.TFrame', height=25)
        self.status_bar.pack(side='bottom', fill='x')
        self.status_label = ttk.Label(self.status_bar, text="Ready", style='Status.TLabel')
        self.status_label.pack(side='left', padx=10)

        self.activity_bar = ttk.Frame(main_container, width=50, style='TFrame')
        self.activity_bar.pack(side='left', fill='y')

        self.main_pane = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL, style='TPanedwindow')
        self.main_pane.pack(fill='both', expand=True)

        self.side_bar = ttk.Frame(self.main_pane, width=250, style='TFrame')
        self.main_pane.add(self.side_bar, weight=1)

        self.editor_area = ttk.Frame(self.main_pane, style='TFrame')
        self.main_pane.add(self.editor_area, weight=4)

        self.module_frames = {}
        self.side_bar_frames = {}

        self.top_frame = ttk.Frame(self.editor_area, style='TFrame')
        self.top_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.user_info_label = ttk.Label(self.top_frame, text="Not Logged In", style='TLabel')
        self.user_info_label.pack(side="left", padx=10, pady=5)

        self.active_project_label = ttk.Label(self.top_frame, text="No Active Project", style='TLabel')
        self.active_project_label.pack(side="left", padx=10, pady=5)

        self.logout_button = ttk.Button(self.top_frame, text="Logout", command=self.logout, style='TButton')
        self.logout_button.pack(side="right", padx=10, pady=5)

    def show_main_application(self):
        """Updates the main GUI after successful login."""
        if hasattr(self, 'user_info_label') and self.user_info_label.winfo_exists():
            self.user_info_label.config(
                text=f"Logged in as: {self.current_username} ({self.current_user_role})"
            )
        self.update_active_project_display()
        self.populate_navigation_menu()
        self.show_module_frame(constants.FRAME_PROJECT_STARTUP, ProjectStartupModuleFrame)

    def update_active_project_display(self):
        """Updates the active project label in the top frame."""
        if hasattr(self, 'active_project_label') and self.active_project_label.winfo_exists():
            if self.active_project_id and self.active_project_name:
                self.active_project_label.config(
                    text=f"Active Project: {self.active_project_name} (ID: {self.active_project_id})"
                )
            else:
                self.active_project_label.config(text="No Active Project Selected")

    def set_active_project(self, project_id, project_name):
        """Sets the active project for the application."""
        self.active_project_id = project_id
        self.active_project_name = project_name
        self.update_active_project_display()
        logger.info(f"Active project set to: ID {project_id}, Name: {project_name}")
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
            self.clear_active_project()
            logger.info("User logged out.")
            messagebox.showinfo("Logout", "You have been logged out.")
            for widget in list(self.activity_bar.winfo_children()):
                widget.destroy()
            for widget in list(self.side_bar.winfo_children()):
                widget.destroy()
            for widget in list(self.editor_area.winfo_children()):
                widget.destroy()
            self.module_frames = {}
            self.side_bar_frames = {}
            self.withdraw()
            self.create_login_window()

    def populate_navigation_menu(self):
        """Populates the activity bar with buttons for accessible modules."""
        for widget in self.activity_bar.winfo_children():
            widget.destroy()

        module_buttons_data = [
            ('Integration & Data Proc.', constants.FRAME_IDP, IntegrationDataProcessingModuleFrame),
            ('Project Startup', constants.FRAME_PROJECT_STARTUP, ProjectStartupModuleFrame),
            ('Execution Management', constants.FRAME_EXEC_MGMT, ExecutionManagementModuleFrame),
            ('Monitoring & Control', constants.FRAME_MON_CTRL, MonitoringControlModuleFrame),
            ('Reporting & Closeout', constants.FRAME_REP_CLOSE, ReportingCloseoutModuleFrame),
            ('Project Scheduling', constants.FRAME_SCHEDULING, SchedulingModuleFrame),
            ('Daily Log', constants.FRAME_DAILY_LOG, DailyLogModuleFrame),
            ('Purchasing & Logistics', constants.FRAME_PURCH_LOGISTICS, PurchasingLogisticsModuleFrame),
            ('Production & Prefab', constants.FRAME_PROD_PREFAB, ProductionPrefabModuleFrame),
            ('User Management', constants.FRAME_USER_MGMT, UserManagementModuleFrame),
            ('CRM', constants.FRAME_CRM, CRMModuleFrame), # Added CRM to navigation
        ]

        for text, module_name, frame_class in module_buttons_data:
            if self.user_manager.check_access(self.current_user_role, module_name):
                btn = ttk.Button(
                    self.activity_bar,
                    text=text,
                    style='Activity.TButton',
                    command=lambda m=module_name, fc=frame_class: self.show_module_frame(m, fc)
                )
                btn.pack(fill="x", pady=5, padx=5)

    def show_module_frame(self, module_name, frame_class=None):
        """Shows the selected module frame in the editor area."""
        for frame in self.module_frames.values():
            if frame.winfo_ismapped():
                frame.pack_forget()

        if module_name not in self.module_frames:
            if frame_class:
                actual_backend_module_key = None
                # Map FRAME constants to MODULE constants for fetching the backend instance
                if module_name == constants.FRAME_IDP:
                    actual_backend_module_key = constants.MODULE_INTEGRATION # Primary module for this combined frame
                elif module_name == constants.FRAME_PROJECT_STARTUP:
                    actual_backend_module_key = constants.MODULE_PROJECT_STARTUP
                elif module_name == constants.FRAME_EXEC_MGMT:
                    actual_backend_module_key = constants.MODULE_EXECUTION_MANAGEMENT
                elif module_name == constants.FRAME_MON_CTRL:
                    actual_backend_module_key = constants.MODULE_MONITORING_CONTROL
                elif module_name == constants.FRAME_REP_CLOSE:
                    actual_backend_module_key = constants.MODULE_REPORTING # Primary module for this combined frame
                elif module_name == constants.FRAME_USER_MGMT:
                    actual_backend_module_key = constants.MODULE_USER_MANAGEMENT
                elif module_name == constants.FRAME_CRM: # Added case for CRM
                    actual_backend_module_key = constants.MODULE_CRM
                # For FRAME_SCHEDULING, FRAME_DAILY_LOG, actual_backend_module_key remains None
                # if they don't have a direct primary backend module in self.modules.
                # Their frames must handle module_instance_to_pass being None.

                module_instance_to_pass = self.modules.get(actual_backend_module_key) if actual_backend_module_key else None

                # Special handling for frames that use a different module than their name might suggest
                if module_name in [constants.FRAME_PURCH_LOGISTICS, constants.FRAME_PROD_PREFAB]:
                    module_instance_to_pass = self.modules.get(constants.MODULE_PROJECT_STARTUP)
                    if not module_instance_to_pass:
                        logger.error(
                            f"{constants.MODULE_PROJECT_STARTUP} module instance not found for {module_name}. "
                            "Cannot initialize frame."
                        )
                        messagebox.showerror(
                            "Initialization Error",
                            f"Backend for {module_name} (via {constants.MODULE_PROJECT_STARTUP}) is not available.",
                            parent=self
                        )
                        return

                # If after all logic, module_instance_to_pass is still None for a frame that expects one,
                # it's an issue, but the frame's __init__ should be robust or this logic refined.
                # For example, if FRAME_IDP absolutely needs data_processing too, its __init__ could fetch it from self.app.modules.

                self.module_frames[module_name] = frame_class(
                    self.editor_area, self, module_instance_to_pass
                )
            else:
                messagebox.showerror("Error", f"Could not load frame for module: {module_name}")
                return

        self.module_frames[module_name].pack(fill="both", expand=True)
        logger.info(f"Displayed {module_name} module frame.")

        # Use constants for checking which sidebar to show
        if module_name == constants.FRAME_PROJECT_STARTUP or module_name == constants.FRAME_IDP:
            self.show_project_list_in_sidebar()
        else:
            self.hide_project_list_in_sidebar()

    def show_project_list_in_sidebar(self):
        if not hasattr(self, 'project_tree_frame') or self.project_tree_frame is None:
            self.project_tree_frame = ttk.LabelFrame(self.side_bar, text="Project List")
            self.project_tree = ttk.Treeview(self.project_tree_frame)
            self.project_tree["columns"] = (
                "ProjectID", "ProjectName", "EstimateDocsComplete", "WBSComplete", "Status"
            )
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

            scrollbar = ttk.Scrollbar(
                self.project_tree_frame, orient="vertical", command=self.project_tree.yview
            )
            self.project_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            self.project_tree.pack(side="left", fill="both", expand=True)

            refresh_button = ttk.Button(
                self.project_tree_frame, text="Refresh List", command=self.load_project_list_data
            )
            refresh_button.pack(side="bottom", pady=5)
            self.side_bar_frames['project_list'] = self.project_tree_frame

        if hasattr(self, 'project_tree_frame') and self.project_tree_frame.winfo_exists():
            self.project_tree_frame.pack(pady=10, padx=10, fill="both", expand=True)
            self.load_project_list_data()

    def hide_project_list_in_sidebar(self):
        if hasattr(self, 'project_tree_frame') and self.project_tree_frame is not None:
            self.project_tree_frame.pack_forget()

    def load_project_list_data(self):
        """Fetches project data and populates the Project List Treeview."""
        if not hasattr(self, 'project_tree') or self.project_tree is None:
            logger.error("Project tree in sidebar not initialized before loading data.")
            return

        for item in self.project_tree.get_children():
            self.project_tree.delete(item)

        project_startup_module = self.modules.get('project_startup')
        if project_startup_module and hasattr(project_startup_module, 'get_all_projects_with_status'):
            projects = project_startup_module.get_all_projects_with_status()
            if projects:
                for project in projects:
                    self.project_tree.insert(
                        "", tk.END,
                        values=(
                            project.get('ProjectID', 'N/A'),
                            project.get('ProjectName', 'N/A'),
                            project.get('EstimateDocsComplete', "N/A"),
                            project.get('WBSComplete', "N/A"),
                            project.get('StatusName', 'N/A')
                        )
                    )
            else:
                self.project_tree.insert("", tk.END, values=("", "No projects found.", "", "", ""))
        else:
            logger.error("Could not load projects. Project Startup module or method not available.")
            messagebox.showerror(
                "Error",
                "Could not load projects. Backend functionality missing.",
                parent=self
            )

if __name__ == "__main__":
    for directory in [Config.DATABASE_DIR, Config.DATA_DIR, Config.REPORTS_DIR, Config.ARCHIVE_DIR, Config.LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)

    _ = db_manager  # Initialize DB Manager

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
