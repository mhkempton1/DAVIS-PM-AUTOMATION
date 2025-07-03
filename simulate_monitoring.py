import sys
import os

# Ensure the project_management_system directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_system_dir = os.path.join(current_dir, "pm_system-main", "project-management_system")
if project_system_dir not in sys.path:
    sys.path.insert(0, project_system_dir)

from database_manager import db_manager # Initializes db_manager
from monitoring_control import MonitoringControl
from configuration import Config # For directory setup, if needed
import pandas as pd

def display_df_or_dict(data, title="Data"):
    """Helper to print DataFrames or dictionaries."""
    print(f"\n--- {title} ---")
    if isinstance(data, pd.DataFrame):
        if data.empty:
            print("No data to display.")
        else:
            print(data.to_string())
    elif isinstance(data, dict):
        if not data:
            print("No data to display.")
        else:
            for key, value in data.items():
                print(f"{key}: {value}")
    elif isinstance(data, str): # If the module returns a string message
        print(data)
    else:
        print("Data is not a DataFrame or Dictionary.")


def simulate_monitoring_phase(project_id):
    print(f"\n--- Simulating Monitoring & Control Phase for Project ID: {project_id} ---")

    # Initialize MonitoringControl module
    # MonitoringControl.__init__ accepts an optional db_m_instance, defaulting to global db_manager.
    monitoring_module = MonitoringControl()

    # 1. Analyze Cost Variance
    # Method signature: analyze_cost_variance(self, project_id)
    print(f"\nAttempting to analyze cost variance for project {project_id}...")
    cost_variance_data, cv_msg = monitoring_module.analyze_cost_variance(project_id)
    print(f"Cost Variance Analysis Message: {cv_msg}")
    display_df_or_dict(cost_variance_data, f"Cost Variance Data for Project {project_id}")

    # 2. Analyze Schedule Variance
    # Method signature: analyze_schedule_variance(self, project_id)
    # This might be problematic if it relies on detailed task schedule vs actuals,
    # and tasks were not fully fleshed out or updated.
    print(f"\nAttempting to analyze schedule variance for project {project_id}...")
    schedule_variance_data, sv_msg = monitoring_module.analyze_schedule_variance(project_id)
    print(f"Schedule Variance Analysis Message: {sv_msg}")
    display_df_or_dict(schedule_variance_data, f"Schedule Variance Data for Project {project_id}")

    # 3. Get Project Summary Performance
    # Method signature: get_project_summary_performance(self, project_id)
    print(f"\nAttempting to get project summary performance for project {project_id}...")
    summary_data, summary_msg = monitoring_module.get_project_summary_performance(project_id)
    print(f"Project Summary Performance Message: {summary_msg}")
    display_df_or_dict(summary_data, f"Project Summary Performance for Project {project_id}")

    print(f"\nMonitoring & Control phase simulation completed for project ID: {project_id}.")
    return True


if __name__ == "__main__":
    test_project_id = 1 # Corrected for DB reset

    print(f"Starting Monitoring & Control Phase simulation for project ID: {test_project_id}")
    monitoring_successful = simulate_monitoring_phase(test_project_id)

    if monitoring_successful:
        print(f"Script finished. Monitoring & Control actions simulated for project ID {test_project_id}.")
    else:
        print(f"Script finished. Monitoring & Control phase simulation was not fully successful.")
