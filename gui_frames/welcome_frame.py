import tkinter as tk
from tkinter import ttk # ttk might be used for styling consistency
from .base_frame import BaseModuleFrame

class WelcomeFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Welcome to Davinci!", font=("Arial", 16, "bold")).pack(pady=20, padx=20)
        tk.Label(self, text="Please select a module from the left menu to begin.", font=("Arial", 12)).pack(pady=10, padx=20)

        # Display current user info if available
        if self.app.current_username and self.app.current_user_role:
            user_info_text = f"Currently logged in as: {self.app.current_username} ({self.app.current_user_role})"
            tk.Label(self, text=user_info_text, font=("Arial", 10)).pack(pady=5)
        else:
            # This case should ideally not happen if WelcomeFrame is shown only after login,
            # but good to have a fallback or ensure it's handled.
            tk.Label(self, text="Not currently logged in.", font=("Arial", 10)).pack(pady=5)

        # You can add more introductory text, images, or quick links here.
        # For example:
        # tk.Label(self, text="This system helps manage construction projects from start to finish.",
        #          wraplength=400, justify=tk.LEFT).pack(pady=10, padx=20)

        # Placeholder for a logo or an image if you have one
        # try:
        #     # Assuming you have a logo image in a path accessible via Config
        #     # from configuration import Config
        #     # logo_path = Config.get_logo_path() # You'd need to add this to Config
        #     # if os.path.exists(logo_path):
        #     #     self.logo_image = tk.PhotoImage(file=logo_path) # Keep a reference
        #     #     tk.Label(self, image=self.logo_image).pack(pady=20)
        #     pass # No logo for now
        # except Exception as e:
        #     logger.warning(f"Could not load logo for WelcomeFrame: {e}")

# Example usage (for context, not part of this file's direct execution)
# In main.py, when showing the welcome/overview frame:
# from gui_frames.welcome_frame import WelcomeFrame
# ...
# self.show_module_frame('overview', WelcomeFrame) # Or similar logic
# Where 'overview' might be a conceptual module name for the welcome screen.
# The WelcomeFrame doesn't typically have its own backend "module_instance",
# so `module_instance` would be None.
# The `app` instance (ProjectManagementApp) is passed for accessing global app state like current_user.
