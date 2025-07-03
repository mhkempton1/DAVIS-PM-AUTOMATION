import hashlib
import logging
import os # Keep for test block path joining
from configuration import Config
from database_manager import db_manager # Import the singleton

# Set up logging for the User Management Module
# BasicConfig is now handled in main.py for the application.
# Modules should just get their logger instance.
logger = logging.getLogger(__name__)

class UserManagement:
    """
    Handles user authentication, authorization, and role-based access control (RBAC).
    Manages user creation, role assignment, and login using the centralized DatabaseManager.
    """
    def __init__(self, db_m_instance=None):
        """
        Initializes the UserManagement module.
        The 'users' table and default admin are expected to be initialized
        by the DatabaseManager when it's first instantiated.
        """
        self.db_manager = db_m_instance if db_m_instance else db_manager
        logger.info("UserManagement module initialized with db_manager.")
        pass

    # _get_db_connection method is removed as db_manager handles connections.
    # self.db_path is no longer needed.

    # def _initialize_db(self): # This method is no longer needed.
    #     """
    #     Initializes the database by creating the 'users' table if it doesn't exist,
    #     and creates a default admin user if no users are present.
    #     Uses db_manager for database operations.
    #     """
    #     create_table_query = '''
    #         CREATE TABLE IF NOT EXISTS users (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             username TEXT NOT NULL UNIQUE,
    #             password_hash TEXT NOT NULL,
    #             role TEXT NOT NULL
    #         )
    #     '''
    #     if not db_manager.execute_query(create_table_query, commit=True):
    #         logger.critical("Failed to create or verify 'users' table.")
    #         # Depending on desired behavior, could raise an exception here.
    #         return # Stop initialization if table creation fails

    #     logger.info("User table checked/created successfully via db_manager.")

    #     count_query = "SELECT COUNT(*) as count FROM users"
    #     result = db_manager.execute_query(count_query, fetch_one=True)

    #     if result and result['count'] == 0:
    #         # Check if admin user already exists before attempting to create
    #         # This is a secondary check; db_manager should handle primary creation
    #         admin_username_check = Config.get_default_admin_credentials()[0]
    #         existing_admin = db_manager.execute_query("SELECT id FROM users WHERE username = ?", (admin_username_check,), fetch_one=True)
    #         if not existing_admin:
    #             admin_user, admin_pass = Config.get_default_admin_credentials()
    #             # Call create_user which now directly uses db_manager
    #             # This part of logic is primarily handled by database_manager.py's _create_users_table_and_default_admin
    #             # This was a fallback, which is now less critical.
    #             # For simplicity and to rely on db_manager, this explicit creation can be removed too.
    #             # If we keep it, it acts as a double check but create_user handles duplicates.
    #             logger.info(f"UserManagement: Attempting to ensure default admin user '{admin_user}' exists if db_manager didn't create it.")
    #             # success, msg = self.create_user(admin_user, admin_pass, 'admin') # create_user defined below
    #             # if success:
    #             #     logger.info(f"UserManagement: Default admin user '{admin_user}' ensured/created.")
    #             # else:
    #             #     logger.error(f"UserManagement: Failed to ensure/create default admin user: {msg}")
    #         else:
    #             logger.info(f"UserManagement: Default admin user '{admin_username_check}' already exists, no action needed here.")


    def _hash_password(self, password):
        """Hashes a password using SHA256 for secure storage."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, password, role):
        """
        Creates a new user with the specified username, password, and role.
        Returns:
            tuple: (bool, str) indicating success and a message.
        """
        if role not in Config.get_role_permissions():
            logger.warning(f"Attempted to create user '{username}' with invalid role '{role}'.")
            return False, "Invalid role specified."

        password_hash = self._hash_password(password)
        insert_query = "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)"

        try:
            # db_manager.execute_query returns True on successful commit
            success = self.db_manager.execute_query(insert_query, (username, password_hash, role), commit=True)
            if success:
                logger.info(f"User '{username}' created with role '{role}'.")
                return True, f"User '{username}' created successfully."
            else:
                # This path might be taken if the commit failed for some reason other than IntegrityError
                logger.error(f"Failed to create user '{username}' due to commit failure or other DB error.")
                return False, "Failed to create user due to a database error."
        except Exception as e:
            # Catching general exception, but IntegrityError for UNIQUE constraint is common
            # db_manager.execute_query itself logs sqlite3.Error.
            # We can make this more specific if db_manager re-raises specific errors or returns error codes.
            # For now, assume execute_query might return False or None for IntegrityError if not committed.
            # A more robust way would be for db_manager to return specific error indicators.
            logger.error(f"Error creating user '{username}': {e}. This might be due to username already existing.")
            # Check if user exists to provide a more specific message
            existing_user = self.db_manager.execute_query("SELECT id FROM users WHERE username = ?", (username,), fetch_one=True)
            if existing_user:
                 return False, "Username already exists."
            return False, f"An error occurred: {e}"


    def authenticate_user(self, username, password):
        """
        Authenticates a user by checking their username and password.
        Returns the user's role if authentication is successful, None otherwise.
        """
        password_hash = self._hash_password(password)
        query = "SELECT role FROM users WHERE username = ? AND password_hash = ?"
        result = self.db_manager.execute_query(query, (username, password_hash), fetch_one=True)

        if result:
            logger.info(f"User '{username}' authenticated successfully with role '{result['role']}'.")
            return result['role']
        else:
            logger.warning(f"Authentication failed for user '{username}'.")
            return None

    def get_user_role(self, username):
        """
        Retrieves the role of a given user.
        """
        query = "SELECT role FROM users WHERE username = ?"
        result = self.db_manager.execute_query(query, (username,), fetch_one=True)
        return result['role'] if result else None

    def get_all_users(self):
        """
        Retrieves all users and their roles.
        Returns a list of dictionaries, or None if an error occurs.
        """
        query = "SELECT username, role FROM users"
        # fetch_all returns a list of Row objects or None on error
        results = self.db_manager.execute_query(query, fetch_all=True)
        if results is None: # Error occurred in db_manager
            return [] # Return empty list to signify failure or no users
        return [dict(row) for row in results] # Convert Row objects to dicts

    def update_user_role(self, username, new_role):
        """
        Updates the role of an existing user.
        Returns:
            tuple: (bool, str) indicating success and a message.
        """
        if new_role not in Config.get_role_permissions():
            logger.warning(f"Attempted to update user '{username}' with invalid role '{new_role}'.")
            return False, "Invalid role specified."

        query = "UPDATE users SET role = ? WHERE username = ?"
        # Check if user exists first, then update
        check_user_query = "SELECT id FROM users WHERE username = ?"
        user_exists = self.db_manager.execute_query(check_user_query, (username,), fetch_one=True)

        if not user_exists:
            logger.warning(f"User '{username}' not found for role update.")
            return False, f"User '{username}' not found."

        success = self.db_manager.execute_query(query, (new_role, username), commit=True)
        if success:
            logger.info(f"Role for user '{username}' updated to '{new_role}'.")
            return True, f"Role for '{username}' updated to '{new_role}'."
        else:
            logger.error(f"Failed to update role for user '{username}' due to a database error.")
            return False, "Failed to update role due to a database error."

    def delete_user(self, username):
        """
        Deletes a user from the system.
        Returns:
            tuple: (bool, str) indicating success and a message.
        """
        # Check if user exists first
        check_user_query = "SELECT id FROM users WHERE username = ?"
        user_exists = self.db_manager.execute_query(check_user_query, (username,), fetch_one=True)

        if not user_exists:
            logger.warning(f"User '{username}' not found for deletion.")
            return False, f"User '{username}' not found."

        query = "DELETE FROM users WHERE username = ?"
        success = self.db_manager.execute_query(query, (username,), commit=True)

        if success:
            logger.info(f"User '{username}' deleted successfully.")
            return True, f"User '{username}' deleted successfully."
        else:
            logger.error(f"Failed to delete user '{username}' due to a database error.")
            return False, "Failed to delete user due to a database error."

    def check_access(self, role, module_name):
        """
        Checks if a given role has access to a specific module.
        """
        if not role: # Handle cases where role might be None (e.g., user not found)
            logger.warning(f"Access check failed: Role is None for module '{module_name}'.")
            return False
        allowed_modules = Config.get_role_permissions().get(role, [])
        has_access = module_name in allowed_modules
        if not has_access:
            logger.warning(f"Access denied: Role '{role}' cannot access module '{module_name}'.")
        return has_access

    def change_user_password(self, username, new_password):
        """
        Changes the password for a given user.
        Returns:
            tuple: (bool, str) indicating success and a message.
        """
        # Check if user exists
        check_user_query = "SELECT id FROM users WHERE username = ?"
        user_exists = self.db_manager.execute_query(check_user_query, (username,), fetch_one=True)

        if not user_exists:
            logger.warning(f"User '{username}' not found for password change.")
            return False, f"User '{username}' not found."

        new_password_hash = self._hash_password(new_password)
        update_query = "UPDATE users SET password_hash = ? WHERE username = ?"

        success = self.db_manager.execute_query(update_query, (new_password_hash, username), commit=True)
        if success:
            logger.info(f"Password for user '{username}' updated successfully.")
            return True, f"Password for '{username}' updated successfully."
        else:
            logger.error(f"Failed to update password for user '{username}' due to a database error.")
            return False, "Failed to update password due to a database error."

    def get_user_id_by_username(self, username):
        """
        Retrieves the ID of a given user.
        Returns the user's ID if found, None otherwise.
        """
        query = "SELECT UserID FROM Users WHERE Username = ?" # Assuming 'UserID' and 'Users' from schema
        # The schema uses 'Employees' table with 'EmployeeID' and 'WorkEmail' as username
        # Let's adjust to the actual schema:
        # schema.sql uses 'Employees' table, with 'EmployeeID' and 'WorkEmail' (or 'Username' if we map it).
        # The 'users' table in UserManagement's own _initialize_db was simpler.
        # Given the current main.py uses UserManagement().authenticate_user(username, password),
        # 'username' here refers to the 'users.username' column.
        # The main schema's 'Employees' table has 'AccessRoleID' but not a direct 'username'/'password' for app login.
        # The app uses its own 'users' table for authentication (username, password_hash, role).
        # This 'users' table was defined in UserManagement._initialize_db and is now in database_manager._create_users_table_and_default_admin
        # So, the query should be against this 'users' table. The schema has 'id' as PK for 'users' table.

        query = "SELECT id FROM users WHERE username = ?" # Corrected for the app's 'users' table
        result = self.db_manager.execute_query(query, (username,), fetch_one=True)
        if result:
            return result['id']
        else:
            logger.warning(f"User ID not found for username: {username}")
            return None

    # TODO: Future Enhancement - Link to Detailed Employee Information
    # This section would contain methods to link a user (if they are an employee)
    # to a more detailed employee profile, likely stored in an 'Employees' table
    # as defined in the main schema.sql. This could involve:
    # - A method like `get_employee_details(username)` which checks if the user
    #   is in the 'Employees' table (e.g., by matching `username` to `WorkEmail`)
    #   and returns their full profile.
    # - Modifications to `get_all_users` or a new method to optionally include
    #   a flag or basic employee info if a link exists.

if __name__ == "__main__":
    # This block demonstrates how the UserManagement module can be used.
    # It requires db_manager to be initialized, which usually happens when main.py runs
    # or when database_manager.py is imported for the first time.
    # For standalone testing of user_management.py, ensure db_manager is correctly configured.

    print("--- Testing UserManagement ---")
    # Ensure db_manager is using a test database if needed, or that the main DB is safe for test data.
    # The current db_manager singleton uses Config.DATABASE_PATH by default.
    # For isolated testing, one might temporarily re-assign db_manager.db_path or use a test-specific Config.
    # However, the test block in database_manager.py handles its own test DB.
    # Here, we rely on the global db_manager.

    # It's better if the test setup here ensures a clean state or uses a dedicated test DB.
    # For simplicity, we'll proceed assuming db_manager is available and works with the configured DB.
    # A proper test setup would involve:
    # 1. Setting Config.DATABASE_PATH to a test DB.
    # 2. Re-initializing db_manager with this test path (if db_manager allows re-init or path change).
    # 3. Cleaning up the test DB before/after tests.

    # Since db_manager is a singleton initialized on first import, changing its path post-init is tricky.
    # The original test used 'UserManagement(db_path=test_db_path)' which is now removed.
    # We will assume the `_initialize_db` call in `UserManagement()` handles table creation.

    # Create a UserManagement instance (which calls _initialize_db)
    um = UserManagement()

    # Test create_user
    print("\n--- Creating Users ---")
    success, msg = um.create_user("john_doe_test", "password123", "project_manager")
    print(f"john_doe_test create: {msg} (Success: {success})")

    success, msg = um.create_user("jane_smith_test", "securepass", "estimator")
    print(f"jane_smith_test create: {msg} (Success: {success})")

    # Try creating default admin again to see if it handles duplicates (it should, via create_user logic)
    admin_user, admin_pass = Config.get_default_admin_credentials()
    success, msg = um.create_user(admin_user, admin_pass, "admin") # Attempt to create default admin
    print(f"Default admin '{admin_user}' re-creation attempt: {msg} (Success: {success})")


    success, msg = um.create_user("invalid_role_user_test", "pass", "nonexistent_role")
    print(f"invalid_role_user_test create: {msg} (Success: {success})")

    success, msg = um.create_user("john_doe_test", "anotherpass", "contractor") # Duplicate
    print(f"john_doe_test duplicate create: {msg} (Success: {success})")

    # Test authenticate_user
    print("\n--- Authenticating Users ---")
    role = um.authenticate_user("john_doe_test", "password123")
    print(f"john_doe_test authenticated, role: {role}")
    role = um.authenticate_user("jane_smith_test", "wrongpass")
    print(f"jane_smith_test (wrong pass) authenticated, role: {role}")
    role = um.authenticate_user("non_existent_test", "anypass")
    print(f"non_existent_test authenticated, role: {role}")

    # Test get_all_users
    print("\n--- All Users ---")
    users = um.get_all_users()
    if users:
        for user_dict in users: # users is now a list of dicts
            print(f"User: {user_dict['username']}, Role: {user_dict['role']}")
    else:
        print("No users found or error retrieving users.")

    # Test update_user_role
    print("\n--- Updating User Role ---")
    success, msg = um.update_user_role("john_doe_test", "contractor")
    print(f"Update john_doe_test role: {msg} (Success: {success})")

    updated_users = um.get_all_users()
    if updated_users:
        for user_dict in updated_users:
            if user_dict['username'] == 'john_doe_test':
                print(f"john_doe_test's new role: {user_dict['role']}")

    success, msg = um.update_user_role("non_existent_test", "project_manager")
    print(f"Update non_existent_test role: {msg} (Success: {success})")

    # Test check_access
    print("\n--- Checking Access ---")
    print(f"Admin can access 'integration': {um.check_access('admin', 'integration')}")
    print(f"Project Manager can access 'user_management': {um.check_access('project_manager', 'user_management')}") # Should be False
    print(f"John Doe (now contractor) can access 'project_planning': {um.check_access('contractor', 'project_planning')}") # Should be False by default PM permissions

    # Test delete_user
    print("\n--- Deleting Users (Test Data) ---")
    success, msg = um.delete_user("jane_smith_test")
    print(f"Delete jane_smith_test: {msg} (Success: {success})")
    success, msg = um.delete_user("john_doe_test")
    print(f"Delete john_doe_test: {msg} (Success: {success})")
    # Deleting default admin if it was created by this test run and not by a previous one.
    # Be cautious with this in a shared dev environment.
    # success, msg = um.delete_user(Config.DEFAULT_ADMIN_USERNAME)
    # print(f"Delete default admin '{Config.DEFAULT_ADMIN_USERNAME}': {msg} (Success: {success})")


    print("\n--- All Users After Test Deletions ---")
    final_users = um.get_all_users()
    if final_users:
        for user_dict in final_users:
            print(f"User: {user_dict['username']}, Role: {user_dict['role']}")
    else:
        print("No users found or error retrieving users.")

    print("\nNote: For full standalone testing of user_management.py, ensure the database (e.g., project_data.db) is in a known state or use a dedicated test database by configuring Config.DATABASE_PATH and re-initializing db_manager if possible before running this test script.")
