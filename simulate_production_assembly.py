import sys
import os
import logging

# Add project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'project-management_system'))

from database_manager import db_manager
from project_startup import ProjectStartup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_dummy_assembly():
    """Ensures a dummy assembly exists for the simulation."""
    logging.info("Checking for dummy assembly...")
    try:
        assembly = db_manager.execute_query(
            "SELECT AssemblyID FROM Assemblies WHERE AssemblyItemNumber = ?",
            ('ASM-001',), fetch_one=True
        )
        if assembly:
            assembly_id = assembly['AssemblyID']
            logging.info(f"Dummy assembly 'ASM-001' already exists with ID: {assembly_id}.")
            return assembly_id
        else:
            logging.info("Dummy assembly not found. Creating one...")
            # Note: The schema for Assemblies might have NOT NULL constraints.
            # This is a minimal insertion.
            cursor = db_manager.execute_query(
                "INSERT INTO Assemblies (AssemblyItemNumber, AssemblyName, Description, Phase) VALUES (?, ?, ?, ?)",
                ('ASM-001', 'Basic Panel Assembly', 'A standard electrical panel assembly.', 'Prefab'),
                commit=True
            )
            new_id = cursor.lastrowid
            logging.info(f"Created new dummy assembly with ID: {new_id}.")
            return new_id
    except Exception as e:
        logging.error(f"Error ensuring dummy assembly exists: {e}", exc_info=True)
        return None

def simulate_production():
    """
    Simulates creating a production order for a prefabricated assembly.
    """
    logging.info("--- Starting Production Assembly Simulation ---")

    # --- Step 1: Ensure a dummy assembly exists ---
    assembly_id = ensure_dummy_assembly()
    if not assembly_id:
        logging.error("Could not create or find a dummy assembly. Aborting simulation.")
        return

    # Instantiate the module
    project_startup_module = ProjectStartup(db_manager)

    # --- Step 2: Create a Production Order ---
    logging.info("\nStep 2: Creating a new production assembly order...")
    try:
        success, message, prod_id = project_startup_module.create_production_assembly_order(
            assembly_id=assembly_id,
            project_id=1,
            quantity_to_produce=5,
            assigned_to_employee_id=3, # Assigning to a different employee for variety
            notes="Priority order for the Wicklow project."
        )
        if success:
            logging.info(f"Successfully created production order. ProductionID: {prod_id}. Message: {message}")
        else:
            logging.error(f"Failed to create production order. Message: {message}")
            return

    except Exception as e:
        logging.error(f"An exception occurred during production order creation: {e}", exc_info=True)
        return

    # --- Step 3: Verify Production Assembly Tracking ---
    logging.info("\nStep 3: Verifying entry in Production_Assembly_Tracking...")
    try:
        production_order = db_manager.execute_query(
            "SELECT * FROM Production_Assembly_Tracking WHERE ProductionID = ?",
            (prod_id,),
            fetch_one=True
        )
        if production_order:
            logging.info("Found new production order entry:")
            for key, value in dict(production_order).items():
                logging.info(f"  {key}: {value}")
        else:
            logging.error("Verification failed: Could not find the new entry in Production_Assembly_Tracking.")
    except Exception as e:
        logging.error(f"An exception occurred while querying Production_Assembly_Tracking: {e}", exc_info=True)

    logging.info("\n--- Simulation Finished ---")

if __name__ == "__main__":
    simulate_production()
