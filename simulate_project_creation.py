import sys
import os
from datetime import datetime, timedelta

# Ensure the project_management_system directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
# Adjust the path to go up one level from where the script is (e.g. repo root)
# to pm_system-main/project-management_system/
# This assumes simulate_project_creation.py is in the root of the repo.
project_system_dir = os.path.join(current_dir, "pm_system-main", "project-management_system")
if project_system_dir not in sys.path:
    sys.path.insert(0, project_system_dir)

from database_manager import db_manager
from project_startup import ProjectStartup
from configuration import Config # For default paths if needed
from utils import calculate_end_date # for end_date calculation

def simulate_create_project():
    print("--- Simulating Project Creation ---")

    # Initialize necessary components
    # db_manager is a singleton, will be initialized on first import if not already.
    # Ensure Config directories exist, similar to main.py
    os.makedirs(Config.DATABASE_DIR, exist_ok=True)
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.REPORTS_DIR, exist_ok=True)
    os.makedirs(Config.ARCHIVE_DIR, exist_ok=True)
    os.makedirs(Config.LOGS_DIR, exist_ok=True)

    # Instantiate ProjectStartup module, passing the db_manager instance
    project_startup_module = ProjectStartup(db_manager)

    project_name_val = "Test Project Alpha" # Renamed to avoid conflict with parameter name
    start_date_str_val = datetime.now().strftime("%Y-%m-%d") # Renamed
    duration_days_val = 30 # Renamed

    # Use the utility function to calculate end_date
    end_date_str_val = calculate_end_date(start_date_str_val, duration_days_val) # Renamed
    if "Error:" in end_date_str_val:
        print(f"Error calculating end date: {end_date_str_val}")
        return None

    print(f"Attempting to create project: '{project_name_val}' starting {start_date_str_val} for {duration_days_val} days (ends {end_date_str_val}).")

    # Call the create_project method
    # create_project(self, project_name, start_date=None, end_date=None, duration_days=None)
    # For simplicity, let's use default customer_id=1 (assuming it exists or schema handles it)
    # and let project_number be auto-generated if the method supports it, or pass a simple one.
    # The method in project_startup.py uses a default customer_id if not provided.
    # It also auto-generates a project_number if not provided.

    project_id, message = project_startup_module.create_project(
        project_name_val,  # Pass project_name positionally
        start_date=start_date_str_val, # Use keyword arg for clarity, matching definition
        end_date=end_date_str_val,     # Use keyword arg, matching definition
        duration_days=duration_days_val # Use keyword arg, matching definition
        # Assuming CustomerID 1 exists or is not strictly required for basic creation
        # The schema has Customers table, but create_project might not enforce it or use a default.
        # Let's check schema.sql: Projects table has CustomerID NOT NULL.
        # Default data for Customers might be needed or the method should handle it.
        # For now, let's try with a placeholder customer_id.
        # The `project_startup.create_project` uses `customer_id=customer_id or 1` (placeholder)
        # It also needs a ProjectManagerEmployeeID and ForemanEmployeeID.
        # The method uses defaults: project_manager_id=1, foreman_id=1
        # Let's assume EmployeeID 1 exists (default admin user might be used as a proxy if Employees table is linked).
        # The `users` table `id` for admin is 1. The `Employees` table also has `EmployeeID` starting at 1.
        # The `schema.sql` for `Employees` does not auto-create an admin employee.
        # This could be an issue. Let's add a default employee for testing if project creation fails.
    )

    if project_id:
        print(f"Project Creation Successful: {message} (Project ID: {project_id})")
        return project_id
    else:
        print(f"Project Creation Failed: {message}")
        # Check if failure is due to missing Customer or Employee
        # Adjusted the retry call to also use correct parameter names
        if "customer" in message.lower() or "employee" in message.lower() or "constraint" in message.lower(): # Added constraint check
            print("Attempting to add default customer and employee for testing...")
            try:
                # Add default customer type if not exists
                db_manager.execute_query("INSERT OR IGNORE INTO CustomerTypes (CustomerTypeID, TypeName) VALUES (1, 'Default Type');", commit=True)
                # Add default project status if not exists (though create_project tries to fetch 'Pending')
                db_manager.execute_query("INSERT OR IGNORE INTO ProjectStatuses (ProjectStatusID, StatusName) VALUES ((SELECT COALESCE(MAX(ProjectStatusID), 0) + 1 FROM ProjectStatuses), 'Pending');", commit=True)
                # Add default customer
                db_manager.execute_query("INSERT OR IGNORE INTO Customers (CustomerID, CustomerName, CustomerTypeID, IsActive) VALUES (1, 'Default Test Customer', 1, 1);", commit=True)
                # Add default employee (assuming AccessRoleID 1 exists for 'Administrator')
                db_manager.execute_query("INSERT OR IGNORE INTO AccessRoles (AccessRoleID, RoleName) VALUES (1, 'Administrator');", commit=True)
                db_manager.execute_query("INSERT OR IGNORE INTO Employees (EmployeeID, FirstName, LastName, AccessRoleID, IsActive, WorkEmail) VALUES (1, 'Admin', 'User', 1, 1, 'admin@example.com');", commit=True)
                print("Default customer and employee inserted (or ignored if existing). Retrying project creation...")

                project_id, message = project_startup_module.create_project(
                    project_name_val,
                    start_date=start_date_str_val,
                    end_date=end_date_str_val,
                    duration_days=duration_days_val
                )
                if project_id:
                    print(f"Project Creation Successful after adding defaults: {message} (Project ID: {project_id})")
                    return project_id
                else:
                    print(f"Project Creation Failed even after adding defaults: {message}")
                    return None
            except Exception as e:
                print(f"Error adding default customer/employee: {e}")
                return None
        return None

if __name__ == "__main__":
    created_project_id = simulate_create_project()
    if created_project_id:
        print(f"Script finished. Project ID {created_project_id} should exist in the database.")
    else:
        print("Script finished. Project creation was not successful.")
