import os
import sys
import logging
from datetime import datetime

# Add the project root to sys.path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules from the project
from database_manager import DatabaseManager
from data_processing import DataProcessing
from configuration import Config

def run_daily_log_test():
    logger.info("--- Starting Daily Log Processing Test ---")

    # 1. Ensure a clean database for testing
    db_file_path = Config.get_database_path()
    if os.path.exists(db_file_path):
        try:
            # Ensure any existing connection is closed before deleting
            if DatabaseManager._instance and DatabaseManager._instance.conn:
                DatabaseManager._instance.close_connection()
            os.remove(db_file_path)
            logger.info(f"Removed existing database file: {db_file_path}")
        except Exception as e:
            logger.error(f"Could not remove database file {db_file_path}: {e}")
            logger.error("Please ensure the database file is not in use and try again.")
            return

    # 2. Force re-initialization of DatabaseManager singleton
    DatabaseManager._instance = None
    db_manager_instance = DatabaseManager() # This will create the DB and apply schema

    # 3. Instantiate DataProcessing module
    data_processor = DataProcessing(db_manager_instance)

    # 4. Define a sample daily log entry
    sample_log_entry = f"""
Template Date: {datetime.now().strftime("%Y-%m-%d")}

### Daily Log - {datetime.now().strftime("%Y-%m-%d")}

Job Site / Location:
* Springfield Mall - Unit 10B

Today's Tasks:
* `[x]` Roughed-in circuits for breakroom
* `[ ]` Pulled wire run A-3
* `[ ]` Troubleshoot panel P2

Materials Used / Needed:
* Used: 500ft 12/2 MC, 10 boxes, 4 breakers. Need: More 1" EMT, 10A fuses

Hours Worked:
* 8 hours

Safety Checks / Observations:
* Performed pre-task safety check. Area clear. Noticed frayed cord on site generator - reported.

Issues / Questions / Blockers:
* Waiting on client decision for light fixture placement. Need clarification on drawing E-102.

Tool Notes:
* Site drill battery needs replacing. Van needs stocking with wire nuts.

---

--- End of Daily Log Template ---
"""

    dummy_employee_id = 1 # Assuming employee with ID 1 exists or will be created
    dummy_project_id = 1  # Assuming project with ID 1 exists or will be created

    # For a proper test, ensure employee and project exist in DB
    # Insert a dummy employee and project if they don't exist
    db_manager_instance.execute_query("INSERT OR IGNORE INTO Employees (EmployeeID, FirstName, LastName, WorkEmail) VALUES (?, ?, ?, ?)", (dummy_employee_id, "Test", "Employee", "test@example.com"), commit=True)
    db_manager_instance.execute_query("INSERT OR IGNORE INTO Projects (ProjectID, ProjectName, CustomerID, StartDate) VALUES (?, ?, ?, ?)", (dummy_project_id, "Test Project", 1, "2023-01-01"), commit=True)

    # 5. Call the processing method
    success, message = data_processor.process_daily_log_entry(sample_log_entry, dummy_employee_id, dummy_project_id)
    logger.info(f"Processing result: {message} (Success: {success})")

    if success:
        # 6. Verify data in the new tables
        logger.info("--- Verifying Data in DailyLogs Table ---")
        daily_logs = db_manager_instance.execute_query("SELECT * FROM DailyLogs", fetch_all=True)
        if daily_logs:
            for log in daily_logs:
                logger.info(f"DailyLog: {dict(log)}")
        else:
            logger.warning("No data found in DailyLogs table.")

        logger.info("--- Verifying Data in DailyLogTasks Table ---")
        daily_log_tasks = db_manager_instance.execute_query("SELECT * FROM DailyLogTasks", fetch_all=True)
        if daily_log_tasks:
            for task in daily_log_tasks:
                logger.info(f"DailyLogTask: {dict(task)}")
        else:
            logger.warning("No data found in DailyLogTasks table.")

        logger.info("--- Verifying Data in DailyLogMaterials Table ---")
        daily_log_materials = db_manager_instance.execute_query("SELECT * FROM DailyLogMaterials", fetch_all=True)
        if daily_log_materials:
            for material in daily_log_materials:
                logger.info(f"DailyLogMaterial: {dict(material)}")
        else:
            logger.warning("No data found in DailyLogMaterials table.")

        logger.info("--- Verifying Data in DailyLogObservations Table ---")
        daily_log_observations = db_manager_instance.execute_query("SELECT * FROM DailyLogObservations", fetch_all=True)
        if daily_log_observations:
            for obs in daily_log_observations:
                logger.info(f"DailyLogObservation: {dict(obs)}")
        else:
            logger.warning("No data found in DailyLogObservations table.")

    # 7. Clean up the created database file
    if os.path.exists(db_file_path):
        try:
            db_manager_instance.close_connection()
            os.remove(db_file_path)
            logger.info(f"Cleaned up test database file: {db_file_path}")
        except Exception as e:
            logger.error(f"Could not clean up database file {db_file_path}: {e}")

    logger.info("--- Daily Log Processing Test Finished ---")

if __name__ == "__main__":
    run_daily_log_test()
