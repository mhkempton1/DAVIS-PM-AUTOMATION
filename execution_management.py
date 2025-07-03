import logging
from database_manager import db_manager # Assuming global db_manager for now, refactor to DI later
from datetime import datetime

logger = logging.getLogger(__name__)

class ExecutionManagement:
    """
    Handles the execution phase of a project, including recording actual costs,
    progress updates, material usage, and managing schedule updates.
    """

    def __init__(self, db_m_instance): # Removed default None and global fallback
        if db_m_instance is None:
            raise ValueError("DatabaseManager instance is required for ExecutionManagement.")
        self.db_manager = db_m_instance
        logger.info("Execution Management module initialized with provided db_manager.")

    def record_actual_cost(self, project_id, wbs_element_id, cost_category, description, amount, transaction_date=None):
        """
        Records an actual cost incurred on a project.
        Args:
            project_id (int): The ID of the project.
            wbs_element_id (int, optional): The ID of the WBS element this cost is associated with.
            cost_category (str): Category of the cost (e.g., Labor, Material, Subcontractor).
            description (str): Description of the cost item.
            amount (float): The amount of the cost.
            transaction_date (str, optional): Date of the transaction (YYYY-MM-DD). Defaults to current date.
        Returns:
            tuple: (bool success, str message)
        """
        if not project_id or not cost_category or not description or amount is None:
            return False, "Project ID, cost category, description, and amount are required."
        if amount <= 0:
            return False, "Cost amount must be positive."

        if transaction_date is None:
            transaction_date = datetime.now().strftime("%Y-%m-%d")

        # Ensure transaction_date is in YYYY-MM-DD format if provided
        try:
            datetime.strptime(transaction_date, "%Y-%m-%d")
        except ValueError:
            return False, "Invalid transaction_date format. Please use YYYY-MM-DD."

        query = """
        INSERT INTO actual_costs (ProjectID, WBSElementID, CostCategory, Description, Amount, TransactionDate, RecordedDate)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        # Schema: ActualCostID, ProjectID, WBSElementID, TaskID, CostCategory, Description, Amount, TransactionDate, VendorID, PurchaseOrderID, Notes, RecordedDate
        # For simplicity, TaskID, VendorID, PurchaseOrderID, Notes are omitted here but can be added.
        params = (project_id, wbs_element_id, cost_category, description, amount, transaction_date)

        success = self.db_manager.execute_query(query, params, commit=True)
        if success:
            last_id = self.db_manager.execute_query("SELECT last_insert_rowid()", fetch_one=True)[0]
            logger.info(f"Actual cost (ID: {last_id}) of {amount} for project {project_id} (WBS: {wbs_element_id}) recorded successfully.")
            return True, f"Actual cost recorded successfully with ID {last_id}."
        else:
            logger.error(f"Failed to record actual cost for project {project_id}.")
            return False, "Failed to record actual cost (database error)."

    def get_all_task_statuses(self):
        """
        Retrieves all available task statuses from the TaskStatuses table.
        Returns:
            list: A list of dictionaries, where each dictionary contains TaskStatusID and StatusName.
                  Returns an empty list if no statuses are found or an error occurs.
        """
        query = "SELECT TaskStatusID, StatusName FROM TaskStatuses ORDER BY TaskStatusID;"
        try:
            status_rows = self.db_manager.execute_query(query, fetch_all=True)
            if status_rows:
                return [dict(row) for row in status_rows]
            return []
        except Exception as e:
            logger.error(f"Error fetching task statuses: {e}", exc_info=True)
            return []

    def update_task_details(self, task_id, actual_start_date=None, actual_end_date=None,
                            percent_complete=None, task_status_id=None, notes=None,
                            lead_employee_id=None, actual_hours=None):
        """
        Updates details for a specific task in the 'Tasks' table.
        Args:
            task_id (int): The ID of the task to update.
            All other arguments are optional and will only be updated if provided.
        Returns:
            tuple: (bool success, str message)
        """
        if not task_id:
            return False, "Task ID is required to update task details."

        # Check if task exists
        task_exists_query = "SELECT TaskID FROM Tasks WHERE TaskID = ?"
        if not self.db_manager.execute_query(task_exists_query, (task_id,), fetch_one=True):
            return False, f"Task with ID {task_id} not found."

        update_fields = []
        params = []

        if actual_start_date is not None:
            try: datetime.strptime(actual_start_date, "%Y-%m-%d")
            except ValueError: return False, "Invalid Actual Start Date format. Use YYYY-MM-DD."
            update_fields.append("ActualStartDate = ?")
            params.append(actual_start_date)

        if actual_end_date is not None:
            try: datetime.strptime(actual_end_date, "%Y-%m-%d")
            except ValueError: return False, "Invalid Actual End Date format. Use YYYY-MM-DD."
            update_fields.append("ActualEndDate = ?")
            params.append(actual_end_date)

        if percent_complete is not None:
            try:
                pc = float(percent_complete)
                if not (0.0 <= pc <= 100.0):
                    return False, "Percent complete must be between 0 and 100."
                update_fields.append("PercentComplete = ?")
                params.append(pc)
            except ValueError:
                return False, "Invalid Percent Complete value."

        if task_status_id is not None:
            # Validate task_status_id exists
            status_exists_query = "SELECT TaskStatusID FROM TaskStatuses WHERE TaskStatusID = ?"
            if not self.db_manager.execute_query(status_exists_query, (task_status_id,), fetch_one=True):
                 return False, f"TaskStatusID {task_status_id} is invalid."
            update_fields.append("TaskStatusID = ?")
            params.append(task_status_id)

        if notes is not None: # Allow empty string for notes to clear it
            update_fields.append("Notes = ?")
            params.append(notes)

        if lead_employee_id is not None:
            # Optionally, validate EmployeeID exists in Employees table
            update_fields.append("LeadEmployeeID = ?")
            params.append(lead_employee_id)

        if actual_hours is not None:
            try:
                ah = float(actual_hours)
                if ah < 0: return False, "Actual hours cannot be negative."
                update_fields.append("ActualHours = ?")
                params.append(ah)
            except ValueError:
                return False, "Invalid Actual Hours value."

        if not update_fields:
            return True, "No details provided to update for the task." # Not an error, just no action

        update_fields.append("LastModifiedDate = CURRENT_TIMESTAMP")

        query = f"UPDATE Tasks SET {', '.join(update_fields)} WHERE TaskID = ?"
        params.append(task_id)

        success = self.db_manager.execute_query(query, tuple(params), commit=True)
        if success:
            logger.info(f"Task ID {task_id} updated successfully.")
            return True, f"Task ID {task_id} updated successfully."
        else:
            logger.error(f"Failed to update task ID {task_id}.")
            return False, f"Failed to update task ID {task_id} (database error)."

    def log_material_to_db(self, project_id, material_stock_number, quantity, unit=None,
                           supplier=None, cost_code=None, wbs_element_id=None, task_id=None,
                           recorded_by_employee_id=None, notes=None):
        """
        Logs material usage to the MaterialLog table.
        It first looks up MaterialSystemID from the Materials table using material_stock_number.
        """
        if not project_id or not material_stock_number or quantity is None:
            return False, "Project ID, Material Stock Number, and Quantity are required."
        if float(quantity) <= 0:
            return False, "Quantity must be positive."

        # Get MaterialSystemID from Materials table
        material_query = "SELECT MaterialSystemID FROM Materials WHERE StockNumber = ?"
        material_row = self.db_manager.execute_query(material_query, (material_stock_number,), fetch_one=True)
        if not material_row:
            return False, f"Material with Stock Number '{material_stock_number}' not found in Item Master."
        material_system_id = material_row['MaterialSystemID']

        transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = """
        INSERT INTO MaterialLog (
            ProjectID, MaterialStockNumber, TaskID, WBSElementID, QuantityUsed, Unit,
            CostCode, Supplier, TransactionDate, RecordedByEmployeeID, Notes, MaterialSystemID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            project_id, material_stock_number, task_id, wbs_element_id, quantity, unit,
            cost_code, supplier, transaction_date, recorded_by_employee_id, notes, material_system_id
        )

        success = self.db_manager.execute_query(query, params, commit=True)
        if success:
            log_id = self.db_manager.execute_query("SELECT last_insert_rowid()", fetch_one=True)[0]
            logger.info(f"Material Log (ID: {log_id}) for stock# {material_stock_number} (Qty: {quantity}) for project {project_id} recorded.")
            return True, f"Material usage logged successfully with ID {log_id}."
        else:
            logger.error(f"Failed to log material usage for project {project_id}, stock# {material_stock_number}.")
            return False, "Failed to log material usage (database error)."

    # Placeholder for schedule task update - more complex, involves Task table and potentially Project schedule
    def update_task_schedule(self, task_id, new_end_date=None, new_status_id=None):
        """
        Updates schedule-related information for a task.
        (This is a basic version, a full scheduling system would be more complex)
        """
        logger.info(f"Attempting to update schedule for Task ID: {task_id} - New EndDate: {new_end_date}, New StatusID: {new_status_id}")
        # This would typically update Tasks.ScheduledEndDate, Tasks.TaskStatusID, etc.
        # For now, let's call the more generic update_task_details

        updates_made = False
        final_message = []

        if new_end_date:
            # Validate date format
            try: datetime.strptime(new_end_date, "%Y-%m-%d")
            except ValueError: return False, "Invalid New End Date format. Use YYYY-MM-DD."

            # This is an example of how to call update_task_details for specific fields.
            # However, update_task_details doesn't have a specific field for ScheduledEndDate.
            # It has ActualEndDate. This indicates a potential mismatch or need for refinement in Task table updates.
            # For now, this function is a placeholder.
            # A more direct update to ScheduledEndDate in Tasks table might be:
            # success_date, msg_date = self.db_manager.execute_query(
            #    "UPDATE Tasks SET ScheduledEndDate = ?, LastModifiedDate = CURRENT_TIMESTAMP WHERE TaskID = ?",
            #    (new_end_date, task_id), commit=True)
            # if success_date: final_message.append(f"ScheduledEndDate updated to {new_end_date}.")
            # else: final_message.append(f"Failed to update ScheduledEndDate.")
            # updates_made = updates_made or success_date
            logger.warning("Updating ScheduledEndDate via update_task_schedule is not fully implemented through update_task_details. Needs direct SQL or method enhancement.")
            final_message.append("ScheduledEndDate update is conceptual in this version.")


        if new_status_id:
            success_status, msg_status = self.update_task_details(task_id, task_status_id=new_status_id)
            if success_status: final_message.append(f"TaskStatusID updated to {new_status_id}.")
            else: final_message.append(f"Failed to update TaskStatusID: {msg_status}")
            updates_made = updates_made or success_status

        if not updates_made and not new_end_date: # new_end_date isn't really "made" yet
             return True, "No schedule information provided to update."

        return updates_made, " ".join(final_message)


