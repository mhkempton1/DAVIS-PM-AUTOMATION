import sys
import os
import logging

# Add project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'project-management_system'))

# Import and run setup script first
import setup_test_environment
setup_test_environment.setup_test_environment()

from database_manager import db_manager, DatabaseManager

# Re-initialize the database manager to get a fresh connection
DatabaseManager._instance = None
db_manager = DatabaseManager()
from data_processing import DataProcessing
from project_startup import ProjectStartup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simulate_llm_and_purchasing():
    """
    Simulates processing a daily log with LLM parsing and creating a material request.
    """
    logging.info("--- Starting LLM Parsing and Purchasing Simulation ---")

    # Instantiate modules
    data_processor = DataProcessing(db_manager)
    project_startup_module = ProjectStartup(db_manager)

    # --- Step 1: Simulate Daily Log with LLM Parsing ---
    logging.info("Step 1: Processing a daily log entry with free-form text...")
    daily_log_text = """
    Daily Log for Project 1
    Template Date: 2025-07-16
    Foreman: John Doe (Employee ID 2)
    ---
    Work Completed:
    - Pulled wire for circuits A1-A5 on the first floor.
    - Installed 15 new outlets in the west wing.
    ---
    Issues / Questions / Blockers:
    We are running critically low on 2x4 conduit. The crew estimates we will be completely out by tomorrow afternoon. This will halt all rough-in work for the north wing. Please order more immediately.
    ---
    Materials Used:
    - 500ft 12/2 MC Cable
    - 15 outlet boxes
    """
    try:
        success, message, log_id = data_processor.process_daily_log_entry(
            employee_id=2,
            project_id=1,
            log_entry=daily_log_text
        )
        if success:
            logging.info(f"Successfully processed daily log. DailyLogID: {log_id}. Message: {message}")
        else:
            logging.error(f"Failed to process daily log. Message: {message}")
            return # Stop simulation if this fails

    except Exception as e:
        logging.error(f"An exception occurred during daily log processing: {e}", exc_info=True)
        return

    # --- Step 2: Verify LLM Parsed Data Log ---
    logging.info("\nStep 2: Verifying entry in LLM_Parsed_Data_Log...")
    try:
        parsed_log = db_manager.execute_query(
            "SELECT * FROM LLM_Parsed_Data_Log WHERE SourceRecordID = ? AND SourceModule = 'DailyLog'",
            (log_id,),
            fetch_one=True
        )
        if parsed_log:
            logging.info("Found LLM parsed log entry:")
            for key, value in dict(parsed_log).items():
                logging.info(f"  {key}: {value}")
        else:
            logging.warning("Could not find a corresponding entry in LLM_Parsed_Data_Log.")
    except Exception as e:
        logging.error(f"An exception occurred while querying LLM_Parsed_Data_Log: {e}", exc_info=True)


    # --- Step 3: Simulate Material Request ---
    logging.info("\nStep 3: Creating a new material request...")
    try:
        success, message, request_id = project_startup_module.add_material_request(
            project_id=1,
            requested_by_employee_id=2,
            material_description="2x4 conduit",
            quantity_requested=500,
            unit_of_measure="ft",
            urgency_level="Urgent",
            required_by_date="2025-07-30",
            notes="Based on daily log from 2025-07-15, this is a critical need."
        )
        if success:
            logging.info(f"Successfully created material request. InternalLogID: {request_id}. Message: {message}")
        else:
            logging.error(f"Failed to create material request. Message: {message}")
            return
    except Exception as e:
        logging.error(f"An exception occurred during material request creation: {e}", exc_info=True)
        return

    # --- Step 4: Verify Purchasing Log ---
    logging.info("\nStep 4: Verifying entry in Purchasing_Log...")
    try:
        purchase_request = db_manager.execute_query(
            "SELECT * FROM Purchasing_Log WHERE InternalLogID = ?",
            (request_id,),
            fetch_one=True
        )
        if purchase_request:
            logging.info("Found new material request entry:")
            for key, value in dict(purchase_request).items():
                logging.info(f"  {key}: {value}")
        else:
            logging.error("Verification failed: Could not find the new entry in Purchasing_Log.")
    except Exception as e:
        logging.error(f"An exception occurred while querying Purchasing_Log: {e}", exc_info=True)

    logging.info("\n--- Simulation Finished ---")

if __name__ == "__main__":
    simulate_llm_and_purchasing()