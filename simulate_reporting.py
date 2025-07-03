import sys
import os

# Ensure the project_management_system directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_system_dir = os.path.join(current_dir, "pm_system-main", "project-management_system")
if project_system_dir not in sys.path:
    sys.path.insert(0, project_system_dir)

from database_manager import db_manager # Initializes db_manager
from reporting import Reporting
from configuration import Config # For directory setup
import pandas as pd

def simulate_reporting_phase(project_id):
    print(f"\n--- Simulating Reporting Phase for Project ID: {project_id} ---")

    # Initialize Reporting module
    # Reporting.__init__ accepts optional instances, defaulting to global db_manager
    # and creating its own MonitoringControl instance.
    reporting_module = Reporting()

    # Ensure reports directory exists
    os.makedirs(Config.get_reports_dir(), exist_ok=True)

    # 1. Generate Estimate vs. Actual Report
    # Method signature: generate_estimate_vs_actual_report(self, project_id)
    # Returns: (DataFrame, bool success, str message)
    print(f"\nAttempting to generate Estimate vs. Actual report for project {project_id}...")
    eva_df, eva_success, eva_msg = reporting_module.generate_estimate_vs_actual_report(project_id)
    print(f"Estimate vs. Actual Report Generation: {eva_msg} (Success: {eva_success})")
    if eva_success and not eva_df.empty:
        print("Estimate vs. Actual Data (first 5 rows):")
        print(eva_df.head().to_string())
        # Attempt to export (optional, can be verbose)
        export_success, export_msg = reporting_module.export_report(eva_df, f"project_{project_id}_eva_report", project_id, "excel")
        print(f"Export of EVA report: {export_msg} (Success: {export_success})")
    elif eva_success and eva_df.empty:
        print("Estimate vs. Actual Report generated, but it's empty.")


    # 2. Generate Performance Summary Report
    # Method signature: generate_performance_report(self, project_id)
    # Returns: (str report_text, bool success, str message)
    print(f"\nAttempting to generate Performance Summary report for project {project_id}...")
    perf_text, perf_success, perf_msg = reporting_module.generate_performance_report(project_id)
    print(f"Performance Summary Report Generation: {perf_msg} (Success: {perf_success})")
    if perf_success and perf_text:
        print("Performance Summary Data (first 500 chars):")
        print(perf_text[:500] + "..." if len(perf_text) > 500 else perf_text)
        export_success, export_msg = reporting_module.export_report(perf_text, f"project_{project_id}_perf_summary", project_id, "text")
        print(f"Export of Performance Summary: {export_msg} (Success: {export_success})")
    elif perf_success and not perf_text:
         print("Performance Summary Report generated, but it's empty.")

    print(f"\nReporting phase simulation completed for project ID: {project_id}.")
    return True


if __name__ == "__main__":
    test_project_id = 1 # Corrected for DB reset

    print(f"Starting Reporting Phase simulation for project ID: {test_project_id}")
    reporting_successful = simulate_reporting_phase(test_project_id)

    if reporting_successful:
        print(f"Script finished. Reporting actions simulated for project ID {test_project_id}.")
    else:
        print(f"Script finished. Reporting phase simulation was not fully successful.")
