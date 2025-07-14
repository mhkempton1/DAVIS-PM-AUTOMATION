import pandas as pd
import logging
import uuid # For generating unique project IDs if needed, otherwise use auto-increment
from datetime import datetime # Added for document notes timestamp
from database_manager import db_manager # Import the singleton database manager
from configuration import Config
from exceptions import AppValidationError, AppOperationConflictError, AppDatabaseError
import constants

# Set up logging for the Project Startup Module
# BasicConfig is now handled in main.py for the application.
# Modules should just get their logger instance.
logger = logging.getLogger(__name__)

class ProjectStartup:
    """
    Handles project creation, setup, and initial status management.
    It will also include functionality for Work Breakdown Structures (WBS),
    schedules, budgets, and resource allocations based on processed estimate data.
    """
    def __init__(self, db_m_instance): # Modified to accept db_manager instance
        """
        Initializes the ProjectStartup module.
        Database tables are expected to be initialized by DatabaseManager via schema.sql.
        """
        self.db_manager = db_m_instance # Use passed instance
        # self._initialize_db_tables() # This is now handled by DatabaseManager executing schema.sql
        logger.info("Project Startup module initialized with provided db_manager.")

    def _get_processed_estimates_df(self):
        """
        Retrieves processed estimate data from the database into a pandas DataFrame.
        """
        query = "SELECT * FROM processed_estimates ORDER BY id ASC"
        rows = self.db_manager.execute_query(query, fetch_all=True)
        if rows:
            data = [dict(row) for row in rows]
            return pd.DataFrame(data)
        return pd.DataFrame()

    def _get_processed_estimates_for_project_df(self, project_id):
        """
        Retrieves processed estimate data from the database for a specific project_id
        into a pandas DataFrame.
        """
        if not project_id:
            logger.warning("Project ID not provided to _get_processed_estimates_for_project_df.")
            return pd.DataFrame()
        # Use schema casing: ProjectID, ProcessedEstimateID
        query = "SELECT * FROM processed_estimates WHERE ProjectID = ? ORDER BY ProcessedEstimateID ASC"
        rows = self.db_manager.execute_query(query, (project_id,), fetch_all=True)
        if rows:
            data = [dict(row) for row in rows]
            return pd.DataFrame(data)
        logger.info(f"No processed estimates found for project_id {project_id}.")
        return pd.DataFrame()

    def create_project(self, project_name, start_date=None, end_date=None, duration_days=None):
        """
        Creates a new project entry in the 'Projects' table.
        'end_date' is the calculated end date. 'duration_days' is also stored.
        Returns the project_id if successful, None otherwise.
        Uses the 'Projects' table structure from schema.sql.
        """
        if not project_name or not isinstance(project_name, str):
            # This validation now typically happens before, or an exception is raised.
            # For robustness, keeping it, but it should ideally not be hit if called from validated GUI.
            logger.error("Project creation failed: Project name must be a non-empty string.")
            raise AppValidationError("Project name must be a non-empty string.")
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                logger.error(f"Project creation failed: Invalid start_date format '{start_date}'. Use YYYY-MM-DD.")
                return None, "Invalid start_date format. Use YYYY-MM-DD."
        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                logger.error(f"Project creation failed: Invalid end_date format '{end_date}'. Use YYYY-MM-DD.")
                return None, "Invalid end_date format. Use YYYY-MM-DD."
        if start_date and end_date:
            if datetime.strptime(start_date, "%Y-%m-%d") > datetime.strptime(end_date, "%Y-%m-%d"):
                logger.error("Project creation failed: Start date cannot be after end date.")
                return None, "Start date cannot be after end date."
        if duration_days is not None:
            if not isinstance(duration_days, int) or duration_days < 0:
                logger.error(f"Project creation failed: Duration days '{duration_days}' must be a non-negative integer.")
                return None, "Duration days must be a non-negative integer."

        # Check for existing project with the same name (using ProjectName from schema.sql)
        existing_project_query = "SELECT ProjectID FROM Projects WHERE ProjectName = ?"
        existing_project = self.db_manager.execute_query(existing_project_query, (project_name,), fetch_one=True)
        if existing_project:
            logger.warning(f"Project '{project_name}' already exists with ID: {existing_project['ProjectID']}. Skipping creation.")
            return existing_project['ProjectID'], f"Project '{project_name}' already exists."

        # Get ProjectStatusID for 'Pending'
        pending_status_query = "SELECT ProjectStatusID FROM ProjectStatuses WHERE StatusName = ?"
        status_row = self.db_manager.execute_query(pending_status_query, (constants.PROJECT_STATUS_PENDING,), fetch_one=True)
        if not status_row:
            msg = f"Could not find '{constants.PROJECT_STATUS_PENDING}' status in ProjectStatuses table. Please ensure schema is up to date."
            logger.error(msg)
            raise AppValidationError(msg)
        pending_status_id = status_row['ProjectStatusID']

        # Placeholder for CustomerID as it's NOT NULL in schema.sql Projects table
        # In a real app, this would come from user input or another source.
        # TODO: Refactor to remove hardcoded CustomerID. Should accept customer info or have a robust way to select/create.
        default_customer_id = 1

        # The 'end_date' parameter is now the calculated end_date.
        # 'duration_days' is a new parameter to be stored.

        insert_query = """
        INSERT INTO Projects (ProjectName, StartDate, EndDate, ProjectStatusID, CustomerID, EstimatedCost, DurationDays)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        # Placeholder for EstimatedCost, will be updated after WBS/budgeting
        initial_estimated_cost = 0.0
        # Ensure duration_days is passed to this method by the caller (e.g., UI action)
        # For now, let's assume create_project signature is changed or duration_days is passed.
        # The plan implies create_project itself doesn't calculate, but receives calculated end_date and duration.
        # So, its signature should be: create_project(self, project_name, start_date, calculated_end_date, duration_days)
        # However, the original method only had project_name, start_date, end_date.
        # Let's adjust the method signature to include duration_days and use the passed end_date as calculated.

        # New signature will be: create_project(self, project_name, start_date, end_date, duration_days)
        # where end_date is the one calculated by the UI layer before calling this.

        params = (project_name, start_date, end_date, pending_status_id, default_customer_id, initial_estimated_cost, duration_days)

        success_insert = self.db_manager.execute_query(insert_query, params, commit=True)
        logger.info(f"PROJECT_STARTUP: create_project execute_query result for INSERT: {success_insert} for project {project_name}")

        if success_insert:
            # Use ProjectID as per schema.sql, not 'id'
            project_id_row = self.db_manager.execute_query("SELECT last_insert_rowid()", fetch_one=True)
            if project_id_row:
                project_id = project_id_row[0]
                logger.info(f"PROJECT_STARTUP: Project '{project_name}' (Retrieved ID: {project_id}) created with Start: {start_date}, End: {end_date}, Duration: {duration_days} days, Status: 'Pending'.")

                # DEBUG: Verify immediately after insert
                verify_project = self.db_manager.execute_query("SELECT * FROM Projects WHERE ProjectID = ?", (project_id,), fetch_one=True)
                logger.info(f"PROJECT_STARTUP: Immediate verification for ProjectID {project_id}: {verify_project}")

                return project_id, f"Project '{project_name}' created successfully with End Date {end_date} (Duration: {duration_days} days) and status 'Pending'."
            else:
                logger.error(f"PROJECT_STARTUP: Failed to retrieve ID for newly created project '{project_name}'. last_insert_rowid() returned: {project_id_row}")
                return None, f"Failed to get ID for project '{project_name}' after creation."
        else:
            logger.error(f"PROJECT_STARTUP: Insert query failed for project '{project_name}'. execute_query returned: {success_insert}.")
            return None, f"Failed to create project '{project_name}'."

    def generate_wbs_from_estimates(self, project_id):
        """
        Generates Work Breakdown Structure (WBS) elements from processed estimate data
        and links them to the specified project.
        Automatically updates 'project_id' in 'processed_estimates' table for those estimates
        that are newly linked and used for WBS generation.
        """
        if not project_id:
            logger.error("Cannot generate WBS: No project ID provided.")
            return False, "No project ID provided."

        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Step 1: Link unassigned processed estimates to this project (within transaction)
            # Check how many are unlinked first
            query_count_unlinked = "SELECT COUNT(*) FROM processed_estimates WHERE ProjectID IS NULL"
            cursor.execute(query_count_unlinked)
            count_result = cursor.fetchone()
            num_unlinked_before = count_result[0] if count_result else 0

            if num_unlinked_before > 0:
                update_estimates_query = "UPDATE processed_estimates SET ProjectID = ? WHERE ProjectID IS NULL"
                cursor.execute(update_estimates_query, (project_id,))
                # Verify rows affected if necessary, cursor.rowcount for sqlite
                logger.info(f"Linked {cursor.rowcount} unassigned processed estimates to project ID {project_id}.")
            else:
                logger.info(f"No unassigned processed estimates found to link for project {project_id}.")

            # Step 2: Get processed estimates specifically for THIS project
            # This still uses db_manager.execute_query for fetching, which is fine as it doesn't commit.
            processed_df = self._get_processed_estimates_for_project_df(project_id)
            if processed_df.empty:
                conn.commit() # Commit linking if that was done
                logger.info(f"No processed estimate data found for project ID {project_id} to generate WBS.")
                return True, "No processed estimate data for this project to generate WBS."

            logger.info(f"Generating WBS for project ID: {project_id} with {len(processed_df)} estimates...")

            # Check if project exists (optional, but good practice)
            project_details = self.get_project_details(project_id) # Uses db_manager.execute_query
            if not project_details:
                conn.rollback() # Nothing to commit if project doesn't exist
                return False, f"Project with ID {project_id} not found."

            # Clear existing WBS elements for the project
            delete_wbs_query = "DELETE FROM wbs_elements WHERE ProjectID = ?"
            cursor.execute(delete_wbs_query, (project_id,))
            logger.info(f"Cleared {cursor.rowcount} existing WBS elements for project {project_id}.")

            wbs_data_aggregated = self._aggregate_estimates_for_wbs(processed_df)

            created_wbs_count = 0
            project_total_estimated_cost = 0.0

            for wbs_code, data in wbs_data_aggregated.items():
                main_processed_estimate_id = data['processed_estimate_ids'][0] if data['processed_estimate_ids'] else None
                insert_wbs_query = """
                INSERT INTO wbs_elements (ProjectID, WBSCode, Description, EstimatedCost, ProcessedEstimateID, Status)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                params = (project_id, wbs_code, data['description'], data['total_cost'], main_processed_estimate_id, constants.WBS_STATUS_PLANNED)
                cursor.execute(insert_wbs_query, params)
                if cursor.lastrowid:
                    created_wbs_count += 1
                    project_total_estimated_cost += data['total_cost']
                else:
                    # This path might not be hit if execute throws error, but good for safety
                    logger.error(f"Failed to insert WBS element for WBSCode {wbs_code} in project {project_id} (no lastrowid).")
                    # No explicit rollback here, let the main exception handler do it.

            if created_wbs_count != len(wbs_data_aggregated):
                 logger.warning(f"Mismatch in WBS items to create ({len(wbs_data_aggregated)}) and actually created ({created_wbs_count}). Review for errors.")
                 # Potentially raise an error to trigger rollback if this is critical

            # Update the project's total estimated cost
            update_project_cost_query = "UPDATE Projects SET EstimatedCost = ? WHERE ProjectID = ?"
            cursor.execute(update_project_cost_query, (project_total_estimated_cost, project_id))
            logger.info(f"Updated EstimatedCost for project {project_id} to {project_total_estimated_cost:.2f} (affected rows: {cursor.rowcount}).")

            conn.commit()
            logger.info(f"Transaction committed for WBS generation, project {project_id}.")
            if created_wbs_count > 0:
                return True, f"Successfully generated/updated {created_wbs_count} WBS items for project {project_id}."
            else:
                # This case might occur if processed_df was not empty but wbs_data_aggregated ended up empty,
                # or if all inserts somehow failed without raising an error caught by the outer try-except.
                return True, "WBS generation processed, but no new WBS items were created. Check logs if estimates were expected."

        except Exception as e: # Catching a more general exception
            if conn:
                conn.rollback()
            logger.error(f"Error during WBS generation for project {project_id}: {e}", exc_info=True)
            return False, f"Failed to generate WBS due to an error: {e}"

    def _aggregate_estimates_for_wbs(self, processed_df: pd.DataFrame) -> dict:
        """
        Aggregates processed estimate data to form WBS elements.
        Args:
            processed_df: DataFrame of processed estimates for a single project.
        Returns:
            A dictionary where keys are WBSCodes and values are dicts with
            'description', 'total_cost', and 'processed_estimate_ids'.
        """
        wbs_data_aggregated = {}
        if processed_df.empty:
            return wbs_data_aggregated

        for _, row in processed_df.iterrows():
            cost_code = row['CostCode'] # This will be the WBSCode
            description = row['Description']
            # Ensure TotalCost is treated as float, default to 0.0 if missing or invalid
            try:
                estimated_cost = float(row.get('TotalCost', 0.0))
            except (ValueError, TypeError):
                estimated_cost = 0.0

            processed_estimate_id = row['ProcessedEstimateID']

            if cost_code not in wbs_data_aggregated:
                wbs_data_aggregated[cost_code] = {
                    'description': description, # Use description from the first estimate line for this WBSCode
                    'total_cost': 0.0,
                    'processed_estimate_ids': [] # Store all linked estimate IDs
                }
            wbs_data_aggregated[cost_code]['total_cost'] += estimated_cost
            wbs_data_aggregated[cost_code]['processed_estimate_ids'].append(processed_estimate_id)
        return wbs_data_aggregated

    def generate_project_budget(self, project_id):
        """
        Generates a budget for the project based on the estimated costs of WBS elements.
        Populates the 'project_budgets' table.
        """
        if not project_id:
            logger.error("Cannot generate budget: No project ID provided.")
            return False, "No project ID provided."

        # Clear existing budget for this project before generating new one
        # Use schema casing: ProjectID
        self.db_manager.execute_query(
            "DELETE FROM project_budgets WHERE ProjectID = ?", (project_id,), commit=True
        )
        logger.info(f"Cleared existing budget entries for project {project_id}.")

        # Get WBS elements for the project
        # Use schema casing: WBSElementID, WBSCode, Description, EstimatedCost, ProjectID
        wbs_query = "SELECT WBSElementID, WBSCode, Description, EstimatedCost FROM wbs_elements WHERE ProjectID = ?"
        wbs_elements = self.db_manager.execute_query(wbs_query, (project_id,), fetch_all=True)

        if not wbs_elements:
            logger.warning(f"No WBS elements found for project {project_id}. Cannot generate detailed budget.")
            return False, "No WBS elements found for project."

        budget_items_to_insert = []
        for wbs_elem in wbs_elements:
            budget_items_to_insert.append((
                project_id,
                wbs_elem['WBSElementID'],      # Schema: WBSElementID
                wbs_elem['WBSCode'],          # Using WBSCode as budget category (schema: BudgetType)
                wbs_elem['EstimatedCost']     # Schema: Amount
            ))

        insert_budget_query = """
        INSERT INTO project_budgets (ProjectID, WBSElementID, BudgetType, Amount)
        VALUES (?, ?, ?, ?)
        """
        conn = self.db_manager.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.executemany(insert_budget_query, budget_items_to_insert)
                conn.commit()
                logger.info(f"Successfully generated budget for project {project_id} with {len(budget_items_to_insert)} items.")
                return True, f"Budget generated successfully for project {project_id}."
            except Exception as e: # Catching a more general exception, assuming db_manager might raise non-sqlite specific ones
                conn.rollback()
                logger.error(f"Database error generating budget for project {project_id}: {e}")
                return False, f"Database error: {e}"
        else:
            logger.error("Database connection not available to generate budget.")
            return False, "Database connection error."

    def allocate_resources(self, project_id):
        """
        Creates detailed resource breakdown for WBS elements based on linked processed estimates.
        Populates the 'WBSElementResources' table.
        """
        if not project_id:
            logger.error("Cannot allocate WBS resources: No ProjectID provided.")
            return False, "No ProjectID provided for WBS resource allocation."

        # Clear existing WBSElementResources for this project to prevent duplication on re-runs
        # Note: WBSElementResources links to wbs_elements, so deleting by ProjectID requires a join or subquery.
        # For simplicity, we'll fetch WBSElementIDs for the project first.
        wbs_ids_query = "SELECT WBSElementID FROM wbs_elements WHERE ProjectID = ?"
        wbs_id_rows = self.db_manager.execute_query(wbs_ids_query, (project_id,), fetch_all=True)
        if wbs_id_rows:
            wbs_ids_for_project = [row['WBSElementID'] for row in wbs_id_rows]
            placeholders = ','.join(['?'] * len(wbs_ids_for_project))
            delete_query = f"DELETE FROM WBSElementResources WHERE WBSElementID IN ({placeholders})"
            self.db_manager.execute_query(delete_query, tuple(wbs_ids_for_project), commit=True)
            logger.info(f"Cleared existing WBSElementResources for project {project_id}.")
        else:
            logger.info(f"No existing WBS elements found for project {project_id}, so no WBSElementResources to clear.")


        # Fetch WBS elements and their linked ProcessedEstimateID
        query = """
        SELECT wbs.WBSElementID, wbs.ProcessedEstimateID, pe.Description, pe.Quantity, pe.Unit, pe.UnitCost, pe.TotalCost
        FROM wbs_elements wbs
        JOIN processed_estimates pe ON wbs.ProcessedEstimateID = pe.ProcessedEstimateID
        WHERE wbs.ProjectID = ? AND wbs.ProcessedEstimateID IS NOT NULL
        """
        # This query assumes a WBS element is derived from a single processed estimate line.
        # If a WBS element aggregates multiple estimates, this logic would need adjustment.

        wbs_estimate_details = self.db_manager.execute_query(query, (project_id,), fetch_all=True)

        if not wbs_estimate_details:
            logger.warning(f"No WBS elements with linked processed estimates found for project {project_id} for resource allocation.")
            return False, "No WBS elements with linked estimates for resource allocation."

        resources_to_insert = []
        for detail in wbs_estimate_details:
            resource_description = detail['Description']
            resource_type = constants.RESOURCE_TYPE_MATERIAL # Default type
            unit = detail['Unit']
            if unit and 'HR' in unit.upper():
                resource_type = constants.RESOURCE_TYPE_LABOR
            elif unit and 'LS' in unit.upper():
                resource_type = constants.RESOURCE_TYPE_LUMP_SUM
            # Consider adding constants.RESOURCE_TYPE_OTHER if no specific match

            resources_to_insert.append((
                detail['WBSElementID'],
                resource_description,
                resource_type,
                detail['Quantity'],
                unit, # UnitOfMeasure
                detail['UnitCost'],
                detail['TotalCost'] # TotalEstimatedCost
            ))

        if not resources_to_insert:
            logger.info(f"No resources derived from estimates to insert for project {project_id}.")
            return True, "No specific resources to allocate based on linked estimates."

        insert_query = """
        INSERT INTO WBSElementResources
            (WBSElementID, ResourceDescription, ResourceType, Quantity, UnitOfMeasure, UnitCost, TotalEstimatedCost)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Note: The clearing of existing resources is done above and committed separately.
            # If that should be part of this transaction, it needs to be moved here.
            # For now, assuming clearing is a pre-step and this focuses on insertion.

            cursor.executemany(insert_query, resources_to_insert)
            conn.commit()
            logger.info(f"Successfully inserted {len(resources_to_insert)} resource details into WBSElementResources for project {project_id}.")
            return True, f"Successfully allocated {len(resources_to_insert)} WBS resource details."

        except Exception as e: # Catching a more general exception
            if conn:
                conn.rollback()
            logger.error(f"Database error inserting into WBSElementResources for project {project_id}: {e}", exc_info=True)
            return False, f"Database error during WBS resource detail allocation: {e}"

    def get_project_details(self, project_id):
        """Retrieves details for a specific project using schema.sql structure."""
        # Ensure to select from 'Projects' and use 'ProjectID'
        # Also, join with ProjectStatuses to get the status name
        query = """
        SELECT p.*, ps.StatusName
        FROM Projects p
        LEFT JOIN ProjectStatuses ps ON p.ProjectStatusID = ps.ProjectStatusID
        WHERE p.ProjectID = ?
        """
        # p.* will include DurationDays if the schema was applied correctly.
        return self.db_manager.execute_query(query, (project_id,), fetch_one=True)

    def get_wbs_for_project(self, project_id):
        """Retrieves WBS elements for a specific project."""
        query = "SELECT * FROM wbs_elements WHERE ProjectID = ?" # Corrected to ProjectID
        rows = self.db_manager.execute_query(query, (project_id,), fetch_all=True)
        return pd.DataFrame([dict(row) for row in rows]) if rows else pd.DataFrame()

    def get_all_projects_with_status(self):
        """
        Retrieves all projects with their names, IDs, and status names.
        """
        query = """
        SELECT p.ProjectID, p.ProjectName, ps.StatusName
        FROM Projects p
        LEFT JOIN ProjectStatuses ps ON p.ProjectStatusID = ps.ProjectStatusID
        ORDER BY p.ProjectID DESC;
        """
        # Ensure db_manager returns list of dicts or objects that can be dict-like accessed
        projects_data = self.db_manager.execute_query(query, fetch_all=True)
        if projects_data:
            # Convert to list of dicts if not already (depends on db_manager.row_factory)
            return [dict(row) for row in projects_data] # schema.sql uses ProjectID, ProjectName, StatusName
        return []

    def get_wbs_element_details(self, wbs_element_id):
        """
        Retrieves details for a specific WBS element.
        Uses WBSElementID from schema.sql.
        """
        query = "SELECT * FROM wbs_elements WHERE WBSElementID = ?"
        row = self.db_manager.execute_query(query, (wbs_element_id,), fetch_one=True)
        return dict(row) if row else None

    def update_wbs_element(self, wbs_element_id, updates: dict):
        """
        Updates specified fields of a WBS element.
        'updates' is a dictionary where keys are column names and values are new values.
        Uses WBSElementID from schema.sql.
        """
        if not updates:
            raise AppValidationError("No updates provided for WBS element.")

        if not isinstance(wbs_element_id, int) or wbs_element_id <= 0:
            msg = f"Invalid WBS Element ID: {wbs_element_id}. Must be a positive integer."
            logger.error(msg)
            raise AppValidationError(msg)

        existing_wbs = self.get_wbs_element_details(wbs_element_id)
        if not existing_wbs:
            msg = f"WBS Element with ID {wbs_element_id} not found."
            logger.error(msg)
            raise AppValidationError(msg) # Or AppOperationConflictError if preferred for "not found"

        validated_updates = {}
        allowed_fields = ['Description', 'EstimatedCost', 'Status', 'StartDate', 'EndDate']

        for key, value in updates.items():
            if key not in allowed_fields:
                logger.warning(f"Attempted to update disallowed or unknown field: {key} in WBS Element {wbs_element_id}")
                continue

            if key == 'EstimatedCost':
                try:
                    cost = float(value)
                    if cost < 0:
                        msg = f"Invalid EstimatedCost '{value}' for WBS {wbs_element_id}. Cannot be negative."
                        logger.error(msg)
                        raise AppValidationError(msg)
                    validated_updates[key] = cost
                except (ValueError, TypeError):
                    msg = f"Invalid EstimatedCost format '{value}' for WBS {wbs_element_id}."
                    logger.error(msg)
                    raise AppValidationError(msg)
            elif key in ['StartDate', 'EndDate']:
                if value is not None and value != "":
                    try:
                        datetime.strptime(str(value), "%Y-%m-%d")
                        validated_updates[key] = str(value)
                    except (ValueError, TypeError):
                        msg = f"Invalid {key} format '{value}' for WBS {wbs_element_id}. Use YYYY-MM-DD."
                        logger.error(msg)
                        raise AppValidationError(msg)
                else:
                    validated_updates[key] = None
            else:
                 validated_updates[key] = value

        start_date_to_check = validated_updates.get('StartDate', existing_wbs.get('StartDate'))
        end_date_to_check = validated_updates.get('EndDate', existing_wbs.get('EndDate'))

        if start_date_to_check and end_date_to_check:
            if datetime.strptime(start_date_to_check, "%Y-%m-%d") > datetime.strptime(end_date_to_check, "%Y-%m-%d"):
                msg = f"Date validation failed for WBS {wbs_element_id}: StartDate {start_date_to_check} cannot be after EndDate {end_date_to_check}."
                logger.error(msg)
                raise AppValidationError(msg)

        if not validated_updates:
            # This might mean only unknown fields were passed, or values were same as existing (if we add that check)
            return True, "No valid updates to apply to WBS Element." # Or raise AppValidationError if appropriate

        update_clauses = []
        params = []

        # Build query based on validated_updates
        for key, value in validated_updates.items():
            # Only add to query if the value is different from existing or if it's a new field being set
            # However, for simplicity and to ensure an update occurs if requested,
            # we'll update all fields present in validated_updates.
            # More sophisticated logic could check existing_wbs[key] != value
            update_clauses.append(f"{key} = ?")
            params.append(value)

        if not update_clauses:
             # This case should ideally be caught by "No valid fields provided for update or no changes detected."
             # but as a safeguard:
            return True, "No actual changes to apply to WBS Element."


        params.append(wbs_element_id) # For the WHERE clause
        query = f"UPDATE wbs_elements SET {', '.join(update_clauses)} WHERE WBSElementID = ?"

        success = self.db_manager.execute_query(query, tuple(params), commit=True)
        if success:
            logger.info(f"Successfully updated WBS Element ID {wbs_element_id} with data: {updates}")
            return True, f"WBS Element ID {wbs_element_id} updated successfully."
        else:
            logger.error(f"Failed to update WBS Element ID {wbs_element_id}.")
            return False, f"Failed to update WBS Element ID {wbs_element_id}."

    def get_budget_for_project(self, project_id):
        """Retrieves budget details for a specific project."""
        query = "SELECT * FROM project_budgets WHERE ProjectID = ?" # Corrected to ProjectID
        rows = self.db_manager.execute_query(query, (project_id,), fetch_all=True)
        return pd.DataFrame([dict(row) for row in rows]) if rows else pd.DataFrame()

    def update_project_details(self, project_id, project_name, start_date, duration_days, customer_id, project_number, project_type_id, project_status_id, calculated_end_date):
        """
        Updates details for a specific project.
        'calculated_end_date' is derived from start_date and duration_days.
        This is a placeholder and will need more robust implementation for actual updates.
        """
        # TODO: Implement full update logic, including fetching ProjectTypeID if name is given, etc.
        # For now, this is a basic structure.

        logger.info(f"Attempting to update project ID: {project_id} (Placeholder function)")

        update_query = """
        UPDATE Projects
        SET ProjectName = ?,
            StartDate = ?,
            EndDate = ?,
            DurationDays = ?,
            CustomerID = ?,
            ProjectNumber = ?,
            ProjectTypeID = ?,
            ProjectStatusID = ?,
            LastModifiedDate = CURRENT_TIMESTAMP
        WHERE ProjectID = ?
        """
        params = (
            project_name, start_date, calculated_end_date, duration_days,
            customer_id, project_number, project_type_id, project_status_id,
            project_id
        )

        success = self.db_manager.execute_query(update_query, params, commit=True)
        if success:
            logger.info(f"Project ID {project_id} placeholder update successful.")
            return True, f"Project ID {project_id} updated (placeholder)."
        else:
            logger.error(f"Failed to update project ID {project_id} (placeholder).")
            return False, f"Failed to update project ID {project_id} (placeholder)."

    def get_resources_for_project(self, project_id):
        """Retrieves resource allocations for a specific project."""
        query = "SELECT * FROM resource_allocations WHERE project_id = ?"
        rows = self.db_manager.execute_query(query, (project_id,), fetch_all=True)
        return pd.DataFrame([dict(row) for row in rows]) if rows else pd.DataFrame()

    def add_design_drawing(self, project_id, document_name, file_path, uploaded_by_employee_id, description=None):
        """
        Adds a design drawing document record to the ProjectDocuments table.
        Args:
            project_id (int): The ID of the project.
            document_name (str): The name of the document.
            file_path (str): The file path or URL of the document.
            uploaded_by_employee_id (int): The ID of the employee uploading the document.
            description (str, optional): A description for the document.
        Returns:
            tuple: (bool, str) indicating success and a message.
        """
        if not all([isinstance(project_id, int) and project_id > 0,
                    document_name and isinstance(document_name, str),
                    file_path and isinstance(file_path, str),
                    isinstance(uploaded_by_employee_id, int) and uploaded_by_employee_id > 0]):
            logger.error(f"Invalid parameters for add_design_drawing: ProjID {project_id}, DocName {document_name}, FilePath {file_path}, EmpID {uploaded_by_employee_id}")
            return None, "Invalid parameters: ProjectID/EmployeeID must be positive integers, DocumentName/FilePath must be non-empty strings."

        if description is not None and not isinstance(description, str):
            logger.error(f"Invalid description type for add_design_drawing: {type(description)}")
            return None, "Description, if provided, must be a string."

        query = """
        INSERT INTO ProjectDocuments (ProjectID, DocumentName, DocumentType, FilePath, UploadedByEmployeeID, Description, UploadDate)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (project_id, document_name, constants.DOC_TYPE_DESIGN_DRAWING, file_path, uploaded_by_employee_id, description)

        success = self.db_manager.execute_query(query, params, commit=True)
        if success:
            drawing_id = self.db_manager.execute_query("SELECT last_insert_rowid()", fetch_one=True)[0]
            logger.info(f"Design drawing '{document_name}' (ID: {drawing_id}) added for project {project_id}.")
            return drawing_id, f"Design drawing '{document_name}' added successfully."
        else:
            logger.error(f"Failed to add design drawing '{document_name}' for project {project_id}.")
            return None, f"Failed to add design drawing '{document_name}'."

    def get_design_drawings_for_project(self, project_id):
        """
        Retrieves all design drawing documents for a specific project.
        Args:
            project_id (int): The ID of the project.
        Returns:
            list: A list of dictionaries, where each dictionary represents a design drawing document.
                  Returns an empty list if no drawings are found or an error occurs.
        """
        query = """
        SELECT ProjectDocumentID, DocumentName, FilePath, UploadDate, Description
        FROM ProjectDocuments
        WHERE ProjectID = ? AND DocumentType = ?
        ORDER BY UploadDate DESC
        """
        rows = self.db_manager.execute_query(query, (project_id, constants.DOC_TYPE_DESIGN_DRAWING), fetch_all=True)
        if rows:
            return [dict(row) for row in rows]
        return []

    def get_project_documents(self, project_id):
        """
        Retrieves all documents for a given project_id.
        """
        query = """
            SELECT
                ProjectDocumentID,
                DocumentName,
                DocumentType,
                FilePath,
                UploadDate,
                Description,
                UploadedByEmployeeID
            FROM ProjectDocuments
            WHERE ProjectID = ?
            ORDER BY UploadDate DESC, DocumentName;
        """
        try:
            documents = db_manager.execute_query(query, (project_id,), fetch_all=True)
            if documents:
                return [dict(doc) for doc in documents]
            return []
        except Exception as e:
            logger.error(f"Error fetching all documents for project ID {project_id}: {e}", exc_info=True)
            return []

    def get_tasks_for_project(self, project_id):
        """
        Retrieves all tasks for a given project_id with additional details.
        Includes Lead Employee's name and Task Status name.
        """
        query = """
            SELECT
                t.TaskID,
                t.TaskName,
                t.Description,
                t.Phase,
                t.ScheduledStartDate,
                t.ScheduledEndDate,
                t.ActualStartDate,
                t.ActualEndDate,
                t.EstimatedHours,
                t.ActualHours,
                t.PercentComplete,
                t.Priority,
                t.PredecessorTaskID,
                e.FirstName || ' ' || e.LastName AS LeadEmployeeName,
                ts.StatusName,
                t.Notes
            FROM Tasks t
            LEFT JOIN Employees e ON t.LeadEmployeeID = e.EmployeeID
            LEFT JOIN TaskStatuses ts ON t.TaskStatusID = ts.TaskStatusID
            WHERE t.ProjectID = ?
            ORDER BY t.TaskID;
        """
        try:
            # Assuming db_manager is accessible as self.db_manager or globally as db_manager
            # Based on other methods, self.db_manager is not consistently used for db_manager access.
            # The class definition shows self.db_manager = db_manager, but methods like
            # get_project_details use db_manager directly.
            # The prompt's method uses 'db_manager.' which implies it's an imported module instance.
            # The file already imports 'from database_manager import db_manager', so 'db_manager.execute_query' is correct.
            tasks = db_manager.execute_query(query, (project_id,), fetch_all=True)
            if tasks:
                # Convert Row objects to dictionaries for easier frontend use
                return [dict(task) for task in tasks]
            return []
        except Exception as e:
            logger.error(f"Error fetching tasks for project ID {project_id}: {e}", exc_info=True)
            return []

    def manage_material(self, details_dict, material_system_id=None):
        """
        Creates a new material (Item Master) or updates an existing one.
        'details_dict' should contain all necessary fields from the UI.
        If 'material_system_id' is provided, it's an update, otherwise an insert.
        Returns (new_or_updated_id, message).
        """
        required_fields = ['StockNumber', 'MaterialName', 'UnitOfMeasure', 'DefaultCost']
        for field in required_fields:
            if not details_dict.get(field):
                return None, f"Missing required field: {field}"

        # Convert numeric fields and handle potential errors
        try:
            details_dict['DefaultCost'] = float(details_dict['DefaultCost']) if details_dict.get('DefaultCost') else 0.0
            details_dict['DefaultPrice'] = float(details_dict['DefaultPrice']) if details_dict.get('DefaultPrice') else None
            details_dict['PreferredVendorID'] = int(details_dict['PreferredVendorID']) if details_dict.get('PreferredVendorID') else None
            details_dict['ReorderPoint'] = float(details_dict['ReorderPoint']) if details_dict.get('ReorderPoint') else None
            details_dict['Labor1'] = float(details_dict.get('Labor1')) if details_dict.get('Labor1') else None
            details_dict['Labor2'] = float(details_dict.get('Labor2')) if details_dict.get('Labor2') else None
            details_dict['Labor3'] = float(details_dict.get('Labor3')) if details_dict.get('Labor3') else None
            # QuantityOnHand is typically managed by transactions, not direct edit here.
        except ValueError as e:
            logger.error(f"Invalid numeric value in material details: {e}")
            return None, f"Invalid numeric value provided for cost, price, vendor ID, reorder point, or labor."

        # Ensure StockNumber is unique if it's a new material or if it's being changed for an existing one.
        check_stock_query = "SELECT MaterialSystemID FROM Materials WHERE StockNumber = ? AND (? IS NULL OR MaterialSystemID != ?)"
        existing_stock = db_manager.execute_query(check_stock_query, (details_dict['StockNumber'], material_system_id, material_system_id), fetch_one=True)
        if existing_stock:
            return None, f"Stock Number '{details_dict['StockNumber']}' already exists for another material."

        if material_system_id: # Update existing material
            # Check if the material_system_id exists
            check_id_query = "SELECT MaterialSystemID FROM Materials WHERE MaterialSystemID = ?"
            if not db_manager.execute_query(check_id_query, (material_system_id,), fetch_one=True):
                return None, f"Material with System ID {material_system_id} not found for update."

            sql = """
                UPDATE Materials SET
                    StockNumber = ?, MaterialName = ?, Category = ?, ExtendedDescription = ?, Barcode = ?,
                    UnitOfMeasure = ?, ManufacturerPartNumber = ?, DefaultCost = ?, DefaultPrice = ?,
                    PreferredVendorID = ?, Manufacturer = ?, ReorderPoint = ?, SalesTaxCode = ?,
                    SubCategory = ?, Labor1 = ?, Labor2 = ?, Labor3 = ?, UpdatedAt = CURRENT_TIMESTAMP
                WHERE MaterialSystemID = ?;
            """
            params = (
                details_dict.get('StockNumber'), details_dict.get('MaterialName'), details_dict.get('Category'),
                details_dict.get('ExtendedDescription'), details_dict.get('Barcode'), details_dict.get('UnitOfMeasure'),
                details_dict.get('ManufacturerPartNumber'), details_dict.get('DefaultCost'), details_dict.get('DefaultPrice'),
                details_dict.get('PreferredVendorID'), details_dict.get('Manufacturer'), details_dict.get('ReorderPoint'),
                details_dict.get('SalesTaxCode'), details_dict.get('SubCategory'),
                details_dict.get('Labor1'), details_dict.get('Labor2'), details_dict.get('Labor3'),
                material_system_id
            )
            action = "updated"
        else: # Insert new material
            sql = """
                INSERT INTO Materials (
                    StockNumber, MaterialName, Category, ExtendedDescription, Barcode, UnitOfMeasure,
                    ManufacturerPartNumber, DefaultCost, DefaultPrice, PreferredVendorID, Manufacturer,
                    ReorderPoint, SalesTaxCode, SubCategory, Labor1, Labor2, Labor3
                    -- QuantityOnHand defaults to 0 or is handled by other processes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            params = (
                details_dict.get('StockNumber'), details_dict.get('MaterialName'), details_dict.get('Category'),
                details_dict.get('ExtendedDescription'), details_dict.get('Barcode'), details_dict.get('UnitOfMeasure'),
                details_dict.get('ManufacturerPartNumber'), details_dict.get('DefaultCost'), details_dict.get('DefaultPrice'),
                details_dict.get('PreferredVendorID'), details_dict.get('Manufacturer'), details_dict.get('ReorderPoint'),
                details_dict.get('SalesTaxCode'), details_dict.get('SubCategory'),
                details_dict.get('Labor1'), details_dict.get('Labor2'), details_dict.get('Labor3')
            )
            action = "created"

        try:
            cursor = self.db_manager.get_connection().cursor()
            cursor.execute(sql, params)
            self.db_manager.get_connection().commit()
            last_row_id = cursor.lastrowid if not material_system_id else material_system_id

            if last_row_id:
                logger.info(f"Material '{details_dict.get('StockNumber')}' (ID: {last_row_id}) {action} successfully.")
                return last_row_id, f"Material '{details_dict.get('StockNumber')}' {action} successfully. ID: {last_row_id}"
            else:
                logger.error(f"Failed to {action} material '{details_dict.get('StockNumber')}'. No ID returned or error in execution.")
                return None, f"Failed to {action} material '{details_dict.get('StockNumber')}'."
        except Exception as e:
            logger.error(f"Database error during material {action} for '{details_dict.get('StockNumber')}': {e}", exc_info=True)
            return None, f"Database error: Could not {action} material. Check logs."

    def get_material_details_by_stock_number(self, stock_number):
        """
        Retrieves all details for a material item by its StockNumber.
        Returns a dictionary of the material's details or None if not found.
        """
        query = "SELECT * FROM Materials WHERE StockNumber = ?;"
        try:
            material_row = db_manager.execute_query(query, (stock_number,), fetch_one=True)
            if material_row:
                return dict(material_row)  # Convert sqlite3.Row to dict
            return None
        except Exception as e:
            logger.error(f"Error fetching material details for StockNumber {stock_number}: {e}", exc_info=True)
            return None

    def manage_assembly(self, assembly_details, components_list, assembly_id=None):
        """
        Creates a new assembly or updates an existing one, including its components.
        'assembly_details' is a dict with AssemblyItemNumber, AssemblyName, Description, Phase.
        'components_list' is a list of dicts, each with MaterialStockNumber, QuantityInAssembly, UnitOfMeasure.
        If 'assembly_id' is provided, it's an update.
        Returns (new_or_updated_assembly_id, message).
        """
        validation_passed, validation_msg = self._validate_assembly_inputs(
            assembly_details, components_list, assembly_id
        )
        if not validation_passed:
            return None, validation_msg

        conn = None
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            if assembly_id: # Update
                # Check if assembly_id exists
                cursor.execute("SELECT AssemblyID FROM Assemblies WHERE AssemblyID = ?", (assembly_id,))
                if not cursor.fetchone():
                    return None, f"Assembly with ID {assembly_id} not found for update."

                cursor.execute("""
                    UPDATE Assemblies SET AssemblyItemNumber = ?, AssemblyName = ?, Description = ?, Phase = ?, UpdatedAt = CURRENT_TIMESTAMP
                    WHERE AssemblyID = ?;
                """, (
                    assembly_details.get('AssemblyItemNumber'), assembly_details.get('AssemblyName'),
                    assembly_details.get('Description'), assembly_details.get('Phase'), assembly_id
                ))
                action = "updated"
                current_assembly_id = assembly_id

                # Delete existing components for this assembly before re-adding
                cursor.execute("DELETE FROM AssemblyComponents WHERE AssemblyID = ?", (assembly_id,))
                logger.info(f"Deleted existing components for AssemblyID {assembly_id} before update.")

            else: # Insert new assembly
                cursor.execute("""
                    INSERT INTO Assemblies (AssemblyItemNumber, AssemblyName, Description, Phase)
                    VALUES (?, ?, ?, ?);
                """, (
                    assembly_details.get('AssemblyItemNumber'), assembly_details.get('AssemblyName'),
                    assembly_details.get('Description'), assembly_details.get('Phase')
                ))
                current_assembly_id = cursor.lastrowid
                if not current_assembly_id: # Should not happen with autoincrement PK
                    conn.rollback()
                    logger.error("Failed to get lastrowid for new assembly.")
                    return None, "Failed to create new assembly (no ID returned)."
                action = "created"

            # Add/Update components
            # First, ensure all referenced MaterialStockNumbers exist.
            for comp in components_list:
                cursor.execute("SELECT MaterialSystemID FROM Materials WHERE StockNumber = ?", (comp['MaterialStockNumber'],))
                material_exists = cursor.fetchone()
                if not material_exists:
                    conn.rollback()
                    return None, f"Material with Stock Number '{comp['MaterialStockNumber']}' not found. Cannot add to assembly."

            # Now insert the components
            for comp in components_list:
                cursor.execute("""
                    INSERT INTO AssemblyComponents (AssemblyID, MaterialStockNumber, QuantityInAssembly, UnitOfMeasure)
                    VALUES (?, ?, ?, ?);
                """, (
                    current_assembly_id, comp['MaterialStockNumber'],
                    comp['QuantityInAssembly'], comp.get('UnitOfMeasure')
                ))

            conn.commit()
            logger.info(f"Assembly '{assembly_details.get('AssemblyName')}' (ID: {current_assembly_id}) and its components {action} successfully.")
            return current_assembly_id, f"Assembly '{assembly_details.get('AssemblyName')}' and its {len(components_list)} component types {action} successfully. ID: {current_assembly_id}"

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error during assembly management for '{assembly_details.get('AssemblyName')}': {e}", exc_info=True)
            return None, f"Database error: Could not manage assembly. Details: {e}"
        finally:
            # Note: The db_manager in the provided snippet doesn't have release_connection.
            # The existing db_manager.close_connection() closes the global connection.
            # For explicit transaction control with get_connection(), we usually pair it with releasing/closing
            # that specific connection instance if get_connection() were to provide new ones.
            # However, this db_manager uses a single shared connection.
            # So, we don't call db_manager.release_connection(conn) or conn.close() here,
            # as it might affect other parts of the application using the shared conn.
            # The commit/rollback is sufficient for transaction management on the shared connection.
            pass

    def _validate_assembly_inputs(self, assembly_details, components_list, assembly_id=None):
        """Helper to validate inputs for manage_assembly."""
        required_asm_fields = ['AssemblyItemNumber', 'AssemblyName']
        for field in required_asm_fields:
            if not assembly_details.get(field) or not isinstance(assembly_details.get(field), str):
                return False, f"Missing or invalid assembly field: {field}. Must be a non-empty string."

        if not isinstance(components_list, list):
            return False, "Components list must be a list."
        if not components_list: # Allowing empty components list for an assembly initially.
             pass # Or: return False, "Components list cannot be empty."

        for i, comp in enumerate(components_list):
            if not isinstance(comp, dict):
                return False, f"Component at index {i} is not a valid dictionary."
            if not comp.get('MaterialStockNumber') or not isinstance(comp.get('MaterialStockNumber'), str):
                return False, f"Component {i}: MaterialStockNumber is required and must be a string."
            if comp.get('QuantityInAssembly') is None: # Check for None explicitly
                 return False, f"Component {i}: QuantityInAssembly is required."
            try:
                qty = float(comp['QuantityInAssembly'])
                if qty <= 0:
                    return False, f"Component {i}: QuantityInAssembly must be positive."
                comp['QuantityInAssembly'] = qty # Ensure it's float after validation
            except (ValueError, TypeError):
                return False, f"Component {i}: Invalid QuantityInAssembly. Must be a number."

            if comp.get('UnitOfMeasure') is not None and not isinstance(comp.get('UnitOfMeasure'), str):
                 return False, f"Component {i}: UnitOfMeasure, if provided, must be a string."


        # Check for unique AssemblyItemNumber if creating new or changing it
        # This check needs db_manager, so it's part of the main method's transaction or pre-check.
        # For simplicity, keeping it in the main method before transaction starts.
        # However, if we want this helper to be fully comprehensive for *all* input validation:
        if assembly_details.get('AssemblyItemNumber'):
            check_item_num_query = "SELECT AssemblyID FROM Assemblies WHERE AssemblyItemNumber = ? AND (? IS NULL OR AssemblyID != ?)"
            existing_assembly_item_num = db_manager.execute_query(
                check_item_num_query,
                (assembly_details['AssemblyItemNumber'], assembly_id, assembly_id),
                fetch_one=True
            )
            if existing_assembly_item_num:
                return False, f"Assembly Item Number '{assembly_details['AssemblyItemNumber']}' already exists."

        return True, "Validation successful."

    def get_assembly_details_by_item_number(self, assembly_item_number):
        """
        Retrieves assembly details and its components by AssemblyItemNumber.
        Returns (assembly_data_dict, components_list_of_dicts) or (None, None).
        """
        assembly_query = "SELECT * FROM Assemblies WHERE AssemblyItemNumber = ?;"
        components_query = """
            SELECT ac.MaterialStockNumber, m.MaterialName, ac.QuantityInAssembly, ac.UnitOfMeasure
            FROM AssemblyComponents ac
            JOIN Materials m ON ac.MaterialStockNumber = m.StockNumber
            WHERE ac.AssemblyID = ?;
        """
        try:
            assembly_data = db_manager.execute_query(assembly_query, (assembly_item_number,), fetch_one=True)
            if not assembly_data:
                return None, None

            assembly_dict = dict(assembly_data)
            assembly_id = assembly_dict['AssemblyID']

            components_data = db_manager.execute_query(components_query, (assembly_id,), fetch_all=True)
            components_list = [dict(comp) for comp in components_data] if components_data else []

            return assembly_dict, components_list
        except Exception as e:
            logger.error(f"Error fetching assembly details for ItemNumber {assembly_item_number}: {e}", exc_info=True)
            return None, None

    def add_material_request(self, project_id: int, requested_by_employee_id: int, material_description: str,
                             quantity_requested: float, unit_of_measure: str, urgency_level: str = None,
                             required_by_date: str = None, notes: str = None):
        """
        Adds a new material request to the Purchasing_Log table.
        Returns:
            tuple: (bool, str, int or None) indicating success, a message, and the new InternalLogID.
        """
        logger.info(f"Adding material request: ProjectID={project_id}, EmpID={requested_by_employee_id}, Desc='{material_description[:50]}...'")

        if not all([requested_by_employee_id, material_description, quantity_requested]):
            logger.error("Missing required fields for material request (EmployeeID, Description, Quantity).")
            return False, "Missing required fields for material request.", None

        query = """
        INSERT INTO Purchasing_Log (
            ProjectID, RequestedByEmployeeID, MaterialDescription, QuantityRequested,
            UnitOfMeasure, UrgencyLevel, RequiredByDate, Notes, Status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            project_id, requested_by_employee_id, material_description, quantity_requested,
            unit_of_measure, urgency_level, required_by_date, notes, constants.PURCHASE_STATUS_REQUESTED
        )

        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            last_row_id = cursor.lastrowid
            conn.commit()

            if last_row_id:
                logger.info(f"Material request logged successfully. InternalLogID: {last_row_id}")
                return True, "Material request logged successfully.", last_row_id
            else:
                logger.error("Failed to log material request (no ID returned), though query might have succeeded.")
                return False, "Failed to log material request (no ID returned).", None
        except Exception as e:
            logger.error(f"Database error adding material request: {e}", exc_info=True)
            return False, f"Database error adding material request: {e}", None

    def create_production_assembly_order(self, assembly_id: int, project_id: int, quantity_to_produce: float,
                                         assigned_to_employee_id: int = None, start_date: str = None,
                                         completion_date: str = None, notes: str = None):
        """
        Creates a new production order for an assembly in the Production_Assembly_Tracking table.
        Returns:
            tuple: (bool, str, int or None) indicating success, a message, and the new ProductionID.
        """
        logger.info(f"Creating production order: AssemblyID={assembly_id}, ProjectID={project_id}, Qty={quantity_to_produce}")

        if not all([assembly_id, quantity_to_produce]):
            logger.error("Missing required fields for production order (AssemblyID, QuantityToProduce).")
            return False, "Missing required fields for production order.", None

        if quantity_to_produce <= 0:
            logger.error(f"Quantity to produce must be positive. Received: {quantity_to_produce}")
            return False, "Quantity to produce must be positive.", None

        query = """
        INSERT INTO Production_Assembly_Tracking (
            AssemblyID, ProjectID, QuantityToProduce, AssignedToEmployeeID,
            StartDate, CompletionDate, Notes, Status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            assembly_id, project_id, quantity_to_produce, assigned_to_employee_id,
            start_date, completion_date, notes, constants.PRODUCTION_STATUS_PLANNED
        )

        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            last_row_id = cursor.lastrowid
            conn.commit()

            if last_row_id:
                logger.info(f"Production order created successfully. ProductionID: {last_row_id}")
                return True, "Production order created successfully.", last_row_id
            else:
                logger.error("Failed to create production order (no ID returned).")
                return False, "Failed to create production order (no ID returned).", None
        except Exception as e:
            logger.error(f"Database error creating production order: {e}", exc_info=True)
            return False, f"Database error creating production order: {e}", None

    def add_document_note(self, document_id, page_number, employee_id, note_text):
        """Adds a note to a document page."""
        if not (isinstance(document_id, int) and document_id > 0):
            return False, "Invalid Document ID."
        if not (isinstance(page_number, int) and page_number > 0): # Assuming page numbers are positive
            return False, "Invalid Page Number."
        if not (isinstance(employee_id, int) and employee_id > 0):
            return False, "Invalid Employee ID."
        if not note_text or not isinstance(note_text, str):
            return False, "Note text cannot be empty."

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        INSERT INTO document_notes (document_id, page_number, employee_id, note_text, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (document_id, page_number, employee_id, note_text, created_at)

        try:
            success = self.db_manager.execute_query(query, params, commit=True)
            if success and success.lastrowid: # Check for truthy cursor and lastrowid for sqlite
                logger.info(f"Note added (ID: {success.lastrowid}) for document ID {document_id}, page {page_number} by employee {employee_id}.")
                return True, "Note added successfully."
            elif success: # Fallback if lastrowid is not available but query succeeded
                logger.info(f"Note added for document ID {document_id}, page {page_number} by employee {employee_id} (no lastrowid).")
                return True, "Note added successfully (no ID)."
            else:
                logger.error(f"Failed to add note for document ID {document_id}, page {page_number}. execute_query returned: {success}")
                return False, "Failed to add note to the database."
        except Exception as e:
            logger.error(f"Exception adding note for document ID {document_id}, page {page_number}: {e}", exc_info=True)
            return False, f"Failed to add note due to an error: {e}"


    def get_document_notes(self, document_id):
        """Retrieves notes for a specific document, joined with employee names."""
        query = """
            SELECT dn.page_number, e.FirstName, e.LastName, dn.note_text, dn.created_at
            FROM document_notes dn
            JOIN Employees e ON dn.employee_id = e.EmployeeID
            WHERE dn.document_id = ?
            ORDER BY dn.page_number, dn.created_at
        """
        notes = self.db_manager.execute_query(query, (document_id,), fetch_all=True)
        if notes:
            return [dict(note) for note in notes]
        return []

    def get_pending_material_requests(self):
        """Retrieves pending material requests from Purchasing_Log."""
        query = """
        SELECT InternalLogID, ProjectID, MaterialDescription, QuantityRequested, UnitOfMeasure,
               UrgencyLevel, RequiredByDate, Status, DateCreated
        FROM Purchasing_Log
        WHERE Status NOT IN (?, ?)
        ORDER BY DateCreated DESC
        """
        params = (constants.PURCHASE_STATUS_RECEIVED_FULL, constants.PURCHASE_STATUS_CANCELLED)
        try:
            requests = self.db_manager.execute_query(query, params, fetch_all=True)
            if requests:
                return [dict(req) for req in requests]
            return []
        except Exception as e:
            logger.error(f"Error fetching pending material requests: {e}", exc_info=True)
            return []

    def get_active_production_orders(self):
        """Retrieves active production orders from Production_Assembly_Tracking."""
        query = """
        SELECT ProductionID, AssemblyID, ProjectID, QuantityToProduce, Status,
               StartDate, CompletionDate, AssignedToEmployeeID, DateCreated
        FROM Production_Assembly_Tracking
        WHERE Status NOT IN (?, ?, ?)
        ORDER BY DateCreated DESC
        """
        params = (constants.PRODUCTION_STATUS_COMPLETED, constants.PRODUCTION_STATUS_SHIPPED, constants.PRODUCTION_STATUS_CANCELLED)
        try:
            orders = self.db_manager.execute_query(query, params, fetch_all=True)
            if orders:
                return [dict(order) for order in orders]
            return []
        except Exception as e:
            logger.error(f"Error fetching active production orders: {e}", exc_info=True)
            return []


if __name__ == "__main__":
    # This block demonstrates how the ProjectPlanning module can be used.

    print("--- Testing Project Planning Module ---")

    # Ensure a clean database for testing the full flow
    import os
    from integration import Integration
    from data_processing import DataProcessing
    from database_manager import DatabaseManager

    test_db_path = Config.get_database_path()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Cleaned up existing database at: {test_db_path}")

    # Initialize DatabaseManager (singleton)
    _ = DatabaseManager()

    # --- Phase 1: Simulate Data Ingestion and Processing ---
    # 1. Create a sample CSV file for Integration
    sample_csv_path = os.path.join(Config.get_data_dir(), 'sample_estimate_for_planning.csv')
    sample_data = {
        'Cost Code': ['01-010', '01-020', '02-100', '03-200', '03-210', '03-210', '04-300'],
        'Description': ['Mobilization', 'PM', 'Site Prep', 'Conc Foot', 'Conc Slab', 'Conc Slab', 'Framing'],
        'Quantity': [1.0, 40.0, 500.0, 15.0, 200.0, 200.0, 100.0],
        'Unit': ['LS', 'HR', 'SY', 'CY', 'SF', 'SF', 'LF'],
        'Unit Cost': [5000.00, 75.00, 15.00, 300.00, 5.00, 5.00, 10.00],
        'Total Cost': [5000.00, 3000.00, 7500.00, 4500.00, 1000.00, 1000.00, 1000.00],
        'Phase': ['Pre-Construction', 'Pre-Construction', 'Foundation', 'Foundation', 'Foundation', 'Foundation', 'Structure']
    }
    sample_df = pd.DataFrame(sample_data)
    sample_df.to_csv(sample_csv_path, index=False)
    print(f"\nSample CSV for planning created at: {sample_csv_path}")

    # 2. Ingest raw data
    integration_module = Integration()
    ingest_success, ingest_message = integration_module.import_estimate_from_csv(sample_csv_path)
    print(f"Raw data ingestion result: {ingest_message}")

    # 3. Process raw data
    data_processor = DataProcessing()
    process_success, process_message = data_processor.process_estimate_data()
    print(f"Data processing result: {process_message}")
    if not process_success:
        print("Data processing failed, cannot proceed with planning.")
        exit()

    # --- Phase 2: Project Startup & Planning ---
    project_startup_module = ProjectStartup()

    # 1. Create a new project
    # For the test, provide a dummy duration_days. End date is also passed directly.
    # In real usage, UI calculates end_date and then calls create_project.
    dummy_start_date = "2025-07-01"
    dummy_duration = 10 # days
    # Let's assume a simple end date for this test, actual calculation will be in UI layer.
    # Or, we can call the util function here for testing the flow.
    # from utils import calculate_end_date
    # dummy_end_date_calculated = calculate_end_date(dummy_start_date, dummy_duration)
    # For simplicity in this block, just using a fixed offset. Real calc is UI's job before calling backend.

    # The create_project now expects: name, start_date, end_date (calculated), duration_days
    # The __main__ block is for simple module testing, not full UI workflow.
    # Let's assume end_date here is pre-calculated for the sake of this test script.
    test_end_date = "2025-07-12" # Example, assumes it's calculated

    project_id, project_msg = project_startup_module.create_project(
        "Office Building Phase 1",
        dummy_start_date,
        test_end_date,  # This should be the calculated end date
        dummy_duration
    )
    print(f"\nProject Creation: {project_msg}")

    if project_id:
        # 2. Generate WBS from estimates
        wbs_success, wbs_msg = project_startup_module.generate_wbs_from_estimates(project_id)
        print(f"WBS Generation: {wbs_msg}")

        # Verify WBS elements
        print("\n--- WBS Elements for Project ---")
        wbs_df = project_startup_module.get_wbs_for_project(project_id)
        if not wbs_df.empty:
            print(f"Number of WBS elements: {len(wbs_df)}")
            print(wbs_df[['wbs_code', 'description', 'estimated_cost']].head(10))
        else:
            print("No WBS elements generated.")

        # Verify processed_estimates are linked
        print("\n--- Processed Estimates linked to Project ---")
        linked_estimates_query = "SELECT id, cost_code, description, project_id, wbs_element_id FROM processed_estimates WHERE project_id = ?"
        linked_estimates = db_manager.execute_query(linked_estimates_query, (project_id,), fetch_all=True)
        if linked_estimates:
            print(f"Number of processed estimates linked: {len(linked_estimates)}")
            for est in linked_estimates[:5]: # Print first 5
                print(f"ID: {est['id']}, Cost Code: {est['cost_code']}, Project ID: {est['project_id']}, WBS ID: {est['wbs_element_id']}")
        else:
            print("No processed estimates linked to the project.")


        # 3. Generate Project Budget
        budget_success, budget_msg = project_startup_module.generate_project_budget(project_id)
        print(f"\nBudget Generation: {budget_msg}")

        # Verify Budget
        print("\n--- Project Budget ---")
        budget_df = project_startup_module.get_budget_for_project(project_id)
        if not budget_df.empty:
            print(f"Number of budget items: {len(budget_df)}")
            print(budget_df[['budget_category', 'estimated_amount']].head())
        else:
            print("No budget items generated.")

        # 4. Allocate Resources
        resources_success, resources_msg = project_startup_module.allocate_resources(project_id)
        print(f"\nResource Allocation: {resources_msg}")

        # Verify Resources
        print("\n--- Resource Allocations ---")
        resources_df = project_startup_module.get_resources_for_project(project_id)
        if not resources_df.empty:
            print(f"Number of resource allocations: {len(resources_df)}")
            print(resources_df[['resource_name', 'resource_type', 'allocated_quantity', 'unit', 'allocated_cost']].head())
        else:
            print("No resources allocated.")

        # Get and display final project details
        project_details = project_startup_module.get_project_details(project_id)
        if project_details:
            print("\n--- Final Project Details (from schema.sql structure) ---")
            print(f"Project Name: {project_details['ProjectName']}")
            print(f"Start Date: {project_details['StartDate']}")
            print(f"End Date: {project_details['EndDate']}")
            print(f"Duration Days: {project_details['DurationDays']}")
            print(f"Status: {project_details['StatusName']}")
            print(f"Estimated Cost: {project_details['EstimatedCost']:.2f}")

    # Clean up test files and database
    if os.path.exists(sample_csv_path):
        os.remove(sample_csv_path)
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"\nCleaned up test database and sample CSV.")