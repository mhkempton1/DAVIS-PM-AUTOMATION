import logging

logger = logging.getLogger(__name__)

class Estimate:
    def __init__(self, db_m_instance):
        self.db_manager = db_m_instance
        logger.info("Estimate module initialized with provided db_manager.")

    def _get_customer_id_by_name(self, customer_name):
        """Helper function to get a customer's ID by their name."""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT CustomerID FROM Customers WHERE CustomerName = ?", (customer_name,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting customer ID by name: {e}")
            return None

    def create_estimate_header(self, estimate_number, project_id, customer_name, estimate_date, status="Draft", description=None, notes=None):
        """Creates a new estimate header in the database."""
        customer_id = self._get_customer_id_by_name(customer_name)
        if not customer_id:
            return False, f"Customer '{customer_name}' not found."

        try:
            sql = """
                INSERT INTO EstimateHeaders (EstimateNumber, ProjectID, CustomerID, EstimateDate, Status, Description, Notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor = self.db_manager.conn.cursor()
            cursor.execute(sql, (estimate_number, project_id, customer_id, estimate_date, status, description, notes))
            self.db_manager.conn.commit()
            logger.info(f"Estimate header '{estimate_number}' created successfully.")
            return True, "Estimate header created successfully."
        except Exception as e:
            logger.error(f"Error creating estimate header: {e}")
            self.db_manager.conn.rollback()
            return False, f"Error creating estimate header: {e}"

    def add_estimate_line_item(self, estimate_number, line_number, description, quantity, uom, unit_price, notes=None):
        """Adds a line item to an existing estimate."""
        try:
            # First, get the EstimateHeaderID from the estimate number
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT EstimateHeaderID FROM EstimateHeaders WHERE EstimateNumber = ?", (estimate_number,))
            result = cursor.fetchone()
            if not result:
                return False, f"Estimate '{estimate_number}' not found."
            estimate_header_id = result[0]

            # Now, insert the new line item
            sql = """
                INSERT INTO EstimateLineItems (EstimateHeaderID, LineNumber, Description, Quantity, UnitOfMeasure, UnitPrice, Notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            line_total = quantity * unit_price
            cursor.execute(sql, (estimate_header_id, line_number, description, quantity, uom, unit_price, notes))
            self.db_manager.conn.commit()
            logger.info(f"Line item {line_number} added to estimate '{estimate_number}'.")
            return True, "Line item added successfully."
        except Exception as e:
            logger.error(f"Error adding line item to estimate: {e}")
            self.db_manager.conn.rollback()
            return False, f"Error adding line item to estimate: {e}"
