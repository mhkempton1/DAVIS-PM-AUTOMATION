import tkinter as tk
from tkinter import ttk

# Assuming other modules might exist, e.g., ProjectSetupFrame
# from gui_frames.project_setup_frame import ProjectSetupFrame
from gui_frames.productivity_frame import ProductivityModuleFrame
from productivity import Productivity
from database_manager import DatabaseManager

class AppState:
    """
    A simple class to hold shared application state.
    """
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.active_project_id = None # Example: Set this when a project is opened/selected

    def get_active_project_id(self):
        return self.active_project_id

    def set_active_project_id(self, project_id):
        self.active_project_id = project_id
        # Potentially notify other parts of the app about the change
        print(f"Active project set to: {project_id}")


class PluginRegistry:
    """
    A simple registry for application modules/plugins.
    """
    def __init__(self):
        self.modules = {}
        self.module_frames = {} # Stores references to the frame classes

    def register_module(self, module_name, module_instance, frame_class):
        self.modules[module_name] = module_instance
        self.module_frames[module_name] = frame_class
        print(f"Module '{module_name}' registered.")

    def get_module(self, module_name):
        return self.modules.get(module_name)

    def get_frame_class(self, module_name):
        return self.module_frames.get(module_name)


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Project Management System")
        self.geometry("1200x800")

        self.db_manager = DatabaseManager("pm_system.db") # Main database
        self.db_manager.connect()

        self.app_state = AppState(self.db_manager)
        self.plugin_registry = PluginRegistry()

        self._initialize_modules()
        self._create_main_layout()
        self.populate_navigation_menu()

        # Simulate setting an active project for demonstration
        self.app_state.set_active_project_id(1) # Example project ID
        # Show a default frame or a welcome screen
        self.show_frame("Productivity") # Default to Productivity for now


    def _initialize_modules(self):
        # Instantiate and register the Productivity module
        productivity_logic = Productivity(self.db_manager)
        self.plugin_registry.register_module("Productivity", productivity_logic, ProductivityModuleFrame)

        # TODO: Initialize and register other modules here
        # Example:
        # project_setup_logic = ProjectSetup(self.db_manager)
        # self.plugin_registry.register_module("ProjectSetup", project_setup_logic, ProjectSetupFrame)

    def _create_main_layout(self):
        # Main container frame
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Navigation bar (Activity Bar)
        self.nav_bar = ttk.Frame(main_container, width=200, style="Nav.TFrame")
        self.nav_bar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        # Add a style for the nav bar for better visual separation if needed
        s = ttk.Style()
        s.configure("Nav.TFrame", background="#e0e0e0")


        # Content area where module frames will be displayed
        self.content_area = ttk.Frame(main_container)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.frames = {} # To store instances of module frames

    def populate_navigation_menu(self):
        # Add "Productivity" button
        prod_button = ttk.Button(self.nav_bar, text="Productivity",
                                 command=lambda: self.show_frame("Productivity"))
        prod_button.pack(fill=tk.X, pady=5, padx=5)

        # TODO: Add buttons for other registered modules
        # Example:
        # ps_button = ttk.Button(self.nav_bar, text="Project Setup",
        #                        command=lambda: self.show_frame("ProjectSetup"))
        # ps_button.pack(fill=tk.X, pady=5, padx=5)

        # Add a separator for clarity if many buttons
        separator = ttk.Separator(self.nav_bar, orient='horizontal')
        separator.pack(fill='x', pady=10, padx=5)


    def show_frame(self, module_name):
        frame_class = self.plugin_registry.get_frame_class(module_name)
        if frame_class:
            # Destroy current frame in content_area if any
            for widget in self.content_area.winfo_children():
                widget.destroy()

            # If frame instance already exists, use it (optional, or always recreate)
            # if module_name in self.frames:
            #     frame = self.frames[module_name]
            # else:
            #     frame = frame_class(self.content_area, self.app_state)
            #     self.frames[module_name] = frame

            # Always recreate frame for simplicity here, or manage instances if state needs to be preserved differently
            frame = frame_class(self.content_area, self.app_state)
            self.frames[module_name] = frame # Store the instance

            frame.pack(fill=tk.BOTH, expand=True)
            # If the frame has a refresh method, call it
            if hasattr(frame, 'refresh_active_project_data'):
                frame.refresh_active_project_data()
            print(f"Showing frame for module: {module_name}")
        else:
            print(f"Error: No frame class registered for module '{module_name}'")


    def on_closing(self):
        print("Application closing...")
        if self.db_manager:
            self.db_manager.disconnect()
        self.destroy()

if __name__ == '__main__':
    app = MainApplication()
    app.protocol("WM_DELETE_WINDOW", app.on_closing) # Handle window close event
    app.mainloop()
