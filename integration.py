import pandas as pd
import os
import logging
from configuration import Config
from database_manager import db_manager

logger = logging.getLogger(__name__)

class Integration:
    def __init__(self, db_m_instance=None):
        self.db_manager = db_m_instance if db_m_instance else db_manager
        logger.info("Integration module initialized.")

    def import_estimate_from_csv(self, file_path, project_id=None):
        if not os.path.exists(file_path):
            logger.error(f"CSV file not found: {file_path}")
            return False, "File not found."

        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')

            if df.empty:
                logger.warning(f"Estimate CSV file '{file_path}' is empty or has no data rows. Nothing to import.")
                return False, "Estimate CSV file is empty or contains no data."

            insert_query = """
            INSERT INTO raw_estimates (ProjectID, RawData, SourceFile, Status)
            VALUES (?, ?, ?, ?)
            """

            base_filename = os.path.basename(file_path)
            imported_rows_count = 0

            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            try:
                for index, row in df.iterrows():
                    estimate_json = pd.Series(row).to_json(orient='index') # Changed raw_data_json to estimate_json
                    params = (project_id, estimate_json, base_filename, 'Pending Processing')
                    cursor.execute(insert_query, params)
                    imported_rows_count += 1

                conn.commit()
                logger.info(f"Successfully imported {imported_rows_count} estimate line items from '{file_path}' into raw_estimates.") # Clarified log
                return True, f"Successfully imported {imported_rows_count} estimate line items from '{base_filename}'." # Clarified message

            except Exception as e_inner:
                conn.rollback()
                logger.error(f"Error during batch insert of estimates from CSV '{file_path}': {e_inner}", exc_info=True) # Clarified log
                return False, f"Error during database insert of estimates: {e_inner}" # Clarified message

        except FileNotFoundError:
            logger.error(f"Error: The estimate CSV file '{file_path}' was not found.") # Clarified log
            return False, "Estimate CSV file not found."
        except pd.errors.EmptyDataError:
            logger.error(f"Error: The estimate CSV file '{file_path}' is empty (pandas error).") # Clarified log
            return False, "Empty estimate CSV file."
        except pd.errors.ParserError as pe:
            logger.error(f"Error: Could not parse estimate CSV '{file_path}'. Check CSV format. Details: {pe}") # Clarified log
            return False, "Estimate CSV parsing error. Ensure valid CSV format."
        except Exception as e:
            logger.exception(f"An unexpected error occurred during estimate CSV import of '{file_path}': {e}") # Clarified log
            return False, f"An unexpected error occurred during estimate import: {e}" # Clarified message

    def import_labor_budget_from_csv(self, file_path, project_id=None):
        """
        Imports labor budget data from a CSV file into the 'project_budgets' table.
        Assumes the CSV has columns like 'Phase', 'Task', 'Cost Code', 'Labor', 'Material', etc.
        """
        if not os.path.exists(file_path):
            logger.error(f"Labor budget CSV file not found: {file_path}")
            return False, "File not found."

        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')

            # Identify the row containing headers (e.g., 'Phase', 'Task', 'Cost Code', 'Labor')
            # This is a heuristic based on the sample provided in the document analysis.
            header_row_index = -1
            for i, row in df.iterrows():
                if 'Phase' in row.values and 'Labor' in row.values and 'Cost Code' in row.values:
                    header_row_index = i
                    break
            
            if header_row_index == -1:
                logger.error(f"Could not find header row in labor budget CSV: {file_path}")
                return False, "Invalid CSV format: Header row not found."

            # Read the CSV again, this time specifying the header row
            df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=header_row_index + 1, header=None)
            # Re-read headers from the identified header row
            headers = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=header_row_index, nrows=1, header=None).iloc[0].tolist()
            df.columns = headers

            # Clean column names (remove leading/trailing spaces, handle special chars)
            df.columns = df.columns.str.strip().str.replace(r'[^a-zA-Z0-9_]', '', regex=True)
            df.rename(columns={'CostCode': 'CostCode', 'Labor': 'Labor', 'Material': 'Material', 'Equip': 'Equip', 'SubCont': 'SubCont', 'DJC': 'DJC'}, inplace=True)

            required_cols = ['Phase', 'Task', 'CostCode', 'Labor']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns in labor budget CSV: {required_cols}. Found: {df.columns.tolist()}")
                return False, "Missing required columns in CSV."

            # Filter out rows where CostCode is empty or 'Job'
            df = df[df['CostCode'].notna() & (df['CostCode'] != 'Job')]

            if df.empty:
                logger.warning(f"No valid data rows found in labor budget CSV after filtering: {file_path}")
                return False, "No valid data rows to import after filtering."

            # Convert relevant columns to numeric, coercing errors
            for col in ['Labor', 'Material', 'Equip', 'SubCont', 'DJC']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '', regex=False) # Remove commas
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                else:
                    df[col] = 0.0 # Add column if missing and set to 0

            insert_query = """
            INSERT INTO project_budgets (ProjectID, WBSElementID, BudgetType, Amount, Notes)
            VALUES (?, ?, ?, ?, ?)
            """
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            inserted_rows = 0

            for index, row in df.iterrows():
                # Try to find WBSElementID based on ProjectID and CostCode
                wbs_element_id = None
                if project_id and 'CostCode' in row and row['CostCode']:
                    wbs_query = "SELECT WBSElementID FROM wbs_elements WHERE ProjectID = ? AND WBSCode = ?"
                    wbs_row = self.db_manager.execute_query(wbs_query, (project_id, row['CostCode']), fetch_one=True)
                    if wbs_row:
                        wbs_element_id = wbs_row['WBSElementID']

                # Insert Labor budget
                if row['Labor'] > 0:
                    cursor.execute(insert_query, (project_id, wbs_element_id, 'Labor', row['Labor'], f"From {os.path.basename(file_path)} - Phase: {row.get('Phase','N/A')} Task: {row.get('Task','N/A')}"))
                    inserted_rows += 1
                
                # Insert Material budget
                if row['Material'] > 0:
                    cursor.execute(insert_query, (project_id, wbs_element_id, 'Material', row['Material'], f"From {os.path.basename(file_path)} - Phase: {row.get('Phase','N/A')} Task: {row.get('Task','N/A')}"))
                    inserted_rows += 1

                # Insert Equip budget
                if row['Equip'] > 0:
                    cursor.execute(insert_query, (project_id, wbs_element_id, 'Equipment', row['Equip'], f"From {os.path.basename(file_path)} - Phase: {row.get('Phase','N/A')} Task: {row.get('Task','N/A')}"))
                    inserted_rows += 1

                # Insert SubCont budget
                if row['SubCont'] > 0:
                    cursor.execute(insert_query, (project_id, wbs_element_id, 'Subcontractor', row['SubCont'], f"From {os.path.basename(file_path)} - Phase: {row.get('Phase','N/A')} Task: {row.get('Task','N/A')}"))
                    inserted_rows += 1

                # Insert DJC budget
                if row['DJC'] > 0:
                    cursor.execute(insert_query, (project_id, wbs_element_id, 'Direct Job Cost', row['DJC'], f"From {os.path.basename(file_path)} - Phase: {row.get('Phase','N/A')} Task: {row.get('Task','N/A')}"))
                    inserted_rows += 1

            conn.commit()
            logger.info(f"Successfully imported {inserted_rows} budget entries from '{file_path}' into project_budgets.")
            return True, f"Successfully imported {inserted_rows} budget entries from '{os.path.basename(file_path)}'."

        except Exception as e:
            logger.exception(f"An unexpected error occurred during labor budget CSV import of '{file_path}': {e}")
            return False, f"An unexpected error occurred: {e}"

    def import_sales_order_from_csv(self, file_path, project_id=None):
        """
        Placeholder for importing sales order data from a CSV file.
        """
        logger.info(f"Simulating import of sales order CSV: {file_path}")
        return True, "Sales order import simulated successfully."

    def import_material_details_from_csv(self, file_path):
        """
        Placeholder for importing material details from a CSV file.
        """
        logger.info(f"Simulating import of material details CSV: {file_path}")
        return True, "Material details import simulated successfully."

    def export_data_to_excel(self, data_df, output_filename, sheet_name='Report'):
        if not isinstance(data_df, pd.DataFrame):
            logger.error("Invalid data type for export to Excel. DataFrame required.")
            return False, "Invalid data for export (must be DataFrame)."

        output_path = os.path.join(Config.get_reports_dir(), output_filename)
        try:
            data_df.to_excel(output_path, sheet_name=sheet_name, index=False)
            logger.info(f"Successfully exported data to Excel: {output_path}")
            return True, f"Report exported to {output_path}"
        except Exception as e:
            logger.exception(f"Error exporting data to Excel '{output_path}': {e}")
            return False, f"Failed to export report: {e}"

    def export_data_to_csv(self, data_df, output_filename):
        if not isinstance(data_df, pd.DataFrame):
            logger.error("Invalid data type for export to CSV. DataFrame required.")
            return False, "Invalid data for export (must be DataFrame)."

        output_path = os.path.join(Config.get_reports_dir(), output_filename)
        try:
            data_df.to_csv(output_path, index=False)
            logger.info(f"Successfully exported data to CSV: {output_path}")
            return True, f"Report exported to {output_path}"
        except Exception as e:
            logger.exception(f"Error exporting data to CSV '{output_path}': {e}")
            return False, f"Failed to export report: {e}"

    def get_raw_estimates(self): # Method name kept for consistency with table
        """Retrieves all imported (raw) estimates from the database."""
        query = "SELECT RawEstimateID, ProjectID, RawData, SourceFile, Status FROM raw_estimates"
        rows = self.db_manager.execute_query(query, fetch_all=True)

        if rows is None:
            logger.error("Failed to retrieve imported estimates from database.") # Clarified log
            return pd.DataFrame()
        if not rows:
            logger.info("No imported estimates found in the database.") # Added info log
            return pd.DataFrame()

        logger.info(f"Retrieved {len(rows)} imported estimates.") # Added info log
        return pd.DataFrame([dict(row) for row in rows])

    # --- QuickBooks Integration Placeholders ---
    def connect_quickbooks(self):
        logger.info("connect_quickbooks called (Not Implemented)")
        return False, "QuickBooks connection is not implemented."

    def disconnect_quickbooks(self):
        logger.info("disconnect_quickbooks called (Not Implemented)")
        return False, "QuickBooks disconnection is not implemented."

    def is_quickbooks_connected(self):
        logger.info("is_quickbooks_connected called (Not Implemented)")
        # Returns a tuple: (is_connected_bool, status_message_str)
        return False, "Not Implemented"

    def fetch_quickbooks_sov(self, qb_project_id_external):
        logger.info(f"fetch_quickbooks_sov called for QB Project ID: {qb_project_id_external} (Not Implemented)")
        return False, "Fetching SOV from QuickBooks is not implemented." # Or (True, []) if you want to simulate empty success

    def link_quickbooks_sov_to_internal(self, internal_project_id, sov_data):
        logger.info(f"link_quickbooks_sov_to_internal called for Internal PID: {internal_project_id} (Not Implemented)")
        return False, "Linking SOV to internal project is not implemented."

    def get_processed_estimates(self):
        """Retrieves all processed estimates from the database."""
        query = "SELECT ProcessedEstimateID, ProjectID, RawEstimateID, CostCode, Description, Quantity, Unit, UnitCost, TotalCost, Phase, ProcessedDate FROM processed_estimates"
        rows = self.db_manager.execute_query(query, fetch_all=True)

        if rows is None:
            logger.error("Failed to retrieve processed estimates from database.")
            return pd.DataFrame()
        if not rows:
            logger.info("No processed estimates found in the database.") # Added info log
            return pd.DataFrame()

        logger.info(f"Retrieved {len(rows)} processed estimates.") # Added info log
        return pd.DataFrame([dict(row) for row in rows])