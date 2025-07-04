import tkinter as tk
from tkinter import ttk # ttk for styling consistency
from .base_frame import BaseModuleFrame
import logging

logger = logging.getLogger(__name__)


class WelcomeFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        # Use consistent styling from app.colors if available
        bg_color = self.app.colors.get('bg_secondary', '#F0F0F0')
        fg_color = self.app.colors.get('fg_primary', '#000000')

        self.configure(bg=bg_color)

        title_label = tk.Label(
            self,
            text="Welcome to Davinci!",
            font=("Arial", 16, "bold"),
            bg=bg_color,
            fg=fg_color
        )
        title_label.pack(pady=20, padx=20)

        info_label = tk.Label(
            self,
            text="Please select a module from the left menu to begin.",
            font=("Arial", 12),
            bg=bg_color,
            fg=fg_color
        )
        info_label.pack(pady=10, padx=20)

        if self.app.current_username and self.app.current_user_role:
            user_info_text = (
                f"Currently logged in as: {self.app.current_username} "
                f"({self.app.current_user_role})"
            )
            user_label = tk.Label(
                self,
                text=user_info_text,
                font=("Arial", 10),
                bg=bg_color,
                fg=fg_color
            )
            user_label.pack(pady=5)
        else:
            logged_out_label = tk.Label(
                self,
                text="Not currently logged in.",
                font=("Arial", 10),
                bg=bg_color,
                fg=fg_color
            )
            logged_out_label.pack(pady=5)

        # Example of more text with wrapping
        # description_label = tk.Label(
        #     self,
        #     text="This system helps manage construction projects from start to finish, "
        #          "integrating planning, execution, and monitoring phases.",
        #     wraplength=400,
        #     justify=tk.LEFT,
        #     bg=bg_color,
        #     fg=fg_color
        # )
        # description_label.pack(pady=10, padx=20)

        # Placeholder for logo (ensure path is correct and image exists if uncommented)
        # try:
        #     from configuration import Config
        #     import os
        #     logo_path = os.path.join(Config.BASE_DIR, 'assets', 'logo.png') # Example path
        #     if os.path.exists(logo_path):
        #         self.logo_image = tk.PhotoImage(file=logo_path)
        #         logo_display = tk.Label(self, image=self.logo_image, bg=bg_color)
        #         logo_display.pack(pady=20)
        #     else:
        #         logger.warning(f"Logo image not found at: {logo_path}")
        # except Exception as e:
        #     logger.warning(f"Could not load logo for WelcomeFrame: {e}")

# Note: The module_instance for WelcomeFrame is typically None as it's informational.
# The 'app' instance provides access to global app state like current_user or styles.
