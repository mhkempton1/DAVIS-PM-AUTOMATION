import sqlite3
import os
import hashlib
import logging

logger = logging.getLogger(__name__)

from configuration import Config


class DatabaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            instance = super(DatabaseManager, cls).__new__(cls)
            instance._db_file = Config.get_database_path()
            instance._schema_file = Config.get_schema_path()
            instance._initialize_db()
            cls._instance = instance
        return cls._instance

    def _initialize_db(self):
        db_exists = os.path.exists(self._db_file)
        db_dir = os.path.dirname(self._db_file)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        db_uri = f"file:{self._db_file}?mode=rwc"
        try:
            self.conn = sqlite3.connect(db_uri, uri=True)
            logger.info(f"DatabaseManager connected to DB via URI: {db_uri}")
        except sqlite3.OperationalError as e:
            logger.error(f"Failed to connect to DB with URI {db_uri}: {e}. Falling back to path only.")
            self.conn = sqlite3.connect(self._db_file)

        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        logger.info(f"DatabaseManager connection established to DB: {self._db_file}")

        if not db_exists:
            logger.info(f"Database file '{self._db_file}' not found. Creating and applying schema.")
            self._apply_schema() # This now also includes the users table with EmployeeID FK
            logger.info(f"Database '{self._db_file}' initialized with schema.")
        else:
            logger.info(f"Database file '{self._db_file}' found. Connecting to existing database.")
            # If DB exists, still ensure users table and EmployeeID column are up-to-date
            self._ensure_users_table_schema()

        self._create_default_admin_if_not_exists()

    def _apply_schema(self):
        try:
            if not os.path.exists(self._schema_file):
                logger.error(f"Schema file not found: {self._schema_file}. Cannot apply schema.")
                return

            with open(self._schema_file, 'r') as f:
                sql_script = f.read()

            # The schema.sql now includes the CREATE TABLE IF NOT EXISTS users with EmployeeID
            # So, we can directly execute it.
            self.cursor.executescript(sql_script) # Use executescript for multi-statement SQL from file
            self.conn.commit()
            logger.info(f"Schema from {self._schema_file} applied successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error applying schema from {self._schema_file}: {e}")
            if os.path.exists(self._db_file) and not os.path.exists(self._db_file): # Check if we were creating it
                try:
                    self.conn.close()
                    os.remove(self._db_file)
                    logger.info(f"Removed partially created database file: {self._db_file}")
                except Exception as e_remove:
                    logger.error(f"Error removing partially created database file: {e_remove}")
            raise

    def _ensure_users_table_schema(self):
        """Ensures the users table exists and has the EmployeeID column if DB already existed."""
        try:
            # Ensure users table exists (it should if schema.sql was ever run)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    EmployeeID INTEGER NULL,
                    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL
                )
            """)
            self.conn.commit()

            # Check if EmployeeID column exists, add if not
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]
            if 'EmployeeID' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN EmployeeID INTEGER NULL REFERENCES Employees(EmployeeID) ON DELETE SET NULL")
                self.conn.commit()
                logger.info("Added 'EmployeeID' column to existing 'users' table.")
            if 'IX_users_EmployeeID' not in [idx[1] for idx in self.cursor.execute("PRAGMA index_list(users)").fetchall()]:
                 self.cursor.execute("CREATE INDEX IF NOT EXISTS IX_users_EmployeeID ON users (EmployeeID)")
                 self.conn.commit()
                 logger.info("Ensured IX_users_EmployeeID index exists on 'users' table.")
        except sqlite3.Error as e:
            logger.error(f"Error ensuring 'users' table schema: {e}")
            # Not raising, to allow app to attempt to continue

    def _create_default_admin_if_not_exists(self):
        """Creates the default admin user if it doesn't exist."""
        try:
            default_username = Config.DEFAULT_ADMIN_USERNAME
            default_password = Config.DEFAULT_ADMIN_PASSWORD
            hashed_password = hashlib.sha256(default_password.encode()).hexdigest()

            self.cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (default_username,))
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute(
                    "INSERT INTO users (username, password_hash, role, EmployeeID) VALUES (?, ?, ?, ?)",
                    (default_username, hashed_password, "admin", None)
                )
                self.conn.commit()
                logger.info("Default admin user created.")
            else:
                logger.info("Default admin user already exists.")
        except sqlite3.Error as e:
            logger.error(f"Error creating default admin user: {e}")
            # Not raising, to allow app to attempt to continue

    def get_connection(self):
        return self.conn

    def get_cursor(self):
        return self.cursor

    def execute_query(self, query, params=None, commit=False, fetch_one=False, fetch_all=False):
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
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error executing query: {query[:100]}... - Error: {e}", exc_info=True)
            if commit:
                try:
                    self.conn.rollback()
                except sqlite3.Error as rb_err:
                    logger.error(f"Rollback failed: {rb_err}")
            return False

    def execute_many_query(self, query, params_list, commit=False):
        try:
            cursor = self.conn.cursor()
            cursor.executemany(query, params_list)
            if commit:
                self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error during executemany: {query[:100]}... - Error: {e}", exc_info=True)
            if commit:
                try:
                    self.conn.rollback()
                except sqlite3.Error as rb_err:
                    logger.error(f"Rollback failed: {rb_err}")
            return False

    def close_connection(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

db_manager = DatabaseManager()
