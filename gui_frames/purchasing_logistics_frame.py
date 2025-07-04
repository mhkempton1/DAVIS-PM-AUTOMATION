import tkinter as tk
from tkinter import ttk, messagebox
import logging
from .base_frame import BaseModuleFrame
# from database_manager import db_manager # No longer needed

logger = logging.getLogger(__name__)

class PurchasingLogisticsModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.app = app
        self.module_instance = module_instance
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Purchasing & Logistics Management", style='Header.TLabel').pack(pady=10)

        request_frame = ttk.LabelFrame(self, text="Request Material (Internal Log)")
        request_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(request_frame, text="Project ID (Optional):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.req_project_id_entry = ttk.Entry(request_frame, width=40)
        self.req_project_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(request_frame, text="Material Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.req_material_desc_entry = ttk.Entry(request_frame, width=40)
        self.req_material_desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(request_frame, text="Quantity Requested:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.req_quantity_entry = ttk.Entry(request_frame, width=40)
        self.req_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(request_frame, text="Unit of Measure:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.req_uom_entry = ttk.Entry(request_frame, width=40)
        self.req_uom_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(request_frame, text="Urgency (Standard, Urgent, Critical):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.req_urgency_combobox = ttk.Combobox(request_frame, values=['Standard', 'Urgent', 'Critical'], width=38)
        self.req_urgency_combobox.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.req_urgency_combobox.set('Standard')

        ttk.Label(request_frame, text="Required By Date (YYYY-MM-DD):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.req_date_entry = ttk.Entry(request_frame, width=40)
        self.req_date_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(request_frame, text="Notes:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.req_notes_entry = ttk.Entry(request_frame, width=40)
        self.req_notes_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        submit_req_button = ttk.Button(request_frame, text="Submit Material Request", command=self.submit_material_request)
        submit_req_button.grid(row=7, column=0, columnspan=2, pady=10)

        display_frame = ttk.LabelFrame(self, text="Pending Internal Material Requests (Purchasing_Log)")
        display_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.requests_tree = ttk.Treeview(display_frame, columns=("LogID", "ProjectID", "Material", "Qty", "UoM", "Urgency", "ReqDate", "Status", "Created"), show="headings")
        # ... (Treeview headings and column configurations remain the same) ...
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
        self.load_pending_requests()

    def submit_material_request(self):
        project_id_str = self.req_project_id_entry.get().strip()
        project_id = None
        if project_id_str:
            try:
                project_id = int(project_id_str)
            except ValueError:
                self.show_message("Input Error", "Project ID must be a valid number if provided.", True, parent=self)
                return
        elif self.app.active_project_id is not None:
            project_id = self.app.active_project_id

        material_description = self.req_material_desc_entry.get().strip()
        quantity_str = self.req_quantity_entry.get().strip()
        unit_of_measure = self.req_uom_entry.get().strip()
        urgency_level = self.req_urgency_combobox.get().strip()
        required_by_date_str = self.req_date_entry.get().strip()
        required_by_date = required_by_date_str if required_by_date_str else None
        notes = self.req_notes_entry.get().strip()

        if not material_description or not quantity_str:
            self.show_message("Input Error", "Material Description and Quantity are required.", True, parent=self)
            return
        try:
            quantity_requested = float(quantity_str)
        except ValueError:
            self.show_message("Input Error", "Quantity must be a valid number.", True, parent=self)
            return

        user_details = self.app.user_manager.get_user_details_by_username(self.app.current_username)
        employee_db_id = user_details.get('employee_db_id') if user_details else None

        if employee_db_id is None:
            # Option 1: Show error and prevent submission
            self.show_message("User Error", "Your app user is not linked to an Employee record. Cannot submit material request.", True, parent=self)
            logger.warning(f"Material request submission blocked for app user {self.app.current_username} due to missing EmployeeID link.")
            return
            # Option 2: Use a placeholder (less ideal for required FKs if backend doesn't handle it)
            # logger.warning(f"No linked EmployeeID for app user {self.app.current_username} for material request. Using placeholder 1.")
            # employee_db_id = 1 # Placeholder, assuming EmployeeID 1 is a generic/system user

        if self.module_instance and hasattr(self.module_instance, 'add_material_request'):
            success, msg, log_id = self.module_instance.add_material_request(
                project_id=project_id,
                requested_by_employee_id=employee_db_id, # Use the actual EmployeeID
                material_description=material_description,
                quantity_requested=quantity_requested,
                unit_of_measure=unit_of_measure,
                urgency_level=urgency_level,
                required_by_date=required_by_date,
                notes=notes
            )
            self.show_message("Material Request", msg, is_error=not success, parent=self)
            if success:
                self.load_pending_requests()
                self.req_project_id_entry.delete(0, tk.END)
                self.req_material_desc_entry.delete(0, tk.END)
                self.req_quantity_entry.delete(0, tk.END)
                self.req_uom_entry.delete(0, tk.END)
                self.req_urgency_combobox.set('Standard')
                self.req_date_entry.delete(0, tk.END)
                self.req_notes_entry.delete(0, tk.END)
        else:
            self.show_message("Error", "Purchasing backend module not available.", True, parent=self)
            logger.error("Module instance or add_material_request method not found.")

    def load_pending_requests(self):
        for i in self.requests_tree.get_children():
            self.requests_tree.delete(i)

        if self.module_instance and hasattr(self.module_instance, 'get_pending_material_requests'):
            try:
                requests = self.module_instance.get_pending_material_requests()
                if requests:
                    for req in requests:
                        self.requests_tree.insert("", "end", values=(
                            req.get('InternalLogID'),
                            req.get('ProjectID', "N/A"),
                            req.get('MaterialDescription'),
                            req.get('QuantityRequested'),
                            req.get('UnitOfMeasure'),
                            req.get('UrgencyLevel'),
                            req.get('RequiredByDate', "N/A"),
                            req.get('Status'),
                            req.get('DateCreated')
                        ))
                else:
                    logger.info("No pending material requests found by backend.")
            except Exception as e:
                logger.error(f"Error loading pending material requests from backend: {e}", exc_info=True)
                self.show_message("Load Error", f"Failed to load pending requests: {e}", True, parent=self)
        else:
            self.show_message("Error", "Backend for loading material requests not available.", True, parent=self)
            logger.error("Module instance or get_pending_material_requests not found.")

    def on_active_project_changed(self):
        logger.info("PurchasingLogisticsModuleFrame: Active project changed.")
        if self.app.active_project_id:
            self.req_project_id_entry.delete(0, tk.END)
            self.req_project_id_entry.insert(0, str(self.app.active_project_id))
        else:
            self.req_project_id_entry.delete(0, tk.END)
        self.load_pending_requests()
