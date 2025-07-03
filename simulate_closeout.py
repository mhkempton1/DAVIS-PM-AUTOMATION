import sys
import os

# Ensure the project_management_system directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_system_dir = os.path.join(current_dir, "pm_system-main", "project-management_system")
if project_system_dir not in sys.path:
    sys.path.insert(0, project_system_dir)

from database_manager import db_manager # Initializes db_manager
from closeout import Closeout
from configuration import Config # For directory setup
import shutil # For checking archive directory

def simulate_closeout_phase(project_id):
    print(f"\n--- Simulating Closeout Phase for Project ID: {project_id} ---")

    # Initialize Closeout module
    # Closeout.__init__ accepts optional instances, defaulting to global db_manager
    # and creating its own Reporting & MonitoringControl instances.
    closeout_module = Closeout()

    # Ensure archive directory exists, as per closeout.py logic
    archive_base_dir = os.path.join(Config.get_reports_dir(), "archive") # From closeout.py
    os.makedirs(archive_base_dir, exist_ok=True)

    print(f"\nAttempting to closeout project {project_id}...")
    # Method signature: closeout_project(self, project_id)
    success, message = closeout_module.closeout_project(project_id)

    print(f"Project Closeout: {message} (Success: {success})")

    if success:
        # Verify project status changed to 'Closed' or similar
        # (Depends on exact status name used by closeout_project)
        # Query schema.sql ProjectStatuses for 'Closed' status ID
        closed_status_id_row = db_manager.execute_query("SELECT ProjectStatusID FROM ProjectStatuses WHERE StatusName = 'Completed'", fetch_one=True) # 'Completed' is in schema.sql
        if not closed_status_id_row:
             closed_status_id_row = db_manager.execute_query("SELECT ProjectStatusID FROM ProjectStatuses WHERE StatusName = 'Closed'", fetch_one=True) # Fallback if 'Closed' exists

        if closed_status_id_row:
            closed_status_id = closed_status_id_row['ProjectStatusID']
            project_status_row = db_manager.execute_query("SELECT StatusName FROM Projects p JOIN ProjectStatuses ps ON p.ProjectStatusID = ps.ProjectStatusID WHERE p.ProjectID = ?", (project_id,), fetch_one=True)
            if project_status_row:
                print(f"Project {project_id} status after closeout: {project_status_row['StatusName']}")
                if project_status_row['StatusName'] == 'Completed' or project_status_row['StatusName'] == 'Closed':
                    print(f"Project status correctly updated to '{project_status_row['StatusName']}'.")
                else:
                    print(f"WARNING: Project status is '{project_status_row['StatusName']}', expected 'Completed' or 'Closed'.")
            else:
                print(f"Could not verify project status for project {project_id} after closeout.")
        else:
            print("Could not find 'Completed' or 'Closed' status ID in ProjectStatuses table to verify.")

        # Verify archive location (basic check if directory exists)
        project_archive_dir = os.path.join(archive_base_dir, f"project_{project_id}_archive")
        if os.path.exists(project_archive_dir) and os.path.isdir(project_archive_dir):
            print(f"Archive directory created at: {project_archive_dir}")
            # Further checks could list files if specific files are expected
        else:
            print(f"WARNING: Archive directory NOT found at: {project_archive_dir}")

    print(f"\nCloseout phase simulation completed for project ID: {project_id}.")
    return success


if __name__ == "__main__":
    test_project_id = 1 # Corrected for DB reset

    print(f"Starting Closeout Phase simulation for project ID: {test_project_id}")
    closeout_successful = simulate_closeout_phase(test_project_id)

    if closeout_successful:
        print(f"Script finished. Closeout actions simulated for project ID {test_project_id}.")
    else:
        print(f"Script finished. Closeout phase simulation was not fully successful.")
