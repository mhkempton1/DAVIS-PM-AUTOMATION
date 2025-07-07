import tkinter as tk
from tkinter import ttk
from .base_frame import BaseModuleFrame
import logging

logger = logging.getLogger(__name__)

class CRMModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        """
        Initializes the CRM Module Frame.

        Args:
            parent: The parent tkinter widget.
            app: The main application instance.
            module_instance: The backend CRM module instance.
        """
        super().__init__(parent, app, module_instance)
        self.module_instance = module_instance # The backend CRM module
        self.create_widgets()
        logger.info("CRMModuleFrame initialized.")

    def create_widgets(self):
        """
        Creates the widgets for the CRM module frame.
        """
        # Main label for the CRM module
        main_label = ttk.Label(self, text="Customer Relationship Management (CRM)", font=("Arial", 16, "bold"))
        main_label.pack(pady=20, padx=20)

        # Placeholder text
        placeholder_text = (
            "This is the CRM module.\n\n"
            "Future functionality will include:\n"
            "- Managing customer contacts\n"
            "- Tracking interactions and communications\n"
            "- Sales pipeline management\n"
            "- Customer support features\n\n"
            "Currently, this is a placeholder."
        )

        info_label = ttk.Label(self, text=placeholder_text, justify=tk.CENTER, wraplength=400)
        info_label.pack(pady=10, padx=20)

        # Example: Button to interact with backend (if methods were defined)
        # if self.module_instance and hasattr(self.module_instance, 'get_customer_count'):
        #     def show_customer_count():
        #         count, message = self.module_instance.get_customer_count() # Hypothetical method
        #         self.show_message("Info", f"Current customer count: {count}\n{message}")

        #     count_button = ttk.Button(self, text="Get Customer Count (Simulated)", command=show_customer_count)
        #     count_button.pack(pady=10)

        logger.debug("CRMModuleFrame widgets created.")

    def on_active_project_changed(self):
        """
        Called when the active project changes in the main application.
        The CRM module might be project-agnostic or could filter by project if relevant.
        """
        # For now, just log. In the future, CRM data might be filtered by active project.
        if self.app.active_project_id:
            logger.info(f"CRMModuleFrame: Active project changed to {self.app.active_project_name} (ID: {self.app.active_project_id})")
            # Potentially refresh or filter CRM data here
        else:
            logger.info("CRMModuleFrame: Active project cleared.")
            # Potentially show all CRM data or a default view

if __name__ == '__main__':
    # This section allows for direct testing of the CRMModuleFrame if needed.
    # It requires a mock app and parent to run.
    # Example:
    # root = tk.Tk()
    # root.title("CRM Frame Test")
    # root.geometry("600x400")
    #
    # # Mock app and module instance for testing
    # class MockApp:
    #     def __init__(self):
    #         self.active_project_id = None
    #         self.active_project_name = None
    #         self.modules = {} # Mock modules
    #
    # class MockCRMModule:
    #     def __init__(self):
    #         logger.info("MockCRMModule initialized for testing.")
    #     # def get_customer_count(self): return 0, "Simulated count"
    #
    # logging.basicConfig(level=logging.INFO)
    # mock_app_instance = MockApp()
    # mock_crm_backend = MockCRMModule()
    #
    # frame = CRMModuleFrame(root, mock_app_instance, mock_crm_backend)
    # frame.pack(fill="both", expand=True)
    #
    # root.mainloop()
    logger.info("crm_frame.py executed directly (for testing notes).")
