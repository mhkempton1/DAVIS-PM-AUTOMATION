import pandas as pd
import numpy as np
import logging
import re
import json # Added for LLM parsing
from datetime import datetime # Added for daily log date fallback
# import sqlite3 # No longer needed as db_manager handles sqlite3.Error
from database_manager import db_manager # Import the singleton database manager
from configuration import Config

import sqlite3 # Import for exception handling

# Get logger instance, rather than basicConfig here as it's likely configured in main.py or db_manager
logger = logging.getLogger(__name__)

class DataProcessing:
    """
    Cleans, validates, and transforms raw estimate data into a standardized format
    for subsequent project planning and management.
    Also handles parsing of unstructured data like daily logs.
    """
    def __init__(self, db_m_instance=None): # Accept optional db_manager
        """
        Initializes the DataProcessing module.
        """
        self.db_manager = db_m_instance if db_m_instance else db_manager # Use passed or global
        logger.info("Data Processing module initialized.")

    def _call_llm_for_parsing(self, text_input: str, schema_hint: str = None):
        """
        Placeholder method to simulate calling an LLM for parsing text.
        In a real scenario, this would involve API calls to an LLM service.
        Args:
            text_input: The raw text to be parsed.
            schema_hint: Optional hint about the expected structure or type of data.
        Returns:
            A tuple containing the parsed JSON string and a confidence score.
        """
        logger.info(f"Simulating LLM call for text: '{text_input[:100]}...' with schema hint: {schema_hint}")
        # Dummy response for now
        dummy_json = json.dumps({
            "parsed_field_1": "LLM_parsed_value1",
            "parsed_field_2": "LLM_parsed_value2",
            "original_text_snippet": text_input[:50] # Include a snippet for reference
        })
        confidence_score = 0.95
        logger.info(f"LLM simulation returned JSON: {dummy_json}, Confidence: {confidence_score}")
        return dummy_json, confidence_score

    def _get_raw_estimates_df(self):
        """
        Retrieves raw estimate data from the database into a pandas DataFrame.
        Returns an empty DataFrame if no data or an error occurs.
        """
        # Fetch only raw estimates that haven't been processed or are marked for reprocessing.
        query = "SELECT RawEstimateID, RawData, ProjectID FROM raw_estimates WHERE Status = 'Pending Processing' OR Status = 'Pending' ORDER BY RawEstimateID ASC"
        rows = self.db_manager.execute_query(query, fetch_all=True)

        if rows is None: # Indicates a DB error from execute_query returning False
            logger.error("Failed to retrieve raw estimates due to a database error (execute_query returned None/False).")
            return pd.DataFrame()
        if not rows: # No data matching criteria
            logger.info("No 'Pending Processing' or 'Pending' raw estimate data found in the database.")
            return pd.DataFrame()

        parsed_data_list = []
        import json
        for row in rows:
            try:
                raw_data_dict = json.loads(row['RawData'])
                # Add RawEstimateID and ProjectID from the parent table for traceability and potential use
                raw_data_dict['RawEstimateID'] = row['RawEstimateID']
                # Preserve original ProjectID if it was linked at import, though processing typically links later.
                raw_data_dict['OriginalProjectID'] = row['ProjectID']
                parsed_data_list.append(raw_data_dict)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for RawEstimateID {row['RawEstimateID']}: {e}. RawData: {row['RawData'][:200]}")
            except Exception as e:
                logger.exception(f"Unexpected error processing row for RawEstimateID {row['RawEstimateID']}: {e}")

        if not parsed_data_list:
            logger.info("No raw data could be successfully parsed from JSON. DataFrame will be empty.")
            return pd.DataFrame()

        return pd.DataFrame(parsed_data_list)


    def process_estimate_data(self):
        """
        Main method to orchestrate the data cleaning, validation, and transformation.
        Reads from raw_estimates, processes, and writes to processed_estimates.
        Returns:
            tuple: (bool, str) indicating success and a message.
        """
        logger.info("Starting data processing for raw estimates...")
        raw_df = self._get_raw_estimates_df() # This now returns a DataFrame of parsed JSON objects

        if raw_df.empty:
            return False, "No raw estimate data to process or error retrieving/parsing data."

        logger.info(f"Retrieved and parsed {len(raw_df)} raw estimate records for processing.")

        processed_df = raw_df.copy()

        # Store RawEstimateIDs for updating status later
        raw_estimate_ids_processed = processed_df['RawEstimateID'].tolist()


        # Step 1: Standardization of Column Names using Config.ESTIMATE_COLUMN_MAPPING
        # Config.ESTIMATE_COLUMN_MAPPING maps from CSV header to desired internal name (e.g., 'Cost Code' -> 'cost_code')
        # The raw_df from _get_raw_estimates_df now has original CSV headers as keys from JSON parsing.

        # Filter mapping to only include columns present in the DataFrame
        # to avoid KeyErrors if a mapped column isn't in every JSON object.
        current_columns = set(processed_df.columns)
        applicable_mapping = {
            csv_header: internal_name
            for csv_header, internal_name in Config.ESTIMATE_COLUMN_MAPPING.items()
            if csv_header in current_columns
        }
        processed_df.rename(columns=applicable_mapping, inplace=True)
        logger.info(f"Applied column mapping. Renamed columns: {applicable_mapping}")


        # Ensure numeric types and handle non-numeric values
        # Target columns for processed_estimates are 'quantity', 'unit_cost', 'total_cost'
        numeric_cols = ['quantity', 'unit_cost', 'total_cost']
        for col in numeric_cols:
            if col in processed_df.columns:
                original_nan_count = processed_df[col].isnull().sum()
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
                coerced_nan_count = processed_df[col].isnull().sum()
                if coerced_nan_count > original_nan_count:
                     logger.warning(f"Non-numeric values found and coerced to NaN in column: '{col}'. These will be filled with 0.")
                processed_df[col] = processed_df[col].fillna(0.0) # Use 0.0 for float columns
            else:
                logger.warning(f"Numeric column '{col}' not found in DataFrame. Adding with default 0.0.")
                processed_df[col] = 0.0

        # Fill missing string values with 'N/A' or ensure they are strings
        string_cols = ['cost_code', 'description', 'unit', 'phase']
        for col in string_cols:
            if col in processed_df.columns:
                processed_df[col] = processed_df[col].fillna('N/A').astype(str).str.strip() # Apply .str accessor
            else:
                logger.warning(f"String column '{col}' not found in DataFrame. Adding with default 'N/A'.")
                processed_df[col] = 'N/A'

        # Step 2: Data Validation and Correction
        if 'quantity' in processed_df.columns and 'unit_cost' in processed_df.columns and 'total_cost' in processed_df.columns:
            calculated_total_cost = processed_df['quantity'] * processed_df['unit_cost']
            tolerance = 0.01
            # Use np.isclose for robust floating-point comparison, ensure Series have same index
            # If lengths are different due to prior processing, this could fail.
            # However, operations so far should maintain df integrity.
            if len(processed_df['total_cost']) == len(calculated_total_cost):
                discrepancy_mask = ~np.isclose(processed_df['total_cost'].values, calculated_total_cost.values, rtol=0, atol=tolerance)
                if np.any(discrepancy_mask): # Check if any True values in mask
                    logger.warning(f"Found {np.sum(discrepancy_mask)} discrepancies in 'total_cost' calculation. Correcting them.")
                    processed_df.loc[discrepancy_mask, 'total_cost'] = calculated_total_cost[discrepancy_mask]
            else:
                logger.error("Length mismatch between total_cost and calculated_total_cost. Skipping correction.")


        # Step 3: Remove Duplicates
        # Define subset for identifying duplicates more carefully
        duplicate_subset = ['cost_code', 'description', 'quantity', 'unit', 'unit_cost', 'phase']
        # Ensure all subset columns exist before dropping duplicates
        existing_duplicate_subset = [col for col in duplicate_subset if col in processed_df.columns]
        if len(existing_duplicate_subset) > 0: # Only drop if some identifying columns exist
            initial_rows = len(processed_df)
            processed_df.drop_duplicates(subset=existing_duplicate_subset, inplace=True, keep='first')
            if len(processed_df) < initial_rows:
                logger.info(f"Removed {initial_rows - len(processed_df)} duplicate rows based on subset: {existing_duplicate_subset}.")
        else:
            logger.warning("Not enough identifying columns to perform duplicate check. Skipping.")


        # Select and reorder final columns for processed_estimates table
        # 'RawEstimateID' is carried from the parsed raw_df for linking.
        # 'project_id' is initially None; will be linked by ProjectStartup.generate_wbs_from_estimates
        final_cols_ordered = [
            'RawEstimateID', 'cost_code', 'description', 'quantity', 'unit',
            'unit_cost', 'total_cost', 'phase', 'project_id'
        ]

        # Add 'project_id' placeholder if not already present from CSV (unlikely for this field)
        if 'project_id' not in processed_df.columns:
            processed_df['project_id'] = None

        # Ensure RawEstimateID is present (it should be from _get_raw_estimates_df)
        if 'RawEstimateID' not in processed_df.columns:
            logger.error("'RawEstimateID' column is missing from the DataFrame before final selection. This should not happen.")
            # Fallback: try to assign a dummy or skip, but this indicates a flaw in data propagation
            # For now, let's assume it's there. If not, saving will fail or be incorrect.
            # Or, we could try to re-attach it if raw_estimate_ids_processed aligns row-wise, but that's risky.
            # Best to ensure it's always carried.

        # Ensure all final columns exist, add if missing.
        for col in final_cols_ordered:
            if col not in processed_df.columns:
                logger.warning(f"Final column '{col}' was missing from processed_df. Adding with default values.")
                if col in numeric_cols:
                    processed_df[col] = 0.0
                elif col == 'RawEstimateID': # Should not happen if logic is correct
                    processed_df[col] = None # Or some other placeholder, though this is problematic
                else:
                    processed_df[col] = 'N/A' if col in string_cols else None

        # Select only the final columns in the specified order
        processed_df_final = processed_df[final_cols_ordered]

        # Step 4: Write processed data to the 'processed_estimates' table
        # Pass the original RawEstimateIDs to update their status after successful save
        return self._save_processed_data(processed_df_final, raw_estimate_ids_processed)

    def _save_processed_data(self, df_to_save, raw_estimate_ids_to_update):
        """
        Saves the processed DataFrame to the 'processed_estimates' table in the database.
        Updates the status of corresponding raw_estimates upon successful save.
        """
        if df_to_save.empty:
            logger.info("No processed data to save.")
            return True, "No processed data to save."

        # Configuration for clearing table can be added here if needed
        # For now, let's assume we want to append or manage updates carefully.
        # The previous logic deleted all from processed_estimates. This might be too broad
        # if we're processing incrementally. Let's stick to it for now for simplicity.
        delete_success = self.db_manager.execute_query("DELETE FROM processed_estimates", commit=True)
        if not delete_success:
            logger.error("Failed to clear existing data in 'processed_estimates' table.")
            return False, "Failed to clear old processed data. Aborting save."
        logger.info("Cleared ALL existing data in 'processed_estimates' table.")

        # Prepare data for insertion
        # The df_to_save should now have 'RawEstimateID' as the first column.
        # Columns for INSERT statement should match 'processed_estimates' table structure from schema.sql,
        # excluding its own auto-incrementing PK ('ProcessedEstimateID').
        # Using exact casing from schema.sql: CostCode, Description, Quantity, Unit, UnitCost, TotalCost, Phase, ProjectID, RawEstimateID
        db_columns_for_insert = [
            'RawEstimateID', 'CostCode', 'Description', 'Quantity', 'Unit',
            'UnitCost', 'TotalCost', 'Phase', 'ProjectID'
        ]
        # DataFrame columns are currently: 'RawEstimateID', 'cost_code', 'description', etc.
        # We need to map df_to_save column names to schema column names if they differ in case.
        # Config.ESTIMATE_COLUMN_MAPPING gives 'Cost Code' -> 'cost_code'. We need reverse for insert if df has 'cost_code'.
        # The df_to_save has already been processed to have 'cost_code', 'description', etc. (lowercase internal names).

        # Create a mapping from our internal DataFrame column names to the DB schema column names
        # This is a bit manual; could be derived if internal names consistently map to schema names with case change.
        df_to_db_col_map = {
            'RawEstimateID': 'RawEstimateID', # Same
            'cost_code': 'CostCode',         # Different case
            'description': 'Description',     # Different case
            'quantity': 'Quantity',         # Different case
            'unit': 'Unit',                 # Different case
            'unit_cost': 'UnitCost',         # Different case
            'total_cost': 'TotalCost',       # Different case
            'phase': 'Phase',               # Different case
            'project_id': 'ProjectID'        # Different case
        }

        # Select and rename columns in df_to_save to match db_columns_for_insert for the INSERT query
        df_renamed_for_insert = df_to_save.rename(columns=df_to_db_col_map)

        # Ensure all target DB columns are present in the renamed DataFrame
        final_df_for_insert = pd.DataFrame()
        for col in db_columns_for_insert:
            if col in df_renamed_for_insert.columns:
                final_df_for_insert[col] = df_renamed_for_insert[col]
            else:
                logger.error(f"Critical error: DB column '{col}' not found in DataFrame prepared for insert. This should not happen.")
                return False, f"Internal error: Missing column {col} for DB insert."

        # Convert specific columns to None if they are NaN
        # (using .loc to avoid SettingWithCopyWarning)
        if 'ProjectID' in final_df_for_insert.columns:
             final_df_for_insert.loc[:, 'ProjectID'] = final_df_for_insert['ProjectID'].apply(lambda x: None if pd.isna(x) else x)
        if 'RawEstimateID' in final_df_for_insert.columns:
             final_df_for_insert.loc[:, 'RawEstimateID'] = final_df_for_insert['RawEstimateID'].apply(lambda x: None if pd.isna(x) else int(x))

        data_to_insert = [tuple(row) for row in final_df_for_insert.to_numpy()]

        if not data_to_insert:
            logger.info("DataFrame was empty after final preparation for DB insert. Nothing to save to processed_estimates.")
            return True, "No data to save after final column preparation."

        insert_query = f"""
        INSERT INTO processed_estimates (
            {', '.join(db_columns_for_insert)}
        ) VALUES ({', '.join(['?'] * len(db_columns_for_insert))})
        """

        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(insert_query, data_to_insert)

            # Update status of raw_estimates
            if raw_estimate_ids_to_update:
                # Ensure IDs are integers for the SQL query
                valid_ids = [int(id_val) for id_val in raw_estimate_ids_to_update if pd.notna(id_val)]
                if valid_ids:
                    placeholders = ', '.join(['?'] * len(valid_ids))
                    update_raw_status_query = f"UPDATE raw_estimates SET Status = 'Processed' WHERE RawEstimateID IN ({placeholders})"
                    cursor.execute(update_raw_status_query, valid_ids)
                    logger.info(f"Updated status to 'Processed' for {len(valid_ids)} raw estimate records.")
                else:
                    logger.warning("No valid RawEstimateIDs provided to update status, though save was attempted.")

            conn.commit()
            logger.info(f"Successfully saved {len(data_to_insert)} processed estimate records and updated raw statuses.")
            return True, f"Successfully processed and saved {len(data_to_insert)} estimate items."

        except sqlite3.Error as e_sql:
            if conn: conn.rollback()
            logger.error(f"SQLite error during saving processed data or updating raw_estimates: {e_sql}")
            logger.error(f"Failed query might be related to: {insert_query[:100]} or update_raw_status_query")
            return False, f"Database error saving processed data: {e_sql}"
        except Exception as e: # Catch any other unexpected error during this process
            if conn: conn.rollback()
            logger.exception(f"An unexpected error occurred in _save_processed_data: {e}")
            return False, f"An unexpected error occurred: {e}"


    def process_turnover_file(self, file_path, project_id=None):
        logger.info(f"Processing turnover file: {file_path} for project_id: {project_id}")
        try:
            # This is a simplified version of the logic from turnover.py
            # It will need to be adapted to fit the database schema and project structure
            
            # For now, we'll just read the file and log its contents
            
            # --- Core Processing Logic from turnover.py ---
            
            # Regex to find the Job ID and Project Name from the first line of the file
            # Example: Job ID,"12345" Project,"My Project"
            
            # Read lines from the file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            parsed_item_data = []
            current_task, current_cost_code = "", ""
            global_customer, global_ref_number = "", ""

            if lines:
                first_row = lines[0]
                job_id_match = re.search(r'Job ID,\"([^\"]*)\"', first_row)
                if job_id_match: global_ref_number = job_id_match.group(1).strip()
                project_name_match = re.search(r'Project,\"([^\"]*)\"', first_row)
                if project_name_match: global_customer = project_name_match.group(1).strip()

            for line in lines:
                line = line.strip()
                # Regex to find the current Task
                # Example: Task: 01-010
                task_match = re.match(r'Task:\s*([^,]+)', line)
                if task_match:
                    current_task = task_match.group(1).strip()
                    continue
                # Regex to find the current Cost Code
                # Example: Cost Code: 01-010-010
                cost_code_match = re.match(r'Cost Code:\s*([^,]+)', line)
                if cost_code_match:
                    current_cost_code = cost_code_match.group(1).strip()
                    continue
                # Regex to find the item data
                # Example: ,12345,10.0,EA,M,
                item_match = re.search(r'^,(\d+),([\d\.]+),([A-Z\s/]+),M,', line)
                if item_match:
                    stock_number, quantity = item_match.group(1).strip(), float(item_match.group(2).strip())
                    if quantity == 0: continue
                    processed_row = {
                        "cost_code": current_cost_code,
                        "description": f"Item: {stock_number}",
                        "quantity": quantity,
                        "unit": item_match.group(3).strip(),
                        "unit_cost": 0, # Not available in this file
                        "total_cost": 0, # Not available in this file
                        "phase": current_task,
                        "project_id": project_id
                    }
                    parsed_item_data.append(processed_row)

            if not parsed_item_data:
                return False, "No valid item data rows were parsed."
            
            final_df = pd.DataFrame(parsed_item_data)
            logger.info(f"Successfully parsed {len(final_df)} total items from report.")
            
            # --- Save to processed_estimates table ---
            
            return self._save_processed_data(final_df)

        except Exception as e:
            logger.error(f"Error processing turnover file: {e}")
            return False, f"Error processing turnover file: {e}"

    def process_daily_log_entry(self, log_entry: str, employee_id: int, project_id: int = None):
        """
        Parses a single daily log entry string and extracts relevant information.
        For now, it will just log the extracted data.
        Later, this will store data in appropriate database tables.
        """
        logger.info(f"Processing daily log entry for employee {employee_id}, project {project_id}:\n{log_entry[:200]}...")

        parsed_data = {
            "log_date": None,
            "job_site": "N/A",
            "tasks_completed": [],
            "tasks_ongoing": [],
            "materials_used": "N/A",
            "materials_needed": "N/A",
            "hours_worked": 0.0,
            "safety_observations": "N/A",
            "issues_blockers": "N/A",
            "tool_notes": "N/A",
            "employee_id": employee_id,
            "project_id": project_id
        }

        # Extract Log Date
        date_match = re.search(r'Template Date:\s*(\d{4}-\d{2}-\d{2})', log_entry)
        if date_match:
            parsed_data["log_date"] = date_match.group(1)
        else:
            # Fallback to current date if not found in log
            parsed_data["log_date"] = datetime.now().strftime("%Y-%m-%d")
            logger.warning(f"Log date not found in entry. Using current date: {parsed_data['log_date']}")

        # Extract Job Site
        job_site_match = re.search(r'Job Site / Location:\s*\n\s*\*(.*?)\*', log_entry, re.DOTALL)
        if job_site_match:
            parsed_data["job_site"] = job_site_match.group(1).strip()

        # Extract Tasks
        tasks_section_match = re.search(r'Today\'s Tasks:\s*\n(.*?)(?=\n\s*Materials Used / Needed:|\Z)', log_entry, re.DOTALL)
        if tasks_section_match:
            tasks_text = tasks_section_match.group(1)
            for line in tasks_text.split('\n'):
                line = line.strip()
                if line.startswith('* `[x]`'):
                    parsed_data["tasks_completed"].append(line[len('* `[x]`'):].strip())
                elif line.startswith('* `[ ]`'):
                    parsed_data["tasks_ongoing"].append(line[len('* `[ ]`'):].strip())

        # Extract Materials Used / Needed
        materials_match = re.search(r'Materials Used / Needed:\s*\n\s*\*(.*?)\*', log_entry, re.DOTALL)
        if materials_match:
            materials_text = materials_match.group(1).strip()
            if "Used:" in materials_text:
                parsed_data["materials_used"] = materials_text.split("Used:")[1].split("Need:")[0].strip() if "Need:" in materials_text else materials_text.split("Used:")[1].strip()
            if "Need:" in materials_text:
                parsed_data["materials_needed"] = materials_text.split("Need:")[1].strip()

        # Extract Hours Worked
        hours_match = re.search(r'Hours Worked:\s*\n\s*\*(.*?)\*', log_entry, re.DOTALL)
        if hours_match:
            hours_text = hours_match.group(1).strip()
            try:
                # Try to extract numeric hours, e.g., "8 hours" or "7:00 AM - 3:30 PM"
                numeric_hours_match = re.search(r'(\d+(\.\d+)?)\s*hours', hours_text)
                if numeric_hours_match:
                    parsed_data["hours_worked"] = float(numeric_hours_match.group(1))
                else:
                    # Attempt to calculate from time range if present
                    time_range_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)', hours_text)
                    if time_range_match:
                        start_time_str, end_time_str = time_range_match.groups()
                        # Assuming same day for simplicity, adjust if cross-day logs are possible
                        dummy_date = datetime.now().strftime("%Y-%m-%d")
                        start_dt = datetime.strptime(f"{dummy_date} {start_time_str}", "%Y-%m-%d %I:%M %p")
                        end_dt = datetime.strptime(f"{dummy_date} {end_time_str}", "%Y-%m-%d %I:%M %p")
                        duration = end_dt - start_dt
                        parsed_data["hours_worked"] = duration.total_seconds() / 3600.0
            except Exception as e:
                logger.warning(f"Could not parse hours worked from '{hours_text}': {e}")

        # Extract Safety Checks / Observations
        safety_match = re.search(r'Safety Checks / Observations:\s*\n\s*\*(.*?)\*', log_entry, re.DOTALL)
        if safety_match:
            parsed_data["safety_observations"] = safety_match.group(1).strip()

        # Extract Issues / Questions / Blockers
        issues_match = re.search(r'Issues / Questions / Blockers:\s*\n\s*\*(.*?)\*', log_entry, re.DOTALL)
        if issues_match:
            parsed_data["issues_blockers"] = issues_match.group(1).strip()

        # Extract Tool Notes
        tool_notes_match = re.search(r'Tool Notes:\s*\n\s*\*(.*?)\*', log_entry, re.DOTALL)
        if tool_notes_match:
            parsed_data["tool_notes"] = tool_notes_match.group(1).strip()

        logger.info(f"Initial Parsed Daily Log Data: {parsed_data}")

        conn = self.db_manager.get_connection()
        daily_log_id = None # Initialize daily_log_id
        llm_processed_info = "" # To store info about LLM processing

        try:
            cursor = conn.cursor()

            # 1. Insert into DailyLogs table
            insert_daily_log_query = """
            INSERT INTO DailyLogs (EmployeeID, ProjectID, LogDate, JobSite, HoursWorked, Notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            # Combine some free-form text fields for the main DailyLogs.Notes if needed, or handle separately
            # For now, let's assume general notes might be added later or are not directly from these specific fields.
            main_notes = f"Safety: {parsed_data['safety_observations']}\nIssues: {parsed_data['issues_blockers']}\nTools: {parsed_data['tool_notes']}"

            daily_log_params = (
                parsed_data["employee_id"],
                parsed_data["project_id"],
                parsed_data["log_date"],
                parsed_data["job_site"],
                parsed_data["hours_worked"],
                main_notes # Storing combined notes from specific sections
            )
            cursor.execute(insert_daily_log_query, daily_log_params)
            daily_log_id = cursor.lastrowid
            logger.info(f"DailyLog record created with ID: {daily_log_id}")

            # 2. Insert tasks into DailyLogTasks
            insert_task_query = """
            INSERT INTO DailyLogTasks (DailyLogID, TaskDescription, IsCompleted)
            VALUES (?, ?, ?)
            """
            for task_desc in parsed_data["tasks_completed"]:
                cursor.execute(insert_task_query, (daily_log_id, task_desc, 1))
            for task_desc in parsed_data["tasks_ongoing"]:
                cursor.execute(insert_task_query, (daily_log_id, task_desc, 0))

            # 3. Insert materials into DailyLogMaterials
            insert_material_query = """
            INSERT INTO DailyLogMaterials (DailyLogID, MaterialDescription, Type)
            VALUES (?, ?, ?)
            """
            if parsed_data["materials_used"] and parsed_data["materials_used"].lower() not in ["n/a", "none", ""]:
                cursor.execute(insert_material_query, (daily_log_id, parsed_data["materials_used"], "Used"))
            if parsed_data["materials_needed"] and parsed_data["materials_needed"].lower() not in ["n/a", "none", ""]:
                cursor.execute(insert_material_query, (daily_log_id, parsed_data["materials_needed"], "Needed"))

            # 4. Insert observations into DailyLogObservations (Original Regex Parsed)
            # This is now more for specific, structured observations if the regex was very precise.
            # The LLM will handle the more free-form text from these sections.
            insert_observation_query = """
            INSERT INTO DailyLogObservations (DailyLogID, ObservationType, Description)
            VALUES (?, ?, ?)
            """
            # Example: If safety_observations was a very structured list, insert here.
            # For now, these are passed to LLM.

            # LLM Parsing for free-form text sections
            free_form_texts_for_llm = {
                "SafetyObservations": parsed_data["safety_observations"],
                "IssuesBlockers": parsed_data["issues_blockers"],
                "ToolNotes": parsed_data["tool_notes"],
                "MaterialsUsed": parsed_data["materials_used"], # Could also be parsed by LLM if complex
                "MaterialsNeeded": parsed_data["materials_needed"] # Could also be parsed by LLM
            }

            llm_log_insert_query = """
            INSERT INTO LLM_Parsed_Data_Log (SourceModule, SourceRecordID, OriginalInput, ParsedJSON, ConfidenceScore, ParsingTimestamp)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """

            for section_name, text_content in free_form_texts_for_llm.items():
                if text_content and text_content.lower() not in ["n/a", "none", ""]:
                    logger.info(f"Calling LLM for section: {section_name} of DailyLogID: {daily_log_id}")
                    parsed_json, confidence = self._call_llm_for_parsing(text_content, schema_hint=f"DailyLog_{section_name}")

                    llm_log_params = (
                        f"DailyLog_{section_name}", # SourceModule
                        daily_log_id,             # SourceRecordID (link to the DailyLogs table entry)
                        text_content,             # OriginalInput
                        parsed_json,              # ParsedJSON
                        confidence                # ConfidenceScore
                    )
                    cursor.execute(llm_log_insert_query, llm_log_params)
                    logger.info(f"LLM parsing result for {section_name} (DailyLogID: {daily_log_id}) logged to LLM_Parsed_Data_Log.")

            llm_processed_info = " LLM processing attempted for relevant sections."

            conn.commit()
            success_message = f"Daily log entry (ID: {daily_log_id}) saved successfully.{llm_processed_info}"
            logger.info(success_message)
            return True, success_message, daily_log_id

        except sqlite3.Error as e_sql:
            if conn: conn.rollback()
            logger.error(f"SQLite error during daily log storage (DailyLogID attempted: {daily_log_id}): {e_sql}")
            return False, f"Database error saving daily log: {e_sql}", None
        except Exception as e:
            if conn: conn.rollback()
            logger.exception(f"An unexpected error occurred during daily log storage (DailyLogID attempted: {daily_log_id}): {e}")
            return False, f"An unexpected error occurred: {e}", None
