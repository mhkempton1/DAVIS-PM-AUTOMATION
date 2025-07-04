import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
from .base_frame import BaseModuleFrame
from configuration import Config # For Config.get_data_dir() if used for fallbacks

# Logger setup
import logging
logger = logging.getLogger(__name__)

class ExecutionManagementModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        # Initialize all widget attributes that might be accessed
        self.info_label = None
        self.cost_wbs_id_entry = None
        self.cost_category_entry = None
        self.cost_description_entry = None
        self.cost_amount_entry = None
        self.cost_date_entry = None
        self.record_cost_button = None
        self.task_id_entry_for_progress = None
        self.task_actual_start_date_entry = None
        self.task_actual_end_date_entry = None
        self.progress_percent_entry = None
        self.task_actual_hours_entry = None
        self.task_status_combo = None
        self.task_lead_employee_id_entry = None
        self.progress_notes_entry = None
        self.update_task_progress_button = None
        self.material_name_entry = None
        self.material_qty_entry = None
        self.material_unit_entry = None
        self.material_cost_code_entry = None
        self.material_supplier_entry = None
        self.log_material_button = None
        self.schedule_task_id_entry = None
        self.schedule_end_date_entry = None
        self.schedule_status_entry = None
        self.update_schedule_task_button = None

        self.task_status_list = [] # For combobox
        self.task_status_display_names = ["(Select Status)"]


        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Execution Management Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        self.info_label = tk.Label(self, text="Select an active project via Project Planning module.", font=("Arial", 10, "italic"))
        self.info_label.pack(pady=5)

        # --- Record Actual Cost ---
        cost_frame = ttk.LabelFrame(self, text="Record Actual Cost")
        cost_frame.pack(pady=10, padx=20, fill="x")
        cost_frame.columnconfigure(1, weight=1)

        cost_fields = [
            ("WBS Element ID (optional):", "cost_wbs_id_entry"),
            ("Cost Category:", "cost_category_entry"),
            ("Description:", "cost_description_entry"),
            ("Amount:", "cost_amount_entry"),
            ("Date (YYYY-MM-DD, optional):", "cost_date_entry")
        ]
        for i, (label_text, entry_attr) in enumerate(cost_fields):
            tk.Label(cost_frame, text=label_text).grid(row=i, column=0, padx=5, pady=2, sticky="w")
            entry = tk.Entry(cost_frame)
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
            setattr(self, entry_attr, entry)
        self.record_cost_button = ttk.Button(cost_frame, text="Record Cost for Active Project", command=self.record_cost_action)
        self.record_cost_button.grid(row=len(cost_fields), column=0, columnspan=2, pady=10)

        # --- Record Progress Update ---
        progress_frame = ttk.LabelFrame(self, text="Update Task Progress / Record Actuals")
        progress_frame.pack(pady=10, padx=20, fill="x")
        progress_frame.columnconfigure(1, weight=1)

        tk.Label(progress_frame, text="Task ID:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.task_id_entry_for_progress = tk.Entry(progress_frame)
        self.task_id_entry_for_progress.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(progress_frame, text="Actual Start (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.task_actual_start_date_entry = tk.Entry(progress_frame)
        self.task_actual_start_date_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(progress_frame, text="Actual End (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.task_actual_end_date_entry = tk.Entry(progress_frame)
        self.task_actual_end_date_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(progress_frame, text="Completion % (0-100):").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.progress_percent_entry = tk.Entry(progress_frame)
        self.progress_percent_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(progress_frame, text="Actual Hours:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.task_actual_hours_entry = tk.Entry(progress_frame)
        self.task_actual_hours_entry.grid(row=4, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(progress_frame, text="Task Status:").grid(row=5, column=0, padx=5, pady=2, sticky="w")
        # Populate task_status_list and task_status_display_names
        execution_module = self.app.modules.get('execution_management')
        if execution_module and hasattr(execution_module, 'get_all_task_statuses'):
            self.task_status_list = execution_module.get_all_task_statuses() # List of dicts
            if self.task_status_list:
                self.task_status_display_names.extend([s['StatusName'] for s in self.task_status_list])
        if not self.task_status_list: # Fallback if empty or module error
             logger.warning("No task statuses fetched from backend for combobox. Using fallback.")
             self.task_status_display_names.extend(['Pending', 'In Progress', 'Completed', 'Blocked', 'Cancelled'])

        self.task_status_combo = ttk.Combobox(progress_frame, values=self.task_status_display_names, state="readonly")
        self.task_status_combo.grid(row=5, column=1, padx=5, pady=2, sticky="ew")
        self.task_status_combo.set(self.task_status_display_names[0])


        tk.Label(progress_frame, text="Lead Employee ID (optional):").grid(row=6, column=0, padx=5, pady=2, sticky="w")
        self.task_lead_employee_id_entry = tk.Entry(progress_frame)
        self.task_lead_employee_id_entry.grid(row=6, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(progress_frame, text="Notes (optional):").grid(row=7, column=0, padx=5, pady=2, sticky="w")
        self.progress_notes_entry = tk.Entry(progress_frame)
        self.progress_notes_entry.grid(row=7, column=1, padx=5, pady=2, sticky="ew")

        self.update_task_progress_button = ttk.Button(progress_frame, text="Update Task Progress", command=self.update_task_progress_action)
        self.update_task_progress_button.grid(row=8, column=0, columnspan=2, pady=10)

        # --- Report Integration Section ---
        # report_integration_frame = ttk.LabelFrame(self, text="External Report Integration")
        # report_integration_frame.pack(pady=10, padx=20, fill="x")
        # ttk.Button(report_integration_frame, text="Import Exaktime Report (Placeholder)", command=self.import_exaktime_placeholder).pack(side="left", padx=5, pady=5)
        # ttk.Button(report_integration_frame, text="Import QuickBooks Report (Placeholder)", command=self.import_quickbooks_placeholder).pack(side="left", padx=5, pady=5)

        # --- Material Information Input Section ---
        material_frame = ttk.LabelFrame(self, text="Log Material Usage")
        material_frame.pack(pady=10, padx=20, fill="x")
        material_frame.columnconfigure(1, weight=1)

        tk.Label(material_frame, text="Material Stock # or Name:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.material_name_entry = tk.Entry(material_frame)
        self.material_name_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        tk.Label(material_frame, text="Quantity:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.material_qty_entry = tk.Entry(material_frame)
        self.material_qty_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        tk.Label(material_frame, text="Unit (e.g., pcs, ft):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.material_unit_entry = tk.Entry(material_frame)
        self.material_unit_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        tk.Label(material_frame, text="Cost Code (optional):").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.material_cost_code_entry = tk.Entry(material_frame)
        self.material_cost_code_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        tk.Label(material_frame, text="Supplier (optional):").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.material_supplier_entry = tk.Entry(material_frame)
        self.material_supplier_entry.grid(row=4, column=1, padx=5, pady=2, sticky="ew")
        self.log_material_button = ttk.Button(material_frame, text="Log Material", command=self.log_material_action)
        self.log_material_button.grid(row=5, column=0, columnspan=2, pady=10)

        # --- Schedule Updates Section (Placeholder) ---
        # schedule_update_frame = ttk.LabelFrame(self, text="Schedule Task Updates")
        # schedule_update_frame.pack(pady=10, padx=20, fill="x")
        # ... (widgets for schedule update) ...
        # self.update_schedule_task_button = ttk.Button(schedule_update_frame, text="Update Schedule Task", command=self.update_schedule_task_action)

        # --- Document Upload Section (Placeholder) ---
        # doc_upload_frame = ttk.LabelFrame(self, text="Supplemental Documents & Schedules")
        # ... (buttons for upload) ...

        self.on_active_project_changed()

    # Placeholder methods for features not fully implemented or moved
    # def import_exaktime_placeholder(self): self.show_message("Placeholder", "Exaktime import to be implemented.")
    # def import_quickbooks_placeholder(self): self.show_message("Placeholder", "QuickBooks import to be implemented.")
    # def update_schedule_task_action(self): self.show_message("Placeholder", "Schedule update logic to be implemented.")
    # def upload_document(self, doc_type): self.show_message("Placeholder", f"Upload for {doc_type} to be implemented.")

    def on_active_project_changed(self):
        is_project_active = bool(self.app.active_project_id)
        state = "normal" if is_project_active else "disabled"

        if self.info_label:
            self.info_label.config(text=f"Actions apply to: {self.app.active_project_name} (ID: {self.app.active_project_id})" if is_project_active else "No active project. Select in 'Project Startup'.")

        if self.record_cost_button: self.record_cost_button.config(state=state)
        if self.update_task_progress_button: self.update_task_progress_button.config(state=state)
        if self.log_material_button: self.log_material_button.config(state=state)
        # if self.update_schedule_task_button: self.update_schedule_task_button.config(state=state)
        # Enable/disable other buttons as needed

    def record_cost_action(self):
        if not self.module: self.show_message("Error", "Execution Module not available.", True); return
        if not self.app.active_project_id: self.show_message("Error", "No active project.", True); return

        project_id = self.app.active_project_id
        try:
            wbs_id_str = self.cost_wbs_id_entry.get().strip()
            wbs_element_id = int(wbs_id_str) if wbs_id_str else None
            cost_category = self.cost_category_entry.get().strip()
            description = self.cost_description_entry.get().strip()
            amount_str = self.cost_amount_entry.get().strip()
            if not cost_category or not description or not amount_str:
                self.show_message("Input Error", "Cost category, description, and amount are required.", True); return
            amount = float(amount_str)
            if amount <= 0:
                self.show_message("Input Error", "Amount must be positive.", True); return

            transaction_date = self.cost_date_entry.get().strip() or None # Optional date

            success, msg = self.module.record_actual_cost(
                project_id, wbs_element_id, cost_category, description, amount, transaction_date
            )
            self.show_message("Record Cost", msg, not success)
            if success: # Clear fields
                self.cost_wbs_id_entry.delete(0, tk.END)
                self.cost_category_entry.delete(0, tk.END)
                self.cost_description_entry.delete(0, tk.END)
                self.cost_amount_entry.delete(0, tk.END)
                self.cost_date_entry.delete(0, tk.END)
        except ValueError:
            self.show_message("Input Error", "Invalid Amount. Must be a number.", True)
        except Exception as e:
            logger.error(f"Error in record_cost_action: {e}", exc_info=True)
            self.show_message("Error", f"An unexpected error occurred: {e}", True)

    def update_task_progress_action(self):
        if not self.module: self.show_message("Error", "Execution Module not available.", True); return
        if not self.app.active_project_id: self.show_message("Error", "No active project.", True); return

        try:
            task_id_str = self.task_id_entry_for_progress.get().strip()
            if not task_id_str: self.show_message("Input Error", "Task ID is required.", True); return
            task_id = int(task_id_str)

            actual_start_date = self.task_actual_start_date_entry.get().strip() or None
            actual_end_date = self.task_actual_end_date_entry.get().strip() or None

            percent_str = self.progress_percent_entry.get().strip()
            percent_complete = float(percent_str) if percent_str else None
            if percent_complete is not None and not (0.0 <= percent_complete <= 100.0):
                self.show_message("Input Error", "Completion % must be 0-100.", True); return

            actual_hours_str = self.task_actual_hours_entry.get().strip()
            actual_hours = float(actual_hours_str) if actual_hours_str else None

            status_name = self.task_status_combo.get().strip()
            task_status_id = None
            if status_name and status_name != "(Select Status)":
                selected_status = next((s for s in self.task_status_list if s['StatusName'] == status_name), None)
                if selected_status: task_status_id = selected_status['TaskStatusID']
                # Else: status_name might be a fallback, backend needs to handle by name if ID not found

            lead_emp_id_str = self.task_lead_employee_id_entry.get().strip()
            lead_employee_id = int(lead_emp_id_str) if lead_emp_id_str else None
            notes = self.progress_notes_entry.get().strip() or None

            success, msg = self.module.update_task_details(
                task_id=task_id, project_id=self.app.active_project_id, # Pass project_id if method needs it
                actual_start_date=actual_start_date, actual_end_date=actual_end_date,
                percent_complete=percent_complete, task_status_id=task_status_id,
                notes=notes, lead_employee_id=lead_employee_id, actual_hours=actual_hours
            )
            self.show_message("Update Task", msg, not success)
            if success: # Clear relevant fields
                for entry in [self.task_id_entry_for_progress, self.task_actual_start_date_entry,
                              self.task_actual_end_date_entry, self.progress_percent_entry,
                              self.task_actual_hours_entry, self.task_lead_employee_id_entry,
                              self.progress_notes_entry]:
                    entry.delete(0, tk.END)
                self.task_status_combo.set("(Select Status)")
        except ValueError:
            self.show_message("Input Error", "Invalid numeric value (ID, %, hours).", True)
        except Exception as e:
            logger.error(f"Error in update_task_progress_action: {e}", exc_info=True)
            self.show_message("Error", f"An unexpected error occurred: {e}", True)

    def log_material_action(self):
        if not self.module: self.show_message("Error", "Execution Module not available.", True); return
        if not self.app.active_project_id: self.show_message("Error", "No active project.", True); return

        project_id = self.app.active_project_id
        material_identifier = self.material_name_entry.get().strip() # Stock# or Name
        qty_str = self.material_qty_entry.get().strip()
        unit = self.material_unit_entry.get().strip()

        if not material_identifier or not qty_str:
            self.show_message("Input Error", "Material Stock #/Name and Quantity are required.", True); return
        try:
            quantity = float(qty_str)
            if quantity <= 0: self.show_message("Input Error", "Quantity must be positive.", True); return
        except ValueError:
            self.show_message("Input Error", "Quantity must be a number.", True); return

        cost_code = self.material_cost_code_entry.get().strip() or None
        supplier = self.material_supplier_entry.get().strip() or None

        user_details = self.app.user_manager.get_user_details_by_username(self.app.current_username)
        employee_db_id = user_details.get('employee_db_id') if user_details else None

        if employee_db_id is None:
            self.show_message("User Error", "Current user not linked to an Employee record. Cannot log material.", True, parent=self)
            logger.warning(f"Material log blocked for app user {self.app.current_username} due to missing EmployeeID link.")
            return

        success, msg = self.module.log_material_to_db(
            project_id=project_id,
            material_stock_number=material_identifier,
            quantity=quantity, unit=unit, supplier=supplier, cost_code=cost_code,
            recorded_by_employee_id=employee_db_id # Pass the actual EmployeeID
        )
        self.show_message("Log Material", msg, is_error=not success)
        if success: # Clear fields
            for entry in [self.material_name_entry, self.material_qty_entry, self.material_unit_entry,
                          self.material_cost_code_entry, self.material_supplier_entry]:
                entry.delete(0, tk.END)
        # Fallback to CSV logging if DB method fails is handled in backend module.
