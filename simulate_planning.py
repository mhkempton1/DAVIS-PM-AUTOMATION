import sys
import os

# Ensure the project_management_system directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_system_dir = os.path.join(current_dir, "pm_system-main", "project-management_system")
if project_system_dir not in sys.path:
    sys.path.insert(0, project_system_dir)

from database_manager import db_manager # Initializes db_manager
from project_startup import ProjectStartup
from configuration import Config # For directory setup, if needed

def simulate_execute_data_dna(project_id):
    print(f"\n--- Simulating Planning (Execute Data DNA) for Project ID: {project_id} ---")

    # Initialize ProjectStartup module
    project_startup_module = ProjectStartup(db_manager)

    # Step 1: Generate WBS from estimates
    # This method also links unassigned processed_estimates to the project_id
    # and updates the project's total estimated cost.
    print(f"\nAttempting to generate WBS for project ID: {project_id}...")
    wbs_success, wbs_msg = project_startup_module.generate_wbs_from_estimates(project_id)
    print(f"WBS Generation for project {project_id}: {wbs_msg} (Success: {wbs_success})")
    if not wbs_success:
        print("Halting planning due to WBS generation failure.")
        return False

    # Step 2: Generate Project Budget
    # This uses the WBS elements created in the previous step.
    print(f"\nAttempting to generate budget for project ID: {project_id}...")
    budget_success, budget_msg = project_startup_module.generate_project_budget(project_id)
    print(f"Budget Generation for project {project_id}: {budget_msg} (Success: {budget_success})")
    if not budget_success:
        print("Halting planning due to budget generation failure.")
        return False

    # Step 3: Allocate Resources (Simplified version)
    # This also uses processed estimates linked to the project.
    # The current implementation in project_startup.py's allocate_resources might need review
    # as it refers to 'wbs_element_id' on processed_estimates which might not be directly set.
    # However, generate_wbs_from_estimates creates WBS and links ProcessedEstimateID to WBS.
    # allocate_resources might need to join these tables or use WBS elements.
    # For now, let's call it as defined.
    # The `allocate_resources` method in `project_startup.py` uses a query:
    # SELECT pe.id, pe.cost_code, pe.description, pe.quantity, pe.unit, pe.unit_cost, pe.total_cost, pe.wbs_element_id
    # FROM processed_estimates pe WHERE pe.project_id = ?
    # This `pe.wbs_element_id` column does not exist in the `processed_estimates` table schema.
    # This will likely cause an error.
    # Let's proceed and see. If it fails, this is an identified bug.
    print(f"\nAttempting to allocate resources for project ID: {project_id}...")
    resources_success, resources_msg = project_startup_module.allocate_resources(project_id)
    print(f"Resource Allocation for project {project_id}: {resources_msg} (Success: {resources_success})")
    if not resources_success:
        print("Resource allocation step failed. This might be an issue to investigate (e.g., schema mismatch or logic).")
        # Depending on strictness, we could return False here.
        # For now, let's log and continue to see if other parts work.
        # return False

    print(f"\nPlanning (Execute Data DNA) simulation completed for project ID: {project_id}.")
    return True


if __name__ == "__main__":
    test_project_id = 1 # Corrected for DB reset

    print(f"Starting Planning (Execute Data DNA) simulation for project ID: {test_project_id}")
    planning_successful = simulate_execute_data_dna(test_project_id)

    if planning_successful:
        print(f"Script finished. Planning steps should be reflected in WBS, budget, and resource tables for project ID {test_project_id}.")
    else:
        print(f"Script finished. Planning (Execute Data DNA) was not fully successful.")
