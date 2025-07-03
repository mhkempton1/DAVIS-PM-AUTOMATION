import sys
import os

# Ensure the project_management_system directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_system_dir = os.path.join(current_dir, "pm_system-main", "project-management_system")
if project_system_dir not in sys.path:
    sys.path.insert(0, project_system_dir)

from database_manager import db_manager # Initializes db_manager
from integration import Integration
from configuration import Config
import pandas as pd

def ensure_sample_csv_exists():
    sample_csv_path = os.path.join(Config.get_data_dir(), 'sample_estimate.csv')
    # Always create/overwrite to ensure the 7-row version is used for simulation
    print(f"Ensuring 7-row sample_estimate.csv at {sample_csv_path} for simulation...")
    os.makedirs(Config.get_data_dir(), exist_ok=True)
    sample_data = {
        'Cost Code': ['01-010', '01-020', '02-100', '03-200', '03-210', '04-300', '05-400'],
        'Description': ['Mobilization', 'Project Supervision', 'Site Prep', 'Concrete Footings', 'Concrete Slab', 'Framing', 'Roofing'],
        'Quantity': [1.0, 40.0, 500.0, 15.0, 200.0, 5000.0, 20.0],
        'Unit': ['LS', 'HR', 'SY', 'CY', 'SF', 'BF', 'SQ'],
        'Unit Cost': [5000.00, 75.00, 15.00, 300.00, 5.00, 0.75, 150.00],
        'Total Cost': [5000.00, 3000.00, 7500.00, 4500.00, 1000.00, 3750.00, 3000.00],
        'Phase': ['Pre-Construction', 'Pre-Construction', 'Foundation', 'Foundation', 'Foundation', 'Structure', 'Exterior']
    }
    sample_df = pd.DataFrame(sample_data)
    sample_df.to_csv(sample_csv_path, index=False)
    print(f"Created/Overwritten sample_estimate.csv at: {sample_csv_path} with 7 data rows.")
    return sample_csv_path

def simulate_ingest_data(project_id_to_link=None):
    print(f"\n--- Simulating Data Ingestion (Linking to Project ID: {project_id_to_link}) ---")

    # Initialize Integration module
    # db_manager is already initialized as it's a singleton imported above
    integration_module = Integration(db_manager) # Pass db_manager instance

    # Ensure sample_estimate.csv exists (as per README instructions)
    csv_file_path = ensure_sample_csv_exists()

    print(f"Attempting to import data from: {csv_file_path}")

    # Call the import_estimate_from_csv method
    # The method signature is: import_estimate_from_csv(self, file_path, project_id=None)
    success, message = integration_module.import_estimate_from_csv(csv_file_path, project_id=project_id_to_link)

    if success:
        print(f"Data Ingestion Successful: {message}")
    else:
        print(f"Data Ingestion Failed: {message}")

    return success

if __name__ == "__main__":
    # This script can be run standalone or called after project creation.
    # For standalone, project_id_to_link can be None (data ingested without project link initially)
    # or a known existing project_id.

    # Example: Ingest data and link it to project ID 1 (created after DB reset)
    # In a real testing sequence, this ID would be passed from the project creation step.
    test_project_id = 1

    # First, make sure the project exists, or the FK constraint on raw_estimates might fail if project_id is not None
    # For this simulation, we assume project_id 2 exists from the previous step.
    # A more robust test would query the DB for the project_id first.

    print(f"Starting data ingestion simulation for project ID: {test_project_id}")
    ingestion_successful = simulate_ingest_data(project_id_to_link=test_project_id)

    if ingestion_successful:
        print(f"Script finished. Data from '{Config.get_data_dir()}/sample_estimate.csv' should be in 'raw_estimates' table, linked to project ID {test_project_id}.")
    else:
        print("Script finished. Data ingestion was not successful.")

    # Example: Ingest data without linking to a project
    # print("\nStarting data ingestion simulation (unlinked)")
    # ingestion_successful_unlinked = simulate_ingest_data(project_id_to_link=None)
    # if ingestion_successful_unlinked:
    #     print(f"Script finished. Data from '{Config.get_data_dir()}/sample_estimate.csv' should be in 'raw_estimates' table, unlinked.")
    # else:
    #     print("Script finished. Unlinked data ingestion was not successful.")
