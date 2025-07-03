import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_system_dir = os.path.join(current_dir, "pm_system-main", "project-management_system")
if project_system_dir not in sys.path:
    sys.path.insert(0, project_system_dir)

from database_manager import db_manager

def reset_status(project_id, new_status_name='Active'):
    status_id_row = db_manager.execute_query(
        "SELECT ProjectStatusID FROM ProjectStatuses WHERE StatusName = ?",
        (new_status_name,),
        fetch_one=True
    )
    if not status_id_row:
        print(f"Status '{new_status_name}' not found in ProjectStatuses.")
        return False

    new_status_id = status_id_row['ProjectStatusID']

    success = db_manager.execute_query(
        "UPDATE Projects SET ProjectStatusID = ? WHERE ProjectID = ?",
        (new_status_id, project_id),
        commit=True
    )
    if success:
        print(f"Project {project_id} status reset to '{new_status_name}' (ID: {new_status_id}).")
        return True
    else:
        print(f"Failed to reset project {project_id} status.")
        return False

if __name__ == "__main__":
    project_to_reset = 1 # Assuming this is the project ID
    reset_status(project_to_reset)
