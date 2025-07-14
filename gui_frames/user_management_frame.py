import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
from .base_frame import BaseModuleFrame
from configuration import Config
from exceptions import AppValidationError, AppOperationConflictError, AppDatabaseError, AppError # Added AppError
import constants # Added
import logging

logger = logging.getLogger(__name__)

class UserManagementModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_username_entry = None
        self.create_password_entry = None
        self.create_role_combo = None
        self.create_employee_link_combo = None # New
        self.manage_username_entry = None
        self.update_role_combo = None
        self.manage_employee_link_combo = None # New
        self.unlinked_employees_map = {} # To map display name to EmployeeID

        self.create_widgets()
        self.load_unlinked_employees_for_combos()

    def create_widgets(self):
        tk.Label(self, text="User Management Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # --- Create New User Frame ---
        create_frame = ttk.LabelFrame(self, text="Create New User")
        create_frame.pack(pady=5, padx=20, fill="x")
        create_frame.columnconfigure(1, weight=1)

        tk.Label(create_frame, text="Username:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.create_username_entry = tk.Entry(create_frame)
        self.create_username_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(create_frame, text="Password:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.create_password_entry = tk.Entry(create_frame, show="*")
        self.create_password_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(create_frame, text="Role:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.create_role_combo = ttk.Combobox(create_frame, values=list(Config.ROLE_PERMISSIONS.keys()), state="readonly")
        self.create_role_combo.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        if Config.ROLE_PERMISSIONS.keys():
            self.create_role_combo.set(list(Config.ROLE_PERMISSIONS.keys())[0])

        tk.Label(create_frame, text="Link to Employee:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.create_employee_link_combo = ttk.Combobox(create_frame, state="readonly")
        self.create_employee_link_combo.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        # Populate later with load_unlinked_employees_for_combos

        ttk.Button(create_frame, text="Create User", command=self.create_user_action).grid(row=4, column=0, columnspan=2, pady=10)

        # --- Manage Existing Users Frame ---
        manage_frame = ttk.LabelFrame(self, text="Manage Existing User")
        manage_frame.pack(pady=5, padx=20, fill="x")
        manage_frame.columnconfigure(1, weight=1)

        tk.Label(manage_frame, text="Username (for lookup):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.manage_username_entry = tk.Entry(manage_frame)
        self.manage_username_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Button(manage_frame, text="Load User Details", command=self.load_user_details_for_management).grid(row=0, column=2, padx=5, pady=2)


        tk.Label(manage_frame, text="New Role:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.update_role_combo = ttk.Combobox(manage_frame, values=list(Config.ROLE_PERMISSIONS.keys()), state="readonly")
        self.update_role_combo.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        if Config.ROLE_PERMISSIONS.keys():
             self.update_role_combo.set(list(Config.ROLE_PERMISSIONS.keys())[0])

        tk.Label(manage_frame, text="Link to Employee:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.manage_employee_link_combo = ttk.Combobox(manage_frame, state="readonly")
        self.manage_employee_link_combo.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        # Populate later

        management_buttons_frame = ttk.Frame(manage_frame)
        management_buttons_frame.grid(row=3, column=0, columnspan=3, pady=5) # Changed to columnspan 3
        ttk.Button(management_buttons_frame, text="Update User Details", command=self.update_user_details_action).pack(side="left", padx=5)
        ttk.Button(management_buttons_frame, text="Delete User", command=self.delete_user_action).pack(side="left", padx=5)
        ttk.Button(management_buttons_frame, text="Change Password", command=self.change_password_action).pack(side="left", padx=5)

        ttk.Button(manage_frame, text="List All Users", command=self.list_users_action).grid(row=4, column=0, columnspan=3, pady=5)
        ttk.Button(manage_frame, text="Refresh Employee Lists", command=self.load_unlinked_employees_for_combos).grid(row=4, column=2, padx=5, pady=2, sticky="e")


    def load_unlinked_employees_for_combos(self):
        self.unlinked_employees_map = {} # Reset map
        employee_display_list = ["(None - Unlinked)"] # Option to explicitly unlink or not link

        if self.module_instance and hasattr(self.module_instance, 'get_unlinked_employees'):
            unlinked_employees = self.module_instance.get_unlinked_employees()
            if unlinked_employees:
                for emp in unlinked_employees:
                    display_name = f"{emp['FirstName']} {emp['LastName']} (ID: {emp['EmployeeID']})"
                    self.unlinked_employees_map[display_name] = emp['EmployeeID']
                    employee_display_list.append(display_name)

        self.create_employee_link_combo['values'] = employee_display_list
        self.create_employee_link_combo.set(employee_display_list[0])

        # For managing existing users, the list might need to include the currently linked employee too
        # This will be handled by load_user_details_for_management
        self.manage_employee_link_combo['values'] = employee_display_list
        self.manage_employee_link_combo.set(employee_display_list[0])


    def load_user_details_for_management(self):
        username = self.manage_username_entry.get().strip()
        if not username:
            self.show_message("Input Error", "Please enter a username to load details.", True)
            return

        if not self.module_instance or not hasattr(self.module_instance, 'get_user_details_by_username'):
            self.show_message("Error", "User Management module not available.", True)
            return

        user_details = self.module_instance.get_user_details_by_username(username)
        if not user_details:
            self.show_message("Not Found", f"User '{username}' not found.", True)
            self.update_role_combo.set(list(Config.ROLE_PERMISSIONS.keys())[0] if Config.ROLE_PERMISSIONS.keys() else "")
            self.manage_employee_link_combo.set("(None - Unlinked)")
            return

        self.update_role_combo.set(user_details.get('role', ''))

        # Populate manage_employee_link_combo
        # It should contain unlinked employees + the currently linked one (if any)
        current_linked_employee_id = user_details.get('employee_db_id')
        employee_display_list_manage = ["(None - Unlinked)"]
        temp_map_manage = {"(None - Unlinked)": None}

        if self.module_instance and hasattr(self.module_instance, 'get_unlinked_employees'):
            unlinked_employees = self.module_instance.get_unlinked_employees()
            if unlinked_employees:
                for emp in unlinked_employees:
                    display_name = f"{emp['FirstName']} {emp['LastName']} (ID: {emp['EmployeeID']})"
                    temp_map_manage[display_name] = emp['EmployeeID']
                    employee_display_list_manage.append(display_name)

        current_selection = "(None - Unlinked)"
        if current_linked_employee_id is not None:
            # Fetch details of the currently linked employee to display them
            # This requires a method like get_employee_details(employee_id) in backend or direct query
            # For simplicity, if linked, we try to find it in the main employee list or just show ID
            # Assuming EmployeeID is enough for now, or we need another backend call
            linked_emp_display = f"Currently Linked: EmployeeID {current_linked_employee_id}"

            # If this employee ID is NOT in the unlinked list, add it specially
            is_current_emp_in_list = any(emp_id == current_linked_employee_id for emp_id in temp_map_manage.values())

            if not is_current_emp_in_list:
                 # Need to fetch this employee's name to make it user-friendly
                 # This ideally comes from a backend method like `get_employee_by_id`
                 # Placeholder:
                 # emp_details = self.module_instance.get_employee_details(current_linked_employee_id)
                 # if emp_details: linked_emp_display = f"{emp_details['FirstName']} {emp_details['LastName']} (ID: {current_linked_employee_id})"
                if current_linked_employee_id not in temp_map_manage.values(): # Add if not already (e.g. if they were unlinked by another admin)
                    employee_display_list_manage.append(linked_emp_display) # Add display for current
                    temp_map_manage[linked_emp_display] = current_linked_employee_id
                current_selection = linked_emp_display

        self.manage_employee_link_combo['values'] = employee_display_list_manage
        self.unlinked_employees_map = temp_map_manage # Update map for this combo
        self.manage_employee_link_combo.set(current_selection)

        self.show_message("User Details", f"Details for '{username}' loaded. Current Role: {user_details.get('role')}, Linked EmployeeID: {current_linked_employee_id or 'None'}.")


    def create_user_action(self):
        if not self.module_instance: self.show_message("Error", "User Management module not available.", True); return

        username = self.create_username_entry.get().strip()
        password = self.create_password_entry.get().strip()
        role = self.create_role_combo.get().strip()

        selected_employee_display = self.create_employee_link_combo.get()
        employee_id_to_link = self.unlinked_employees_map.get(selected_employee_display) # Will be None if "(None - Unlinked)"

        if not username or not password or not role:
            self.show_message("Input Error", "Username, Password, and Role are required.", True)
            return

        try:
            # Assuming create_user now might return (True, message) on success,
            # or raise AppError on failure.
            success, msg = self.module_instance.create_user(username, password, role, employee_id=employee_id_to_link)
            self.show_message("Create User", msg, is_error=not success) # is_error based on success flag
            if success:
                self.create_username_entry.delete(0, tk.END)
                self.create_password_entry.delete(0, tk.END)
                if Config.ROLE_PERMISSIONS.keys(): self.create_role_combo.set(list(Config.ROLE_PERMISSIONS.keys())[0])
                self.load_unlinked_employees_for_combos() # Refresh employee list
        except (AppValidationError, AppOperationConflictError, AppDatabaseError) as ae:
            logger.error(f"Error creating user '{username}': {ae}", exc_info=True)
            self.show_message("Create User Error", str(ae), is_error=True)
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Unexpected error creating user '{username}': {e}", exc_info=True)
            self.show_message("System Error", "An unexpected error occurred during user creation. Check logs.", is_error=True)


    def update_user_details_action(self):
        """Handles updating role and employee link."""
        if not self.module_instance:
            self.show_message("Error", "User Management module not available.", True)
            return

        username = self.manage_username_entry.get().strip()
        if not username:
            self.show_message("Input Error", "Username is required to update details.", True)
            return

        new_role = self.update_role_combo.get().strip()
        selected_employee_display = self.manage_employee_link_combo.get()
        employee_id_to_link = self.unlinked_employees_map.get(selected_employee_display)

        try:
            current_user_details = self.module_instance.get_user_details_by_username(username)
            if not current_user_details:
                self.show_message("Error", f"User '{username}' not found.", True)
                return

            role_updated_success, role_msg = True, "Role not changed."
            if new_role and new_role != current_user_details.get('role'):
                role_updated_success, role_msg = self.module_instance.update_user_role(username, new_role)

            link_updated_success, link_msg = True, "Link not changed."
            if employee_id_to_link != current_user_details.get('employee_db_id'):
                link_updated_success, link_msg = self.module_instance.update_user_employee_link(username, employee_id_to_link)

            if role_updated_success and link_updated_success:
                self.show_message("Update User", f"Successfully updated user '{username}'.")
                self.manage_username_entry.delete(0, tk.END)
                self.update_role_combo.set('')
                self.manage_employee_link_combo.set('')
                self.load_unlinked_employees_for_combos()
            else:
                error_messages = []
                if not role_updated_success:
                    error_messages.append(f"Role update failed: {role_msg}")
                if not link_updated_success:
                    error_messages.append(f"Link update failed: {link_msg}")
                self.show_message("Update User Error", "\n".join(error_messages), is_error=True)

        except AppError as ae:
            logger.error(f"Error updating user '{username}': {ae}", exc_info=True)
            self.show_message("Update User Error", str(ae), is_error=True)
        except Exception as e:
            logger.error(f"Unexpected error updating user '{username}': {e}", exc_info=True)
            self.show_message("System Error", "An unexpected error occurred. Check logs.", is_error=True)


    def delete_user_action(self):
        if not self.module_instance: self.show_message("Error", "User Management module not available.", True); return
        username = self.manage_username_entry.get().strip()
        if not username:
            self.show_message("Input Error", "Username is required for deletion.", True)
            return
        if username.lower() == Config.DEFAULT_ADMIN_USERNAME.lower() and username.lower() != "admin_test_user_to_delete":
             self.show_message("Action Denied", "Default admin user cannot be deleted this way.", True)
             return

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete user '{username}'?", parent=self):
            try:
                success, msg = self.module_instance.delete_user(username) # Assumes delete_user might still return tuple
                self.show_message("Delete User", msg, is_error=not success)
                if success:
                    self.manage_username_entry.delete(0, tk.END)
                    self.load_unlinked_employees_for_combos()
            except AppError as ae:
                logger.error(f"Error deleting user '{username}': {ae}", exc_info=True)
                self.show_message("Delete User Error", str(ae), is_error=True)
            except Exception as e:
                logger.error(f"Unexpected error deleting user '{username}': {e}", exc_info=True)
                self.show_message("System Error", "An unexpected error occurred. Check logs.", is_error=True)

    def change_password_action(self):
        if self.app.current_user_role != constants.ROLE_ADMIN:
            self.show_message("Access Denied", "Only administrators can change passwords.", True)
            return

        username = simpledialog.askstring("Change Password", "Enter username for password change:", parent=self)
        if not username: return

        if not self.module_instance or not hasattr(self.module_instance, 'change_user_password'):
            self.show_message("Error", "User Management module not available for password change.", True)
            return

        new_password = simpledialog.askstring("Change Password", f"Enter new password for {username}:", show='*', parent=self)
        if not new_password: return
        confirm_password = simpledialog.askstring("Change Password", "Confirm new password:", show='*', parent=self)
        if not confirm_password: return

        if new_password != confirm_password:
            self.show_message("Error", "Passwords do not match.", True) # GUI validation
            return

        try:
            # Assuming change_user_password might still return (True, msg) or raise AppError
            success, msg = self.module_instance.change_user_password(username, new_password)
            self.show_message("Change Password", msg, is_error=not success)
        except AppError as ae:
            logger.error(f"Error changing password for '{username}': {ae}", exc_info=True)
            self.show_message("Change Password Error", str(ae), is_error=True)
        except Exception as e:
            logger.error(f"Unexpected error changing password for '{username}': {e}", exc_info=True)
            self.show_message("System Error", "An unexpected error occurred. Check logs.", is_error=True)


    def list_users_action(self):
        # ... (implementation remains similar, ensure self.module_instance check) ...
        if not self.module_instance or not hasattr(self.module_instance, 'get_all_users'):
            self.show_message("Error","User Management module not available.", True); return
        users_data = self.module_instance.get_all_users()
        if users_data:
            df_users = pd.DataFrame(users_data)
            # Select and rename columns for better display
            df_display = df_users[['username', 'role', 'EmployeeID', 'FirstName', 'LastName']].copy()
            df_display.rename(columns={
                'username': 'Username', 'role': 'App Role',
                'EmployeeID': 'Linked Emp. ID',
                'FirstName': 'Emp. First Name', 'LastName': 'Emp. Last Name'
            }, inplace=True)
            self.display_dataframe(df_display, "All Application Users")
        else:
            self.show_message("No Users", "No users found or error fetching them.")
