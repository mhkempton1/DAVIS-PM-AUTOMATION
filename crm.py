import logging

logger = logging.getLogger(__name__)

class Crm:
    def __init__(self, db_m_instance):
        self.db_manager = db_m_instance
        logger.info("CRM module initialized with provided db_manager.")

    def add_customer(self, customer_name, customer_type_name, billing_address, qb_customer_id=None, default_payment_terms=None, is_active=True):
        """Adds a new customer to the database."""
        try:
            # First, get the CustomerTypeID from the CustomerTypes table
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT CustomerTypeID FROM CustomerTypes WHERE TypeName = ?", (customer_type_name,))
            result = cursor.fetchone()
            if not result:
                logger.error(f"Customer type '{customer_type_name}' not found.")
                return False, f"Customer type '{customer_type_name}' not found."
            customer_type_id = result[0]

            # Now, insert the new customer
            sql = """
                INSERT INTO Customers (CustomerName, CustomerTypeID, BillingAddress_Street, QuickBooksCustomerID, DefaultPaymentTerms, IsActive)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (customer_name, customer_type_id, billing_address, qb_customer_id, default_payment_terms, is_active))
            self.db_manager.conn.commit()
            logger.info(f"Customer '{customer_name}' added successfully.")
            return True, "Customer added successfully."
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            self.db_manager.conn.rollback()
            return False, f"Error adding customer: {e}"

    def get_customer_by_name(self, customer_name):
        """Retrieves a customer by name."""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT * FROM Customers WHERE CustomerName = ?", (customer_name,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting customer by name: {e}")
            return None
