import sys
import os

# Ensure the project_management_system directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_system_dir = os.path.join(current_dir, "pm_system-main", "project-management_system")
if project_system_dir not in sys.path:
    sys.path.insert(0, project_system_dir)

from database_manager import db_manager # Initializes db_manager
from data_processing import DataProcessing
from configuration import Config # For directory setup, if DataProcessing needs it

def simulate_process_data():
    print(f"\n--- Simulating Data Processing ---")

    # Initialize DataProcessing module
    # db_manager is already initialized
    data_processing_module = DataProcessing(db_manager) # Pass db_manager instance

    print(f"Attempting to process raw estimate data...")

    # Call the process_estimate_data method
    # Signature: process_estimate_data(self, project_id_to_filter=None)
    # If project_id_to_filter is None, it processes all raw_estimates not yet processed.
    # If a project_id is provided, it will only process raw_estimates linked to that project.
    # Since our raw data was linked to project_id 2 during ingestion, we can either pass 2
    # or None (if we assume no other raw data exists or we want to process all pending).
    # The method process_estimate_data() does not take project_id_to_filter.
    # It processes all raw estimates with 'Pending Processing' status.
    # However, the _get_raw_estimates_df filters by 'Pending Processing' OR 'Pending'
    # and carries over ProjectID if it was set during ingestion.

    success, message = data_processing_module.process_estimate_data() # Processes all pending

    if success:
        print(f"Data Processing Successful: {message}")
    else:
        print(f"Data Processing Failed: {message}")

    return success

if __name__ == "__main__":
    print(f"Starting data processing simulation...")
    processing_successful = simulate_process_data()

    if processing_successful:
        print(f"Script finished. Raw data should be processed into 'processed_estimates' table.")
    else:
        print("Script finished. Data processing was not successful.")
