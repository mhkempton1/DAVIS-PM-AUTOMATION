import tkinter as tk
from tkinter import ttk, messagebox
import logging
from .base_frame import BaseModuleFrame
# from database_manager import db_manager # No longer needed

logger = logging.getLogger(__name__)

class ProductionPrefabModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.app = app
        self.module_instance = module_instance
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Production & Prefabrication Management", style='Header.TLabel').pack(pady=10)

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

        prod_display_frame = ttk.LabelFrame(self, text="Active Production Orders (Production_Assembly_Tracking)")
        prod_display_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.orders_tree = ttk.Treeview(prod_display_frame, columns=("ProdID", "AssemblyID", "ProjectID", "Qty", "Status", "StartDate", "EndDate", "AssignedTo", "Created"), show="headings")
        self.orders_tree.heading("ProdID", text="Prod ID")
        self.orders_tree.heading("AssemblyID", text="Assembly ID")
        # ... (rest of headings and column configs)
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
        self.load_production_orders()

    def submit_production_order(self):
        assembly_id_str = self.prod_assembly_id_entry.get().strip()
        project_id_str = self.prod_project_id_entry.get().strip()
        quantity_str = self.prod_quantity_entry.get().strip()
        assigned_emp_id_str = self.prod_assigned_emp_id_entry.get().strip()
        start_date_str = self.prod_start_date_entry.get().strip()
        start_date = start_date_str if start_date_str else None
        completion_date_str = self.prod_completion_date_entry.get().strip()
        completion_date = completion_date_str if completion_date_str else None
        notes = self.prod_notes_entry.get().strip()

        if not assembly_id_str or not quantity_str:
            self.show_message("Input Error", "Assembly ID and Quantity to Produce are required.", True, parent=self)
            return

        try:
            assembly_id = int(assembly_id_str)
            quantity_to_produce = float(quantity_str)
            project_id = None
            if project_id_str:
                project_id = int(project_id_str)
            elif self.app.active_project_id is not None:
                project_id = self.app.active_project_id

            assigned_to_employee_id = None # This is the Employees.EmployeeID
            if assigned_emp_id_str:
                assigned_to_employee_id = int(assigned_emp_id_str)
            elif self.app.current_username: # Default to current user's linked EmployeeID if field is empty
                user_details = self.app.user_manager.get_user_details_by_username(self.app.current_username)
                employee_db_id = user_details.get('employee_db_id') if user_details else None
                if employee_db_id:
                    assigned_to_employee_id = employee_db_id
                    logger.info(f"Defaulting AssignedToEmployeeID to current user's linked EmployeeID: {employee_db_id}")
                else:
                    # If current user is not linked, allow unassigned if backend/schema supports NULL for AssignedToEmployeeID
                    logger.warning(f"No linked EmployeeID for current user {self.app.current_username}. Production order will be unassigned if no manual ID entered.")
                    # assigned_to_employee_id remains None, which is fine as the DB column is nullable.
            # If assigned_emp_id_str was empty AND no current_username, assigned_to_employee_id remains None.

        except ValueError:
            self.show_message("Input Error", "Assembly ID, Project ID, Quantity, and Assigned Employee ID (if provided) must be valid numbers.", True, parent=self)
            return

        if self.module_instance and hasattr(self.module_instance, 'create_production_assembly_order'):
            success, msg, prod_id = self.module_instance.create_production_assembly_order(
                assembly_id=assembly_id,
                project_id=project_id,
                quantity_to_produce=quantity_to_produce,
                assigned_to_employee_id=assigned_to_employee_id, # This should now be the correct EmployeeID or None
                start_date=start_date,
                completion_date=completion_date,
                notes=notes
            )
            self.show_message("Create Production Order", msg, is_error=not success, parent=self)
            if success:
                self.load_production_orders()
                self.prod_assembly_id_entry.delete(0, tk.END)
                self.prod_project_id_entry.delete(0, tk.END)
                self.prod_quantity_entry.delete(0, tk.END)
                self.prod_assigned_emp_id_entry.delete(0, tk.END)
                self.prod_start_date_entry.delete(0, tk.END)
                self.prod_completion_date_entry.delete(0, tk.END)
                self.prod_notes_entry.delete(0, tk.END)
        else:
            self.show_message("Error", "Production backend module not available.", True, parent=self)
            logger.error("Module instance or create_production_assembly_order method not found.")

    def load_production_orders(self):
        for i in self.orders_tree.get_children():
            self.orders_tree.delete(i)

        if self.module_instance and hasattr(self.module_instance, 'get_active_production_orders'):
            try:
                orders = self.module_instance.get_active_production_orders()
                if orders:
                    for order in orders:
                        self.orders_tree.insert("", "end", values=(
                            order.get('ProductionID'),
                            order.get('AssemblyID'),
                            order.get('ProjectID', "N/A"),
                            order.get('QuantityToProduce'),
                            order.get('Status'),
                            order.get('StartDate', "N/A"),
                            order.get('CompletionDate', "N/A"),
                            order.get('AssignedToEmployeeID', "N/A"),
                            order.get('DateCreated')
                        ))
                else:
                    logger.info("No active production orders found by backend.")
            except Exception as e:
                logger.error(f"Error loading production orders from backend: {e}", exc_info=True)
                self.show_message("Load Error", f"Failed to load production orders: {e}", True, parent=self)
        else:
            self.show_message("Error", "Backend for loading production orders not available.", True, parent=self)
            logger.error("Module instance or get_active_production_orders not found.")

    def on_active_project_changed(self):
        logger.info("ProductionPrefabModuleFrame: Active project changed.")
        if self.app.active_project_id:
            self.prod_project_id_entry.delete(0, tk.END)
            self.prod_project_id_entry.insert(0, str(self.app.active_project_id))
        else:
            self.prod_project_id_entry.delete(0, tk.END)
        self.load_production_orders()
