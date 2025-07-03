import os
import sys
import logging

# Add the project root to sys.path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging for the setup script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules from the project
from database_manager import DatabaseManager
from configuration import Config

def setup_test_environment():
    logger.info("--- Setting Up Test Environment ---")

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
            return False

    # 2. Force re-initialization of DatabaseManager singleton (creates DB and applies schema)
    DatabaseManager._instance = None
    db_manager_instance = DatabaseManager() 

    # 3. Read and execute populate_test_data.sql
    populate_script_path = os.path.join(Config.BASE_DIR, 'database', 'populate_test_data.sql')
    if not os.path.exists(populate_script_path):
        logger.error(f"Populate script not found: {populate_script_path}")
        return False

    try:
        with open(populate_script_path, 'r') as f:
            sql_script = f.read()
        
        # Split the script into individual statements
        sql_script_no_comments = "\n".join(line for line in sql_script.splitlines() if not line.strip().startswith('--'))
        statements = [stmt.strip() for stmt in sql_script_no_comments.split(';') if stmt.strip()]

        if not statements:
            logger.warning(f"No SQL statements found in populate script: {populate_script_path}")
            return False

        logger.info(f"Executing {len(statements)} statements from {populate_script_path}...")
        for i, statement in enumerate(statements):
            if not db_manager_instance.execute_query(statement, commit=True):
                logger.error(f"Error executing statement {i+1}: {statement[:100]}...")
                return False
        logger.info("Test data populated successfully.")
        return True

    except Exception as e:
        logger.exception(f"An error occurred during test environment setup: {e}")
        return False

if __name__ == "__main__":
    if setup_test_environment():
        logger.info("Test environment setup completed successfully.")
    else:
        logger.error("Test environment setup failed.")