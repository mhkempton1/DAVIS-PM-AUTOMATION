import unittest
import os
import sys
import sqlite3
import pandas as pd

# Add the parent directory (project_management_system) to sys.path
# to allow imports of modules like project_startup, database_manager, etc.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from project_startup import ProjectStartup
from database_manager import DatabaseManager, db_manager as global_db_manager
from configuration import Config

class TestProjectStartup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Set up for all tests in this class.
        Use a dedicated test database.
        """
        cls.test_db_path = os.path.join(parent_dir, 'test_project_data.db')
        Config.DATABASE_PATH = cls.test_db_path # Override config for DB path

        # Ensure any existing test DB is removed for a clean start
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

        # Reset the global db_manager instance to use the new test_db_path
        # This is a bit of a hack for singletons; cleaner ways might involve dependency injection
        # or a configurable db_path in DatabaseManager itself.
        DatabaseManager._instance = None
        cls.db_manager = DatabaseManager() # This will initialize and apply schema to test_project_data.db

        # ---- DEBUG code removed ----

        cls.project_startup = ProjectStartup(cls.db_manager) # Pass the test-specific db_manager

        # Pre-populate necessary lookup data if not handled by schema or if specific IDs are needed
        # Example: Ensure 'Pending' status and a default customer exist.
        # The schema.sql should already insert 'Pending' status.
        # We need a customer for project creation due to NOT NULL constraint.
        try:
            cls.db_manager.execute_query(
                "INSERT OR IGNORE INTO CustomerTypes (TypeName) VALUES ('TestType')", commit=True
            )
            cls.db_manager.execute_query(
                "INSERT OR IGNORE INTO Customers (CustomerID, CustomerName, CustomerTypeID) VALUES (1, 'Test Customer', (SELECT CustomerTypeID FROM CustomerTypes WHERE TypeName = 'TestType'))",
                commit=True
            )
            # Ensure 'Pending' status exists and get its ID
            pending_status_row = cls.db_manager.execute_query("SELECT ProjectStatusID FROM ProjectStatuses WHERE StatusName = 'Pending'", fetch_one=True)
            if not pending_status_row:
                # This should not happen if schema.sql is correct and ran
                raise Exception("Critical: 'Pending' status not found in test database after schema application.")
            cls.pending_status_id = pending_status_row['ProjectStatusID']

        except sqlite3.Error as e:
            print(f"SQLite error during test setup: {e}")
            # This might indicate schema.sql issues or other DB problems
            # Depending on the error, you might want to fail the test suite here
            raise
        except Exception as e:
            print(f"General error during test setup: {e}")
            raise


    @classmethod
    def tearDownClass(cls):
        """
        Clean up after all tests in this class.
        """
        cls.db_manager.close_connection()
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        # Restore original db_manager if necessary, though for isolated test runs it might not matter
        DatabaseManager._instance = None
        Config.DATABASE_PATH = os.path.join(parent_dir, 'project_data.db') # Restore original path
        _ = DatabaseManager() # Re-initialize global one with original path

    def setUp(self):
        """
        Set up before each test method.
        Could be used to clean specific tables or reset state if needed between tests.
        For now, assuming tearDownClass handles the main DB cleanup.
        """
        # logger is not defined in this scope, so commenting out direct logger calls for now.
        # Will rely on print for debug or pass logger instance if needed.
        # print(f"TEST_DEBUG: setUp: self.db_manager instance: {id(self.db_manager)}")
        # print(f"TEST_DEBUG: setUp: self.project_startup.db_manager instance: {id(self.project_startup.db_manager)}")
        self.assertIs(self.db_manager, self.project_startup.db_manager, "Test's db_manager and ProjectStartup's db_manager are not the same instance!")

        # print("TEST_DEBUG: setUp: Attempting to clear Projects, wbs_elements, and processed_estimates before test.")
        delete_projects_success = self.db_manager.execute_query("DELETE FROM Projects", commit=True)
        delete_wbs_success = self.db_manager.execute_query("DELETE FROM wbs_elements", commit=True)
        delete_processed_estimates_success = self.db_manager.execute_query("DELETE FROM processed_estimates", commit=True)

        # print(f"TEST_DEBUG: setUp: DELETE FROM Projects result: {delete_projects_success}")
        # print(f"TEST_DEBUG: setUp: DELETE FROM wbs_elements result: {delete_wbs_success}")
        # print(f"TEST_DEBUG: setUp: DELETE FROM processed_estimates result: {delete_processed_estimates_success}")

        self.assertTrue(delete_projects_success, "Failed to delete projects in setUp.")
        self.assertTrue(delete_wbs_success, "Failed to delete WBS elements in setUp.")
        self.assertTrue(delete_processed_estimates_success, "Failed to delete processed_estimates in setUp.")

        project_count = self.db_manager.execute_query("SELECT COUNT(*) FROM Projects", fetch_one=True)[0]
        # print(f"TEST_DEBUG: setUp: Project count after delete: {project_count}")
        self.assertEqual(project_count, 0, "Projects table should be empty at start of test after setUp delete.")

        wbs_count = self.db_manager.execute_query("SELECT COUNT(*) FROM wbs_elements", fetch_one=True)[0]
        # print(f"TEST_DEBUG: setUp: WBS count after delete: {wbs_count}")
        self.assertEqual(wbs_count, 0, "WBS elements table should be empty at start of test after setUp delete.")

        processed_estimates_count = self.db_manager.execute_query("SELECT COUNT(*) FROM processed_estimates", fetch_one=True)[0]
        # print(f"TEST_DEBUG: setUp: Processed Estimates count after delete: {processed_estimates_count}")
        self.assertEqual(processed_estimates_count, 0, "Processed Estimates table should be empty at start of test after setUp delete.")

    def tearDown(self):
        """
        Clean up after each test method.
        Primary cleanup moved to setUp. This can be used for other specific post-test cleanup if needed.
        """
        pass

    # --- Test Cases Will Go Here ---

    def test_create_project_success(self):
        project_name = "Test Project Alpha"
        start_date = "2024-01-01"
        # end_date is now calculated by UI/caller, duration_days is passed
        # For test, let's assume a duration and calculate end_date like UI would
        from utils import calculate_end_date as calc_end_date_util # Alias to avoid conflict
        duration_days = 30
        calculated_end_date = calc_end_date_util(start_date, duration_days)
        self.assertNotIn("Error:", calculated_end_date, "End date calculation failed in test setup")


        project_id, msg = self.project_startup.create_project(project_name, start_date, calculated_end_date, duration_days)

        self.assertIsNotNone(project_id, "Project ID should not be None on successful creation.")
        self.assertIn("created successfully", msg.lower())
        # logger.info(f"TEST_DEBUG: test_create_project_success: project_id returned by create_project: {project_id}") # Removed logger call

        # Verify in DB
        created_project = self.db_manager.execute_query(
            "SELECT p.ProjectName, p.StartDate, p.EndDate, ps.StatusName FROM Projects p JOIN ProjectStatuses ps ON p.ProjectStatusID = ps.ProjectStatusID WHERE p.ProjectID = ?",
            (project_id,),
            fetch_one=True
        )
        # logger.info(f"TEST_DEBUG: test_create_project_success: created_project from DB: {created_project}") # Removed logger call
        self.assertIsNotNone(created_project, "Project not found in DB after creation.")
        self.assertEqual(created_project['ProjectName'], project_name)
        self.assertEqual(created_project['StartDate'], start_date)
        self.assertEqual(created_project['EndDate'], calculated_end_date) # Use calculated_end_date for assertion
        self.assertEqual(created_project['StatusName'], "Pending")

    def test_create_project_existing_name(self):
        project_name = "Test Project Beta"
        from utils import calculate_end_date as calc_end_date_util # Alias
        duration1 = 60
        start_date1 = "2024-01-01"
        end_date1 = calc_end_date_util(start_date1, duration1)
        self.project_startup.create_project(project_name, start_date1, end_date1, duration1) # Create first time

        duration2 = 90
        start_date2 = "2025-01-01"
        end_date2 = calc_end_date_util(start_date2, duration2)
        project_id_again, msg_again = self.project_startup.create_project(project_name, start_date2, end_date2, duration2)

        self.assertIsNotNone(project_id_again, "Project ID should be returned even if project exists.")
        self.assertIn("already exists", msg_again.lower())

        # Verify only one project with this name exists
        count = self.db_manager.execute_query(
            "SELECT COUNT(*) FROM Projects WHERE ProjectName = ?", (project_name,), fetch_one=True
        )[0]
        self.assertEqual(count, 1, "Should not create a duplicate project with the same name.")

    def test_get_all_projects_with_status_no_projects(self):
        projects = self.project_startup.get_all_projects_with_status()
        self.assertEqual(len(projects), 0, "Should return an empty list if no projects exist.")

    def test_get_all_projects_with_status_multiple_projects(self):
        self.project_startup.create_project("Project Gamma", "2024-01-01", "2024-01-31")
        self.project_startup.create_project("Project Delta", "2024-02-01", "2024-02-28")

        projects = self.project_startup.get_all_projects_with_status()
        self.assertEqual(len(projects), 2, "Should return all created projects.")

        project_names_fetched = sorted([p['ProjectName'] for p in projects])
        self.assertEqual(project_names_fetched, ["Project Delta", "Project Gamma"]) # Default order is DESC ID

        for p in projects:
            self.assertIn('ProjectID', p)
            self.assertIn('ProjectName', p)
            self.assertIn('StatusName', p)
            if p['ProjectName'] == "Project Gamma":
                self.assertEqual(p['StatusName'], "Pending")

    def _create_dummy_project(self, name="Dummy Project for WBS"):
        """Helper to create a project and return its ID."""
        from utils import calculate_end_date as calc_end_date_util
        start_date = "2023-01-01"
        duration_days = 10
        end_date = calc_end_date_util(start_date, duration_days)
        project_id, _ = self.project_startup.create_project(name, start_date, end_date, duration_days)
        self.assertIsNotNone(project_id)
        return project_id

    def _create_dummy_wbs_element(self, project_id, wbs_code="WBS-001", description="Dummy WBS Item", estimated_cost=100.0, status="Planned"):
        """Helper to insert a WBS element directly and return its ID."""
        query = """
        INSERT INTO wbs_elements (ProjectID, WBSCode, Description, EstimatedCost, Status)
        VALUES (?, ?, ?, ?, ?)
        """
        success = self.db_manager.execute_query(query, (project_id, wbs_code, description, estimated_cost, status), commit=True)
        self.assertTrue(success, "Failed to create dummy WBS element for test.")
        wbs_id = self.db_manager.execute_query("SELECT last_insert_rowid()", fetch_one=True)[0]
        self.assertIsNotNone(wbs_id)
        return wbs_id

    def test_get_wbs_element_details_exists(self):
        project_id = self._create_dummy_project()
        wbs_desc = "Detailed WBS Item"
        wbs_id = self._create_dummy_wbs_element(project_id, description=wbs_desc)

        details = self.project_startup.get_wbs_element_details(wbs_id)
        self.assertIsNotNone(details)
        self.assertEqual(details['WBSElementID'], wbs_id)
        self.assertEqual(details['ProjectID'], project_id)
        self.assertEqual(details['Description'], wbs_desc)

    def test_get_wbs_element_details_not_exists(self):
        details = self.project_startup.get_wbs_element_details(99999) # Non-existent ID
        self.assertIsNone(details)

    def test_update_wbs_element_success(self):
        project_id = self._create_dummy_project()
        wbs_id = self._create_dummy_wbs_element(project_id, description="Old Description", estimated_cost=100.0, status="Planned")

        updates = {
            "Description": "New Updated Description",
            "EstimatedCost": 150.75,
            "Status": "In Progress"
        }
        success, msg = self.project_startup.update_wbs_element(wbs_id, updates)
        self.assertTrue(success)
        self.assertIn("updated successfully", msg.lower())

        updated_details = self.project_startup.get_wbs_element_details(wbs_id)
        self.assertEqual(updated_details['Description'], "New Updated Description")
        self.assertEqual(updated_details['EstimatedCost'], 150.75)
        self.assertEqual(updated_details['Status'], "In Progress")

    def test_update_wbs_element_non_existent(self):
        success, msg = self.project_startup.update_wbs_element(88888, {"Description": "Fail Update"})
        self.assertFalse(success)
        self.assertIn("not found", msg.lower())

    def test_update_wbs_element_no_valid_fields(self):
        project_id = self._create_dummy_project()
        wbs_id = self._create_dummy_wbs_element(project_id)
        success, msg = self.project_startup.update_wbs_element(wbs_id, {"InvalidField": "value"})
        self.assertFalse(success)
        self.assertIn("no valid fields", msg.lower())

    def test_update_wbs_element_empty_updates(self):
        project_id = self._create_dummy_project()
        wbs_id = self._create_dummy_wbs_element(project_id)
        success, msg = self.project_startup.update_wbs_element(wbs_id, {})
        self.assertFalse(success)
        self.assertIn("no updates provided", msg.lower())

    def _insert_dummy_processed_estimate(self, project_id=None, cost_code="CC1", description="Desc1", total_cost=100.0, raw_estimate_id=1):
        """Helper to insert a processed estimate and return its ProcessedEstimateID."""
        # Note: schema_sql for processed_estimates uses PascalCase for column names.
        query = """
        INSERT INTO processed_estimates (ProjectID, CostCode, Description, Quantity, Unit, UnitCost, TotalCost, Phase, RawEstimateID)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Make Quantity and UnitCost consistent with TotalCost for this dummy data
        quantity = 1.0
        unit_cost = total_cost
        unit = "LS"
        phase = "TestPhase"

        success = self.db_manager.execute_query(query, (project_id, cost_code, description, quantity, unit, unit_cost, total_cost, phase, raw_estimate_id), commit=True)
        self.assertTrue(success, "Failed to insert dummy processed estimate.")
        # Fetch ProcessedEstimateID (assuming it's an alias for rowid or an auto-incrementing PK)
        # The actual PK name in schema.sql is ProcessedEstimateID
        last_id = self.db_manager.execute_query("SELECT last_insert_rowid()", fetch_one=True)[0]
        return last_id

    def test_generate_wbs_from_estimates_no_estimates(self):
        project_id = self._create_dummy_project("Project WBS No Estimates")
        success, msg = self.project_startup.generate_wbs_from_estimates(project_id)
        self.assertTrue(success) # Should succeed, but indicate no data
        self.assertIn("no unlinked estimates were found", msg.lower()) # Adjusted expected message based on current implementation

        wbs_df = self.project_startup.get_wbs_for_project(project_id)
        self.assertTrue(wbs_df.empty, "WBS should be empty if no estimates.")

    def test_generate_wbs_from_estimates_with_data(self):
        project_id = self._create_dummy_project("Project WBS With Data")
        # Insert a processed estimate that is initially unlinked (ProjectID is NULL)
        self._insert_dummy_processed_estimate(project_id=None, cost_code="WBS-GEN-CC1", description="Estimate for WBS Gen", total_cost=1000.0, raw_estimate_id=101)
        self._insert_dummy_processed_estimate(project_id=None, cost_code="WBS-GEN-CC2", description="Another Est for WBS Gen", total_cost=500.0, raw_estimate_id=102)

        success, msg = self.project_startup.generate_wbs_from_estimates(project_id)
        self.assertTrue(success, f"generate_wbs_from_estimates failed: {msg}")
        self.assertIn("wbs generated successfully", msg.lower())

        # Verify WBS elements created
        wbs_df = self.project_startup.get_wbs_for_project(project_id)
        self.assertEqual(len(wbs_df), 2, "Incorrect number of WBS elements generated.")
        self.assertIn("WBS-GEN-CC1", wbs_df['WBSCode'].values) # Schema uses WBSCode
        self.assertIn("WBS-GEN-CC2", wbs_df['WBSCode'].values)

        # Verify total estimated cost on project
        project_details = self.project_startup.get_project_details(project_id)
        self.assertEqual(project_details['EstimatedCost'], 1500.0) # Schema uses EstimatedCost

        # Verify processed_estimates are now linked to this project_id
        linked_estimates = self.db_manager.execute_query(
            "SELECT COUNT(*) FROM processed_estimates WHERE ProjectID = ? AND CostCode LIKE 'WBS-GEN-CC%'", (project_id,), fetch_one=True
        )[0]
        self.assertEqual(linked_estimates, 2, "Processed estimates were not correctly linked to the project.")

    def test_generate_project_budget_no_wbs(self):
        project_id = self._create_dummy_project("Project Budget No WBS")
        success, msg = self.project_startup.generate_project_budget(project_id)
        self.assertFalse(success) # Expect failure as no WBS elements
        self.assertIn("no wbs elements found", msg.lower())

    def test_generate_project_budget_with_wbs(self):
        project_id = self._create_dummy_project("Project Budget With WBS")
        self._create_dummy_wbs_element(project_id, wbs_code="BUDGET-WBS1", estimated_cost=1200.0)
        self._create_dummy_wbs_element(project_id, wbs_code="BUDGET-WBS2", estimated_cost=800.0)

        success, msg = self.project_startup.generate_project_budget(project_id)
        self.assertTrue(success, f"generate_project_budget failed: {msg}")

        budget_df = self.project_startup.get_budget_for_project(project_id)
        self.assertEqual(len(budget_df), 2)
        # Schema: BudgetType (used WBSCode), Amount
        self.assertAlmostEqual(budget_df['Amount'].sum(), 2000.0)
        self.assertIn("BUDGET-WBS1", budget_df['BudgetType'].values)


    def test_allocate_resources_no_wbs_estimates(self):
        project_id = self._create_dummy_project("Project Res No Data")
        # Ensure no WBS elements with linked processed_estimates
        success, msg = self.project_startup.allocate_resources(project_id)
        self.assertFalse(success) # Expected to fail or return specific message if no data
        self.assertIn("no wbs elements with linked estimates", msg.lower())

    def test_allocate_resources_with_data(self):
        project_id = self._create_dummy_project("Project Res With Data")
        # Create a processed estimate (unlinked)
        processed_estimate_id_1 = self._insert_dummy_processed_estimate(project_id=None, cost_code="RES-CC1", description="Resource Item 1", total_cost=700.0, raw_estimate_id=201)
        # Create a WBS element and link it to this processed_estimate_id by calling generate_wbs
        # This ensures wbs_elements.ProcessedEstimateID is populated.
        # First, ensure the processed estimate is linked to project by WBS generation
        wbs_gen_success, _ = self.project_startup.generate_wbs_from_estimates(project_id)
        self.assertTrue(wbs_gen_success, "WBS generation step failed during resource allocation test setup.")

        # Now allocate resources
        success, msg = self.project_startup.allocate_resources(project_id)
        self.assertTrue(success, f"allocate_resources failed: {msg}")

        # Verify WBSElementResources
        wbs_resources_df = self.db_manager.execute_query(
             "SELECT wr.* FROM WBSElementResources wr JOIN wbs_elements wbs ON wr.WBSElementID = wbs.WBSElementID WHERE wbs.ProjectID = ?",
             (project_id,), fetch_all=True
        )
        wbs_resources_df = pd.DataFrame([dict(row) for row in wbs_resources_df]) if wbs_resources_df else pd.DataFrame()

        self.assertGreater(len(wbs_resources_df), 0, "No WBSElementResources created.")
        self.assertEqual(wbs_resources_df.iloc[0]['ResourceDescription'], "Resource Item 1")
        self.assertEqual(wbs_resources_df.iloc[0]['TotalEstimatedCost'], 700.0)


if __name__ == '__main__':
    unittest.main()
