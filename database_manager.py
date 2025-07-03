import sqlite3
import os
import hashlib # For password hashing
import logging

# Configure logging for database operations
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Removed basicConfig
logger = logging.getLogger(__name__)

import sqlite3
import os
import hashlib # For password hashing
import logging # Keep import for getLogger

# Configure logging for database operations
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Removed basicConfig
logger = logging.getLogger(__name__) # Restored logger definition

from configuration import Config # Changed from relative to absolute

class DatabaseManager:
    _instance = None
    # _db_file and _schema_file will be instance variables

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # Create the new instance
            instance = super(DatabaseManager, cls).__new__(cls)
            # Set instance-specific paths using Config at the moment of creation
            instance._db_file = Config.get_database_path() # Corrected method name
            instance._schema_file = Config.get_schema_path() # Will add this method to Config
            # Initialize the database for this instance
            instance._initialize_db()
            cls._instance = instance
        return cls._instance

    def _initialize_db(self):
        # self._db_file and self._schema_file are now instance variables
        db_exists = os.path.exists(self._db_file)

        # Ensure the directory for the database file exists
        db_dir = os.path.dirname(self._db_file)
        if db_dir: # Check if db_dir is not empty (e.g. if _db_file is just a name like ":memory:")
            os.makedirs(db_dir, exist_ok=True)

        db_uri = f"file:{self._db_file}?mode=rwc" # mode=rwc (read-write-create)
        try:
            self.conn = sqlite3.connect(db_uri, uri=True)
            logger.info(f"DatabaseManager attempting to connect to DB via URI: {db_uri}")
        except sqlite3.OperationalError as e:
            logger.error(f"Failed to connect to DB with URI {db_uri}: {e}. Falling back to path only.")
            # Fallback if URI with mode=rwc is not supported or path has issues with URI scheme
            self.conn = sqlite3.connect(self._db_file)

        self.conn.row_factory = sqlite3.Row # This allows fetching rows as dictionary-like objects
        self.cursor = self.conn.cursor()
        logger.info(f"DatabaseManager connected to DB: {self._db_file}")

        if not db_exists:
            logger.info(f"Database file '{self._db_file}' not found. Creating new database and applying schema '{self._schema_file}'...")
            self._apply_schema()
            logger.info(f"Database '{self._db_file}' initialized successfully with schema.")
        else:
            logger.info(f"Database file '{self._db_file}' found. Connecting to existing database.")

        # Always ensure users table and default admin exist, even if DB existed
        self._create_users_table_and_default_admin()

    def _apply_schema(self):
        # self._schema_file is an instance variable
        try:
            if not os.path.exists(self._schema_file):
                logger.error(f"DATABASE_MANAGER: Schema file not found at {self._schema_file}. Cannot apply schema.")
                # raise FileNotFoundError(f"Schema file not found: {self._schema_file}") # Or handle as appropriate
                return # Cannot proceed without schema file

            with open(self._schema_file, 'r') as f:
                sql_script = f.read()

            # Split the script into individual statements
            # Remove comments first (simple approach for -- style comments)
            sql_script_no_comments = "\n".join(line for line in sql_script.splitlines() if not line.strip().startswith('--'))

            # Split by semicolon. Filter out empty strings that can result from multiple semicolons or semicolons at the end.
            statements = [stmt.strip() for stmt in sql_script_no_comments.split(';') if stmt.strip()]

            if not statements:
                logger.warning(f"No SQL statements found in schema file: {self._schema_file} after stripping comments and splitting.")
                # If the schema is intentionally empty, this is not an error.
                # However, for this project, schema.sql is expected to have content.
                # Consider raising an error or specific handling if an empty schema is problematic.
                return # Or raise error if schema cannot be empty

            logger.info(f"Found {len(statements)} statements to execute from {self._schema_file}.")
            completed_statements = 0
            for i, statement in enumerate(statements):
                try:
                    # More verbose logging for specific tables of interest
                    if "CREATE TABLE CustomerTypes" in statement:
                        logger.info(f"Attempting to execute: {statement[:100]}")
                    elif "CREATE TABLE ProjectStatuses" in statement:
                        logger.info(f"Attempting to execute: {statement[:100]}")
                    elif "CREATE TABLE Customers" in statement and "CustomerTypeID INT NULL" in statement : # The detailed one
                        logger.info(f"Attempting to execute: {statement[:100]}")

                    self.cursor.execute(statement)
                    completed_statements += 1
                except sqlite3.Error as e_stmt:
                    logger.error(f"DATABASE_MANAGER: Error executing schema statement {i+1}/{len(statements)}: '{statement[:200]}...'")
                    logger.error(f"DATABASE_MANAGER: SQLite error: {e_stmt}")
                    raise  # Re-raise to be caught by the outer try-except

            self.conn.commit()
            logger.info(f"DATABASE_MANAGER: Schema from {self._schema_file} applied. {completed_statements}/{len(statements)} statements executed successfully.")
        except sqlite3.Error as e: # This will catch the re-raised error from the loop or other sqlite errors
            logger.error(f"DATABASE_MANAGER: Overall error applying schema from {self._schema_file}: {e}")
            # Optionally, roll back or delete the partially created DB file
            if os.path.exists(self._db_file):
                os.remove(self._db_file)
            raise

    def _create_users_table_and_default_admin(self):
        # Create a simple 'users' table as described in README.md,
        # separate from the detailed HR.Employees table in your schema.sql
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            ''')
            self.conn.commit()
            logger.info("Checked/created 'users' table.")

            # Create default admin user if not exists
            default_username = "admin"
            default_password = "admin_password" # This should be hashed immediately
            hashed_password = hashlib.sha256(default_password.encode()).hexdigest()

            self.cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (default_username,))
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                                    (default_username, hashed_password, "admin"))
                self.conn.commit()
                logger.info("Default admin user created.")
            else:
                logger.info("Default admin user already exists.")

        except sqlite3.Error as e:
            logger.error(f"Error creating users table or default admin: {e}")
            raise


    def get_connection(self):
        return self.conn

    def get_cursor(self):
        return self.cursor

    def execute_query(self, query, params=None, commit=False, fetch_one=False, fetch_all=False):
        """
        Executes a SQL query.
        :param query: The SQL query string.
        :param params: A tuple of parameters to bind to the query.
        :param commit: Boolean, whether to commit the transaction.
        :param fetch_one: Boolean, whether to fetch one result.
        :param fetch_all: Boolean, whether to fetch all results.
        :return: Query results if fetching, True for successful commit, False otherwise.
        """
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if commit:
                self.conn.commit()
                return cursor
            elif fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            return True # For operations like CREATE TABLE, UPDATE, DELETE without fetching
        except sqlite3.Error as e:
            logger.error(f"Database error during query execution: {e}")
            if commit:
                self.conn.rollback()
            return False

    def execute_many_query(self, query, params_list, commit=False):
        """
        Executes a SQL query for multiple sets of parameters.
        :param query: The SQL query string.
        :param params_list: A list of tuples, where each tuple is a set of parameters for one execution.
        :param commit: Boolean, whether to commit the transaction after all executions.
        :return: True for successful commit, False otherwise.
        """
        try:
            cursor = self.conn.cursor()
            cursor.executemany(query, params_list)
            if commit:
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error during execute_many_query: {e}")
            if commit:
                self.conn.rollback()
            return False

    def close_connection(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

# Note: The logging setup is basic. For a production system, you'd want more
# sophisticated logging to a file as mentioned in your README.md under "Logging".

db_manager = DatabaseManager()
