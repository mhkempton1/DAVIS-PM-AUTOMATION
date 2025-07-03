import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd # For displaying list of users
from .base_frame import BaseModuleFrame
from configuration import Config # For ROLE_PERMISSIONS

# Logger setup
import logging
logger = logging.getLogger(__name__)

class UserManagementModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        # module_instance here will be the UserManagement backend instance
        super().__init__(parent, app, module_instance)

        # Initialize UI attributes
        self.create_username_entry = None
        self.create_password_entry = None
        self.create_role_combo = None
        self.manage_username_entry = None
        self.update_role_combo = None

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="User Management Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # --- Create New User Frame ---
        create_frame = ttk.LabelFrame(self, text="Create New User")
        create_frame.pack(pady=5, padx=20, fill="x")
        create_frame.columnconfigure(1, weight=1) # Make entry fields expand

        tk.Label(create_frame, text="Username:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.create_username_entry = tk.Entry(create_frame)
        self.create_username_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(create_frame, text="Password:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.create_password_entry = tk.Entry(create_frame, show="*")
        self.create_password_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(create_frame, text="Role:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.create_role_combo = ttk.Combobox(create_frame, values=list(Config.ROLE_PERMISSIONS.keys()), state="readonly")
        self.create_role_combo.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        if Config.ROLE_PERMISSIONS.keys(): # Set a default selection
            self.create_role_combo.set(list(Config.ROLE_PERMISSIONS.keys())[0])

        ttk.Button(create_frame, text="Create User", command=self.create_user_action).grid(row=3, column=0, columnspan=2, pady=5)

        # --- Manage Existing Users Frame ---
        manage_frame = ttk.LabelFrame(self, text="Manage Existing Users")
        manage_frame.pack(pady=5, padx=20, fill="x")
        manage_frame.columnconfigure(1, weight=1) # Make entry field expand

        tk.Label(manage_frame, text="Username:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.manage_username_entry = tk.Entry(manage_frame)
        self.manage_username_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        tk.Label(manage_frame, text="New Role:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.update_role_combo = ttk.Combobox(manage_frame, values=list(Config.ROLE_PERMISSIONS.keys()), state="readonly")
        self.update_role_combo.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        if Config.ROLE_PERMISSIONS.keys(): # Set a default selection
             self.update_role_combo.set(list(Config.ROLE_PERMISSIONS.keys())[0])


        buttons_frame = ttk.Frame(manage_frame) # Frame for buttons to be side-by-side
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(buttons_frame, text="Update Role", command=self.update_user_role_action).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Delete User", command=self.delete_user_action).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Change Password", command=self.change_password_action).pack(side="left", padx=5)

        ttk.Button(manage_frame, text="List All Users", command=self.list_users_action).grid(row=3, column=0, columnspan=2, pady=5)

    def change_password_action(self):
        # Ensure current user is admin (this check could also be in backend)
        if self.app.current_user_role != 'admin':
            self.show_message("Access Denied", "Only administrators can change passwords.", True)
            return

        username = simpledialog.askstring("Change Password", "Enter username for password change:", parent=self)
        if not username: return

        new_password = simpledialog.askstring("Change Password", f"Enter new password for {username}:", show='*', parent=self)
        if not new_password: return

        confirm_password = simpledialog.askstring("Change Password", "Confirm new password:", show='*', parent=self)
        if not confirm_password: return

        if new_password != confirm_password:
            self.show_message("Error", "Passwords do not match.", True)
            return

        if self.module and hasattr(self.module, 'change_user_password'):
            # self.module is the UserManagement instance
            success, msg = self.module.change_user_password(username, new_password)
            self.show_message("Change Password", msg, not success)
        else:
            self.show_message("Error", "User Management module or change_user_password method not available.", True)

    def create_user_action(self):
        if not self.module: self.show_message("Error", "User Management module not available.", True); return

        username = self.create_username_entry.get().strip()
        password = self.create_password_entry.get().strip()
        role = self.create_role_combo.get().strip()

        if not username or not password or not role:
            self.show_message("Input Error", "All fields (Username, Password, Role) are required.", True)
            return

        success, msg = self.module.create_user(username, password, role)
        self.show_message("Create User", msg, not success)
        if success:
            self.create_username_entry.delete(0, tk.END)
            self.create_password_entry.delete(0, tk.END)
            # Optionally reset role combo to default
            if Config.ROLE_PERMISSIONS.keys(): self.create_role_combo.set(list(Config.ROLE_PERMISSIONS.keys())[0])


    def update_user_role_action(self):
        if not self.module: self.show_message("Error", "User Management module not available.", True); return

        username = self.manage_username_entry.get().strip()
        new_role = self.update_role_combo.get().strip()

        if not username or not new_role:
            self.show_message("Input Error", "Username and New Role are required.", True)
            return

        success, msg = self.module.update_user_role(username, new_role)
        self.show_message("Update Role", msg, not success)
        if success:
            self.manage_username_entry.delete(0, tk.END)
            # Optionally reset role combo
            if Config.ROLE_PERMISSIONS.keys(): self.update_role_combo.set(list(Config.ROLE_PERMISSIONS.keys())[0])


    def delete_user_action(self):
        if not self.module: self.show_message("Error", "User Management module not available.", True); return

        username = self.manage_username_entry.get().strip()
        if not username:
            self.show_message("Input Error", "Username is required for deletion.", True)
            return

        if username.lower() == 'admin': # Basic protection for default admin
            self.show_message("Action Denied", "Default 'admin' user cannot be deleted through this interface.", True)
            return

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete user '{username}'? This cannot be undone.", parent=self):
            success, msg = self.module.delete_user(username)
            self.show_message("Delete User", msg, not success)
            if success:
                self.manage_username_entry.delete(0, tk.END)
        else:
            self.show_message("Deletion Cancelled", "User deletion cancelled.")

    def list_users_action(self):
        if not self.module: self.show_message("Error", "User Management module not available.", True); return

        users_data = self.module.get_all_users() # Expected to be list of dicts
        if users_data:
            # Convert to DataFrame for display_dataframe utility method
            # Ensure columns match what display_dataframe expects or adjust here
            # Example: users_data might be [{'id':1, 'username':'admin', 'role':'admin'}, ...]
            df_users = pd.DataFrame(users_data)
            # Can select/rename columns if needed: df_users = df_users[['username', 'role']]
            self.display_dataframe(df_users, "All Users")
        else:
            self.show_message("No Users", "No users found in the system or error fetching them.")
