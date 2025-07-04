import hashlib
import logging
import os
import sqlite3 # For specific error handling like IntegrityError

from configuration import Config
from database_manager import db_manager

logger = logging.getLogger(__name__)


class UserManagement:
    """
    Handles user authentication, authorization, and role-based access control (RBAC).
    Also manages linking app users to Employee records.
    """

    def __init__(self, db_m_instance=None):
        """Initializes the UserManagement module."""
        self.db_manager = db_m_instance if db_m_instance else db_manager
        logger.info("UserManagement module initialized with db_manager.")

    def _hash_password(self, password):
        """Hashes a password using SHA256 for secure storage."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, password, role, employee_id=None):
        """
        Creates a new user with username, password, role, and optional EmployeeID.
        Returns: tuple (bool, str) indicating success and a message.
        """
        if role not in Config.get_role_permissions():
            logger.warning(f"Attempted to create user '{username}' with invalid role '{role}'.")
            return False, "Invalid role specified."

        if employee_id is not None:
            try:
                employee_id = int(employee_id) # Ensure it's an int
                emp_exists_query = "SELECT EmployeeID FROM Employees WHERE EmployeeID = ?"
                if not self.db_manager.execute_query(emp_exists_query, (employee_id,), fetch_one=True):
                    logger.warning(f"Attempt to create user '{username}' with non-existent EmployeeID {employee_id}.")
                    return False, f"EmployeeID {employee_id} does not exist in Employees table."

                emp_linked_query = "SELECT username FROM users WHERE EmployeeID = ?"
                existing_link = self.db_manager.execute_query(emp_linked_query, (employee_id,), fetch_one=True)
                if existing_link:
                    logger.warning(f"EmployeeID {employee_id} is already linked to user '{existing_link['username']}'.")
                    return False, f"EmployeeID {employee_id} is already linked to another user."
            except ValueError:
                 logger.warning(f"Invalid EmployeeID format for user '{username}': {employee_id}.")
                 return False, "EmployeeID must be a valid number."
            except Exception as e_val:
                logger.error(f"Error validating EmployeeID for user '{username}': {e_val}", exc_info=True)
                return False, f"Error validating EmployeeID: {e_val}"

        password_hash = self._hash_password(password)
        insert_query = "INSERT INTO users (username, password_hash, role, EmployeeID) VALUES (?, ?, ?, ?)"

        try:
            success_cursor = self.db_manager.execute_query(
                insert_query, (username, password_hash, role, employee_id), commit=True
            )
            if success_cursor:
                logger.info(f"User '{username}' created with role '{role}' and EmployeeID {employee_id}.")
                return True, f"User '{username}' created successfully."
            else:
                logger.error(f"Failed to create user '{username}'. Check logs for DB error.")
                existing_user_check = self.db_manager.execute_query(
                    "SELECT id FROM users WHERE username = ?", (username,), fetch_one=True
                )
                if existing_user_check:
                    return False, "Username already exists."
                return False, "Failed to create user due to a database error."
        except sqlite3.IntegrityError as ie:
             logger.error(f"Integrity error creating user '{username}': {ie}", exc_info=True)
             if "UNIQUE constraint failed: users.username" in str(ie):
                 return False, "Username already exists."
             if "FOREIGN KEY constraint failed" in str(ie) and employee_id is not None:
                 return False, f"Invalid EmployeeID {employee_id} or foreign key constraint violation."
             return False, f"Database integrity error: {ie}"
        except Exception as e:
            logger.error(f"Unexpected exception creating user '{username}': {e}", exc_info=True)
            return False, f"An unexpected error occurred: {e}"

    def authenticate_user(self, username, password):
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
        query = "SELECT role FROM users WHERE username = ?"
        result = self.db_manager.execute_query(query, (username,), fetch_one=True)
        return result['role'] if result else None

    def get_all_users(self):
        query = "SELECT u.id, u.username, u.role, u.EmployeeID, e.FirstName, e.LastName FROM users u LEFT JOIN Employees e ON u.EmployeeID = e.EmployeeID ORDER BY u.username"
        results = self.db_manager.execute_query(query, fetch_all=True)
        return [dict(row) for row in results] if results else []

    def update_user_role(self, username, new_role):
        if new_role not in Config.get_role_permissions():
            return False, "Invalid role specified."
        user_details = self.get_user_details_by_username(username)
        if not user_details:
            return False, f"User '{username}' not found."

        query = "UPDATE users SET role = ? WHERE username = ?"
        success = self.db_manager.execute_query(query, (new_role, username), commit=True)
        if success:
            return True, f"Role for '{username}' updated to '{new_role}'."
        return False, "Failed to update role."

    def update_user_employee_link(self, username, employee_id):
        """Links or unlinks an app user to an EmployeeID."""
        user_details = self.get_user_details_by_username(username)
        if not user_details:
            return False, f"User '{username}' not found."

        app_user_id = user_details['app_user_id']

        if employee_id is not None:
            try:
                employee_id = int(employee_id)
                emp_exists_query = "SELECT EmployeeID FROM Employees WHERE EmployeeID = ?"
                if not self.db_manager.execute_query(emp_exists_query, (employee_id,), fetch_one=True):
                    return False, f"EmployeeID {employee_id} does not exist."

                # Check if this EmployeeID is already linked to another app user
                emp_linked_query = "SELECT username FROM users WHERE EmployeeID = ? AND id != ?"
                existing_link = self.db_manager.execute_query(emp_linked_query, (employee_id, app_user_id), fetch_one=True)
                if existing_link:
                    return False, f"EmployeeID {employee_id} is already linked to user '{existing_link['username']}'."
            except ValueError:
                return False, "EmployeeID must be a valid number."
            except Exception as e_val:
                logger.error(f"Error validating EmployeeID for linking user '{username}': {e_val}", exc_info=True)
                return False, f"Error validating EmployeeID: {e_val}"

        query = "UPDATE users SET EmployeeID = ? WHERE id = ?"
        success = self.db_manager.execute_query(query, (employee_id, app_user_id), commit=True)
        if success:
            action = f"linked to EmployeeID {employee_id}" if employee_id is not None else "unlinked from Employee record"
            logger.info(f"User '{username}' (AppUserID: {app_user_id}) {action}.")
            return True, f"User '{username}' successfully {action}."
        return False, f"Failed to update EmployeeID link for user '{username}'."

    def delete_user(self, username):
        # ... (implementation remains similar) ...
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
            logger.error(f"Failed to delete user '{username}'.")
            return False, "Failed to delete user due to a database error."


    def check_access(self, role, module_name):
        # ... (implementation remains similar) ...
        if not role:
            logger.warning(f"Access check failed: Role is None for module '{module_name}'.")
            return False
        allowed_modules = Config.get_role_permissions().get(role, [])
        has_access = module_name in allowed_modules
        if not has_access:
            logger.debug(f"Access denied: Role '{role}' cannot access module '{module_name}'.")
        return has_access

    def change_user_password(self, username, new_password):
        # ... (implementation remains similar) ...
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
            logger.error(f"Failed to update password for user '{username}'.")
            return False, "Failed to update password due to a database error."

    def get_user_details_by_username(self, username):
        query = "SELECT id, EmployeeID, role, username FROM users WHERE username = ?" # Added role, username
        result = self.db_manager.execute_query(query, (username,), fetch_one=True)
        if result:
            return {
                'app_user_id': result['id'],
                'employee_db_id': result['EmployeeID'],
                'role': result['role'], # Good to have role here too
                'username': result['username']
            }
        else:
            logger.warning(f"User details not found for username: {username}")
            return None

    def get_unlinked_employees(self):
        """
        Retrieves a list of employees (EmployeeID, FirstName, LastName)
        who are not currently linked to any app user in the 'users' table.
        """
        query = """
        SELECT e.EmployeeID, e.FirstName, e.LastName
        FROM Employees e
        LEFT JOIN users u ON e.EmployeeID = u.EmployeeID
        WHERE u.EmployeeID IS NULL
        ORDER BY e.LastName, e.FirstName;
        """
        results = self.db_manager.execute_query(query, fetch_all=True)
        return [dict(row) for row in results] if results else []

    # get_employee_id_for_app_user can be removed or kept if used internally,
    # but get_user_details_by_username is now preferred.
    # For now, I'll keep it but note its deprecation.
    def get_employee_id_for_app_user(self, app_username):
        """DEPRECATED: Use get_user_details_by_username instead."""
        logger.warning("get_employee_id_for_app_user is deprecated. Use get_user_details_by_username.")
        details = self.get_user_details_by_username(app_username)
        return details['employee_db_id'] if details else None


if __name__ == "__main__":
    print("--- Testing UserManagement ---")
    um = UserManagement()

    try:
        db_manager.execute_query("INSERT OR IGNORE INTO Employees (EmployeeID, FirstName, LastName, WorkEmail) VALUES (1, 'Test', 'Emp', 'testemp@example.com')")
        db_manager.execute_query("INSERT OR IGNORE INTO Employees (EmployeeID, FirstName, LastName, WorkEmail) VALUES (2, 'Another', 'Emp', 'another@example.com')")
        db_manager.execute_query("INSERT OR IGNORE INTO Employees (EmployeeID, FirstName, LastName, WorkEmail) VALUES (3, 'Unlinked', 'User', 'unlinked@example.com')")
        db_manager.conn.commit()
    except Exception as e:
        print(f"Could not ensure test employees: {e}")

    print("\n--- Creating Users ---")
    # ... (create_user tests updated to include employee_id)
    um.create_user("john_doe_test", "password123", "project_manager", 1)
    um.create_user("jane_smith_test", "securepass", "estimator", None)
    # ...

    print("\n--- Listing Unlinked Employees ---")
    unlinked_emps = um.get_unlinked_employees()
    if unlinked_emps:
        print(f"Found {len(unlinked_emps)} unlinked employees:")
        for emp in unlinked_emps:
            print(f"  ID: {emp['EmployeeID']}, Name: {emp['FirstName']} {emp['LastName']}")
    else:
        print("No unlinked employees found.")

    print("\n--- Linking User to Employee ---")
    # Assuming jane_smith_test exists and EmployeeID 2 exists and is unlinked
    details_jane_before = um.get_user_details_by_username("jane_smith_test")
    if details_jane_before:
        print(f"Jane Smith before link: {details_jane_before}")
        success_link, msg_link = um.update_user_employee_link("jane_smith_test", 2)
        print(f"Linking Jane Smith to EmployeeID 2: {msg_link} (Success: {success_link})")
        details_jane_after = um.get_user_details_by_username("jane_smith_test")
        print(f"Jane Smith after link: {details_jane_after}")

    print("\n--- Listing Unlinked Employees (After Link) ---")
    unlinked_emps_after = um.get_unlinked_employees()
    if unlinked_emps_after:
        print(f"Found {len(unlinked_emps_after)} unlinked employees:")
        for emp in unlinked_emps_after:
            print(f"  ID: {emp['EmployeeID']}, Name: {emp['FirstName']} {emp['LastName']}")
    else:
        print("No unlinked employees found.")

    print("\n--- Unlinking User from Employee ---")
    success_unlink, msg_unlink = um.update_user_employee_link("jane_smith_test", None) # Pass None to unlink
    print(f"Unlinking Jane Smith: {msg_unlink} (Success: {success_unlink})")
    details_jane_unlinked = um.get_user_details_by_username("jane_smith_test")
    print(f"Jane Smith after unlink: {details_jane_unlinked}")


    # ... (rest of __main__ tests) ...
    print("\n--- All Users (with EmployeeID) ---")
    all_users = um.get_all_users()
    if all_users:
        for user_dict in all_users:
            print(f"User: {user_dict['username']}, Role: {user_dict['role']}, AppUserID: {user_dict['id']}, Linked EmployeeID: {user_dict['EmployeeID']}, EmployeeName: {user_dict.get('FirstName')} {user_dict.get('LastName')}")
    else:
        print("No users found or error retrieving users.")

    print("\n--- Deleting Test Users ---")
    test_users_to_delete = ["john_doe_test", "jane_smith_test", "invalid_role_user_test", "link_fail_user"]
    for user in test_users_to_delete:
        if um.get_user_details_by_username(user):
            success, msg = um.delete_user(user)
            print(f"Delete {user}: {msg} (Success: {success})")
        else:
            print(f"User {user} not found or not created, skipping deletion.")

    print("\nUserManagement testing complete.")
