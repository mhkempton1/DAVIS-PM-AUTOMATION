import pandas as pd # Added import
import logging
import os
import shutil # For zipping files for archiving
from datetime import datetime
from database_manager import db_manager
from configuration import Config
from reporting import Reporting # To generate final reports
from monitoring_control import MonitoringControl # Added import
import constants # Added

# Set up logging for the Closeout Module
# BasicConfig is now handled in main.py for the application.
logger = logging.getLogger(__name__)

class Closeout:
    """
    Manages project closeout, finalizes reports, updates project status,
    and archives project data for historical records.
    """
    def __init__(self, db_m_instance, reporting_instance=None, monitor_control_instance=None): # db_m_instance is now required
        """
        Initializes the Closeout module.
        """
        if db_m_instance is None:
            raise ValueError("DatabaseManager instance is required for Closeout.")
        self.db_manager = db_m_instance

        # Instantiate dependencies if not provided, ensuring they also get the db_manager
        used_monitor_control = monitor_control_instance if monitor_control_instance else MonitoringControl(db_m_instance=self.db_manager)
        self.reporting_module = reporting_instance if reporting_instance else Reporting(db_m_instance=self.db_manager, monitor_control_instance=used_monitor_control)

        self.archive_dir = os.path.join(Config.get_reports_dir(), 'archive')
        os.makedirs(self.archive_dir, exist_ok=True)
        logger.info("Closeout module initialized with provided db_manager.")

    def finalize_project_reports(self, project_id):
        """
        Generates and exports all final reports for a given project.
        """
        logger.info(f"Finalizing reports for Project ID: {project_id}")
        reports_generated = []

        # Generate Estimate vs. Actual Report (Excel)
        eva_df, success_eva, msg_eva = self.reporting_module.generate_estimate_vs_actual_report(project_id)
        if success_eva:
            export_success, export_msg = self.reporting_module.export_report(eva_df, 'Estimate vs. Actual', project_id, 'excel')
            reports_generated.append({'name': 'Estimate vs. Actual', 'path': os.path.join(Config.get_reports_dir(), f"project_{project_id}_estimate_vs._actual_report.xlsx") if export_success else None, 'status': export_msg})
        else:
            reports_generated.append({'name': 'Estimate vs. Actual', 'path': None, 'status': msg_eva})
            logger.error(f"Failed to generate Estimate vs. Actual Report for project {project_id}: {msg_eva}")

        # Generate Performance Summary Report (Text)
        perf_text, success_perf, msg_perf = self.reporting_module.generate_performance_report(project_id)
        if success_perf:
            export_success, export_msg = self.reporting_module.export_report(perf_text, 'Performance Summary', project_id, 'text')
            reports_generated.append({'name': 'Performance Summary', 'path': os.path.join(Config.get_reports_dir(), f"project_{project_id}_performance_summary_report.txt") if export_success else None, 'status': export_msg})
        else:
            reports_generated.append({'name': 'Performance Summary', 'path': None, 'status': msg_perf})
            logger.error(f"Failed to generate Performance Summary Report for project {project_id}: {msg_perf}")

        # Add other reports as needed (e.g., resource utilization, detailed cost breakdown)

        logger.info(f"Final report generation process completed for Project ID: {project_id}.")
        return reports_generated, True, "Final reports processed."

    def mark_project_closed(self, project_id):
        """
        Updates the status of a project to 'Closed' in the database.
        Uses 'Completed' status name as per schema.sql ProjectStatuses table.
        """
        # Get ProjectStatusID for 'Completed'
        status_query = "SELECT ProjectStatusID FROM ProjectStatuses WHERE StatusName = ?"
        status_row = self.db_manager.execute_query(status_query, (constants.PROJECT_STATUS_COMPLETED,), fetch_one=True)
        if not status_row:
            logger.error(f"Could not find '{constants.PROJECT_STATUS_COMPLETED}' status in ProjectStatuses. Closeout cannot update project status.")
            return False, f"Critical error: '{constants.PROJECT_STATUS_COMPLETED}' status definition not found."
        completed_status_id = status_row['ProjectStatusID']

        # Get current EndDate if exists, otherwise use today
        project_details = self.db_manager.execute_query(
            "SELECT EndDate FROM Projects WHERE ProjectID = ?", (project_id,), fetch_one=True
        )
        current_end_date = project_details['EndDate'] if project_details and project_details['EndDate'] else datetime.now().strftime('%Y-%m-%d')

        update_query = "UPDATE Projects SET ProjectStatusID = ?, EndDate = ?, LastModifiedDate = CURRENT_TIMESTAMP WHERE ProjectID = ?"
        params = (completed_status_id, current_end_date, project_id)

        success = self.db_manager.execute_query(update_query, params, commit=True)
        if success:
            logger.info(f"Project ID {project_id} status updated to 'Completed' (ID: {completed_status_id}) and EndDate to {current_end_date}.")
            return True, "Project status updated to 'Completed' successfully."
        else:
            logger.error(f"Failed to update status for Project ID {project_id} to 'Completed'.")
            return False, "Failed to update project status."

    def archive_project_data(self, project_id, report_paths):
        """
        Archives relevant project reports and data files into a ZIP archive.
        This provides a snapshot of the project at closeout.
        """
        archive_name = f"project_{project_id}_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        archive_path_base = os.path.join(self.archive_dir, archive_name)

        # Create a temporary directory to collect files before zipping
        temp_archive_folder = os.path.join(self.archive_dir, f"temp_{project_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        os.makedirs(temp_archive_folder, exist_ok=True)

        files_to_archive = []

        # 1. Add generated reports
        for report in report_paths:
            if report and os.path.exists(report):
                shutil.copy(report, temp_archive_folder)
                files_to_archive.append(os.path.basename(report))
                logger.info(f"Added report to archive: {report}")

        # 2. Add a snapshot of project's main data tables as CSVs (optional but good practice)
        # You'd need to fetch data from wbs_elements, actual_costs, progress_updates, etc.
        # and save them as temporary CSVs.
        # Corrected queries to use ProjectID and be parameterized.
        project_tables_queries = {
            'wbs_elements': "SELECT * FROM wbs_elements WHERE ProjectID = ?",
            'project_budgets': "SELECT * FROM project_budgets WHERE ProjectID = ?",
            'actual_costs': "SELECT * FROM actual_costs WHERE ProjectID = ?",
            'progress_updates': "SELECT * FROM progress_updates WHERE ProjectID = ?"
            # Add other relevant tables like MaterialLog, Tasks if desired for archive
        }

        for table_name, query_template in project_tables_queries.items():
            rows = self.db_manager.execute_query(query_template, (project_id,), fetch_all=True)
            if rows:
                df = pd.DataFrame([dict(row) for row in rows])
                temp_csv_path = os.path.join(temp_archive_folder, f"{table_name}_project_{project_id}.csv")
                df.to_csv(temp_csv_path, index=False)
                files_to_archive.append(os.path.basename(temp_csv_path))
                logger.info(f"Added table data to archive: {table_name}.csv")
            else:
                logger.info(f"No data for table '{table_name}' for project {project_id} to archive.")

        if not files_to_archive:
            logger.warning(f"No files found to archive for project {project_id}.")
            shutil.rmtree(temp_archive_folder) # Clean up empty temp folder
            return False, "No data or reports available to archive."

        # Create the zip archive
        try:
            shutil.make_archive(archive_path_base, 'zip', temp_archive_folder)
            final_archive_path = f"{archive_path_base}.zip"
            logger.info(f"Project ID {project_id} data archived to: {final_archive_path}")
            return True, f"Project data archived successfully to {final_archive_path}."
        except Exception as e:
            logger.error(f"Error creating archive for Project ID {project_id}: {e}")
            return False, f"Failed to create archive: {e}"
        finally:
            # Clean up the temporary folder
            if os.path.exists(temp_archive_folder):
                shutil.rmtree(temp_archive_folder)
                logger.info(f"Cleaned up temporary archive folder: {temp_archive_folder}")

    def closeout_project(self, project_id):
        """
        Orchestrates the complete project closeout process.
        1. Finalize reports.
        2. Mark project as closed.
        3. Archive project data and reports.
        """
        logger.info(f"Starting closeout process for Project ID: {project_id}")

        # Check if project exists and is not already closed
        # Corrected to use ProjectID and ProjectStatusID, and compare with 'Completed' status ID
        project_details_query = """
        SELECT p.ProjectStatusID, ps.StatusName
        FROM Projects p
        JOIN ProjectStatuses ps ON p.ProjectStatusID = ps.ProjectStatusID
        WHERE p.ProjectID = ?
        """
        project_status_row = self.db_manager.execute_query(project_details_query, (project_id,), fetch_one=True)

        if not project_status_row:
            logger.error(f"Project ID {project_id} not found. Cannot close out.")
            return False, f"Project ID {project_id} not found."

        # Check if project status is already 'Completed' or 'Closed'
        # 'Completed' is the status set by mark_project_closed.
        # 'Closed' might be an alternative name in some contexts or future states.
        if project_status_row['StatusName'] == constants.PROJECT_STATUS_COMPLETED or \
           project_status_row['StatusName'] == constants.PROJECT_STATUS_CLOSED:
            logger.warning(f"Project ID {project_id} is already '{project_status_row['StatusName']}'.")
            return False, f"Project ID {project_id} is already '{project_status_row['StatusName']}'."

        # Step 1: Finalize Reports
        reports_info, reports_status, reports_msg = self.finalize_project_reports(project_id)
        if not reports_status:
            logger.error(f"Closeout halted: Failed to finalize reports for project {project_id}. Reason: {reports_msg}")
            return False, f"Closeout halted: Failed to finalize reports. Reason: {reports_msg}"
        logger.info(f"Reports finalized for project {project_id}.")

        # Collect paths of successfully generated reports for archiving
        report_paths_for_archive = [r['path'] for r in reports_info if r['path'] is not None]

        # Step 2: Mark Project as Closed
        close_status, close_msg = self.mark_project_closed(project_id)
        if not close_status:
            logger.error(f"Closeout halted: Failed to mark project {project_id} as closed. Reason: {close_msg}")
            return False, f"Closeout halted: Failed to mark project as closed. Reason: {close_msg}"
        logger.info(f"Project {project_id} status updated to 'Closed'.")


        # Step 3: Archive Project Data
        archive_status, archive_msg = self.archive_project_data(project_id, report_paths_for_archive)
        if not archive_status:
            logger.warning(f"Project {project_id} was closed, but archiving failed. Reason: {archive_msg}")
            # Project is still closed, but archiving issue noted.
            # return True, f"Project closed, but archiving failed: {archive_msg}" # Original
        # Even if archiving fails, the project is marked closed. Success message should reflect overall process.

        # TODO: Future Enhancement - Cost Code Closure and Task Progression
        # - Identify all relevant cost codes for the project.
        # - Mark them as closed in a 'CostCodes' or similar table (prevent further posting).
        # - Trigger any final task status updates in a 'Tasks' or 'WBS_Elements' table (e.g., set to 'Closed').
        # - This might involve new methods or calls to other modules.
        logger.info("Placeholder: Logic for cost code closure and final task status updates would go here.")

        if not archive_status: # Re-check for final message
             return True, f"Project closed successfully, but data archiving encountered an issue: {archive_msg}"

        logger.info(f"Project {project_id} closeout complete and archived successfully.")
        return True, "Project closeout process completed successfully."

if __name__ == "__main__":
    # This block demonstrates how the Closeout module can be used.

    print("--- Testing Closeout Module ---")

    # Ensure a clean database for testing the full flow
    import os
    from integration import Integration
    from data_processing import DataProcessing
    from project_planning import ProjectPlanning
    from execution_management import ExecutionManagement
    from database_manager import DatabaseManager

    test_db_path = Config.get_database_path()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Cleaned up existing database at: {test_db_path}")

    # Initialize DatabaseManager (singleton)
    _ = DatabaseManager()

    # --- Simulate full data flow up to Execution Management ---
    sample_csv_path = os.path.join(Config.get_data_dir(), 'sample_estimate_for_closeout.csv')
    sample_data = {
        'Cost Code': ['01-010', '02-100', '03-200'],
        'Description': ['Mobilization', 'Site Prep', 'Concrete Footings'],
        'Quantity': [1.0, 500.0, 15.0],
        'Unit': ['LS', 'SY', 'CY'],
        'Unit Cost': [5000.00, 15.00, 300.00],
        'Total Cost': [5000.00, 7500.00, 4500.00],
        'Phase': ['Pre-Construction', 'Foundation', 'Foundation']
    }
    sample_df = pd.DataFrame(sample_data)
    sample_df.to_csv(sample_csv_path, index=False)

    integration_module = Integration()
    integration_module.import_estimate_from_csv(sample_csv_path)

    data_processor = DataProcessing()
    data_processor.process_estimate_data()

    project_planner = ProjectPlanning()
    project_id, project_msg = project_planner.create_project("Community Center Build", "2024-01-01", "2024-06-30")
    if not project_id:
        print(f"Failed to create project for closeout test: {project_msg}")
        exit()
    print(f"Project created with ID: {project_id}")

    project_planner.generate_wbs_from_estimates(project_id)
    project_planner.generate_project_budget(project_id)
    project_planner.allocate_resources(project_id)

    # Fetch WBS element IDs for actuals
    wbs_elements = project_planner.get_wbs_for_project(project_id)
    wbs_map = {row['wbs_code']: row['id'] for index, row in wbs_elements.iterrows()}
    wbs_mobilization_id = wbs_map.get('01-010')
    wbs_site_prep_id = wbs_map.get('02-100')
    wbs_concrete_footings_id = wbs_map.get('03-200')

    exec_manager = ExecutionManagement()

    # Simulate Actuals and Progress (assume project is near completion or completed)
    print("\n--- Simulating Final Actuals and Progress for Closeout ---")
    exec_manager.record_actual_cost(project_id, wbs_mobilization_id, 'Labor', 'Mobilization Labor', 4800.00, '2024-01-10')
    exec_manager.record_progress_update(project_id, wbs_mobilization_id, 100.0, '2024-01-15', 'Mobilization done')

    exec_manager.record_actual_cost(project_id, wbs_site_prep_id, 'Subcontractor', 'Site Work Sub', 7800.00, '2024-02-28')
    exec_manager.record_progress_update(project_id, wbs_site_prep_id, 100.0, '2024-03-05', 'Site prep done')

    exec_manager.record_actual_cost(project_id, wbs_concrete_footings_id, 'Material', 'Concrete Delivery', 3000.00, '2024-04-01')
    exec_manager.record_actual_cost(project_id, wbs_concrete_footings_id, 'Labor', 'Concrete Install', 1600.00, '2024-04-05') # Total 4600 (slightly over)
    exec_manager.record_progress_update(project_id, wbs_concrete_footings_id, 100.0, '2024-04-10', 'Footings complete')

    # --- Closeout Process ---
    closeout_module = Closeout()

    print(f"\n--- Initiating Closeout for Project ID: {project_id} ---")
    final_status, final_message = closeout_module.closeout_project(project_id)
    print(f"\nCloseout Result: {final_message}")

    # Verify project status
    closed_project_details = db_manager.execute_query(
        "SELECT id, project_name, status, end_date FROM projects WHERE id = ?", (project_id,), fetch_one=True
    )
    if closed_project_details:
        print(f"\nVerified Project Status:")
        print(f"  Project ID: {closed_project_details['id']}")
        print(f"  Project Name: {closed_project_details['project_name']}")
        print(f"  Status: {closed_project_details['status']}")
        print(f"  End Date: {closed_project_details['end_date']}")


    # Test attempting to close an already closed project
    print(f"\n--- Attempting to Close Already Closed Project ID: {project_id} ---")
    re_close_status, re_close_message = closeout_module.closeout_project(project_id)
    print(f"Re-close Attempt Result: {re_close_message}")

    # Clean up test files and database
    if os.path.exists(sample_csv_path):
        os.remove(sample_csv_path)
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Clean up generated reports and archive
    reports_dir = Config.get_reports_dir()
    for item in os.listdir(reports_dir):
        item_path = os.path.join(reports_dir, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path) and item != 'archive': # Keep archive dir for a moment if needed
            shutil.rmtree(item_path)
    # Remove archive directory after testing
    if os.path.exists(closeout_module.archive_dir):
        shutil.rmtree(closeout_module.archive_dir)

    print(f"\nCleaned up test database, sample CSV, and generated reports/archive.")