if __name__ == "__main__":
    # Example Usage (requires database to be set up with schema and some data)
    # Ensure db_manager is initialized (typically done when db_manager.py is imported)

    logger.info("--- Testing Execution Management Module ---")

    # Assuming Project ID 1 and WBS Element ID 1 exist from previous steps / manual setup
    test_project_id = 1
    test_wbs_element_id = 1 # e.g., Mobilization WBS
    test_task_id = 1 # Assume a task exists or create one for testing

    exec_mgmt = ExecutionManagement()

    # 1. Record Actual Cost
    print("\n1. Recording Actual Cost...")
    cost_success, cost_msg = exec_mgmt.record_actual_cost(
        project_id=test_project_id,
        wbs_element_id=test_wbs_element_id,
        cost_category="Labor",
        description="Site Supervisor Hours",
        amount=1250.75,
        transaction_date="2024-07-20"
    )
    print(f"Record Cost Result: {cost_success} - {cost_msg}")

    cost_success_2, cost_msg_2 = exec_mgmt.record_actual_cost(
        project_id=test_project_id,
        wbs_element_id=None, # Project-level cost
        cost_category="Permits",
        description="City Construction Permit",
        amount=500.00
    )
    print(f"Record Project-Level Cost Result: {cost_success_2} - {cost_msg_2}")

    # 2. Get Task Statuses
    print("\n2. Fetching Task Statuses...")
    statuses = exec_mgmt.get_all_task_statuses()
    if statuses:
        print(f"Found {len(statuses)} task statuses. First few: {statuses[:3]}")
        # Find 'In Progress' status ID for next step
        in_progress_status_id = next((s['TaskStatusID'] for s in statuses if s['StatusName'] == 'In Progress'), None)
        completed_status_id = next((s['TaskStatusID'] for s in statuses if s['StatusName'] == 'Completed'), None)
    else:
        print("No task statuses found or error.")
        in_progress_status_id = None # Fallback
        completed_status_id = None

    # 3. Update Task Progress (Assuming Task ID 1 exists for Project ID 1)
    # First, ensure Task 1 exists or create it for testability
    # For this test, we'll assume it exists from WBS creation or prior step.
    # A robust test would create it.
    # Let's try to create a task if it doesn't exist for test_task_id within test_project_id
    task_check = db_manager.execute_query("SELECT TaskID FROM Tasks WHERE TaskID = ? AND ProjectID = ?", (test_task_id, test_project_id), fetch_one=True)
    if not task_check:
        # Create a dummy task for testing progress update
        # TaskType, Description, Phase, ScheduledStartDate, ScheduledEndDate, EstimatedHours, TaskStatusID, LeadEmployeeID, CreatedByEmployeeID
        # Using 'Pending' status ID (assuming it's 1 from schema default inserts)
        pending_status_id_for_task = next((s['TaskStatusID'] for s in statuses if s['StatusName'] == 'Pending'), 1)

        db_manager.execute_query(
            """INSERT INTO Tasks (TaskID, ProjectID, TaskType, Description, TaskStatusID, ScheduledStartDate, ScheduledEndDate)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (test_task_id, test_project_id, 'General', 'Initial Setup Task', pending_status_id_for_task, '2024-07-01', '2024-07-05'),
            commit=True
        )
        print(f"Created dummy Task ID {test_task_id} for Project {test_project_id} for testing.")


    print("\n3. Updating Task Progress...")
    if in_progress_status_id:
        progress_success, progress_msg = exec_mgmt.update_task_details(
            task_id=test_task_id, # Assume task 1 exists for project 1
            actual_start_date="2024-07-21",
            percent_complete=25.5,
            task_status_id=in_progress_status_id,
            notes="Started mobilization tasks.",
            actual_hours=16
        )
        print(f"Update Task Progress (to In Progress): {progress_success} - {progress_msg}")
    else:
        print("Skipping progress update to 'In Progress' as status ID not found.")

    # 4. Log Material Usage
    print("\n4. Logging Material Usage...")
    # Assume 'CM-001' is a valid StockNumber in Materials table
    # For test, check if CM-001 exists, if not, add it.
    mat_check = db_manager.execute_query("SELECT MaterialSystemID FROM Materials WHERE StockNumber = ?", ('CM-001',), fetch_one=True)
    if not mat_check:
        db_manager.execute_query(
            "INSERT INTO Materials (StockNumber, MaterialName, UnitOfMeasure, DefaultCost) VALUES (?, ?, ?, ?)",
            ('CM-001', 'Concrete Mix Bag', 'BAG', 5.50), commit=True
        )
        print("Added dummy material CM-001 for testing.")

    material_success, material_msg = exec_mgmt.log_material_to_db(
        project_id=test_project_id,
        material_stock_number="CM-001", # Use stock number
        quantity=10,
        unit="BAG",
        wbs_element_id=test_wbs_element_id, # Optional: link to WBS
        task_id=test_task_id, # Optional: link to Task
        notes="Used for foundation prep"
    )
    print(f"Log Material Usage Result: {material_success} - {material_msg}")

    # 5. Simulate completing the task
    print("\n5. Completing the Task...")
    if completed_status_id:
        complete_success, complete_msg = exec_mgmt.update_task_details(
            task_id=test_task_id,
            actual_end_date="2024-07-25",
            percent_complete=100.0,
            task_status_id=completed_status_id,
            notes="Mobilization fully completed.",
            actual_hours=40 # Total actual hours
        )
        print(f"Update Task Progress (to Completed): {complete_success} - {complete_msg}")
    else:
        print("Skipping progress update to 'Completed' as status ID not found.")

    logger.info("--- Execution Management Module Test Complete ---")
