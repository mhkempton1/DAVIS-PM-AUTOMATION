import importlib
import os
import logging

# Set up logging for the Plugin Registry
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PluginRegistry:
    """
    Manages the dynamic loading and registration of system modules (plugins).
    Allows for new modules to be added without modifying core code.
    """
    _registered_modules = {}

    @classmethod
    def register_module(cls, module_name, module_instance):
        """
        Registers a module instance with the registry.
        The module_name should be a unique identifier (e.g., its filename without .py).
        The module_instance should be an instantiated object of the module's main class.
        """
        if module_name in cls._registered_modules:
            logger.warning(f"Module '{module_name}' is already registered. Overwriting.")
        cls._registered_modules[module_name] = module_instance
        logger.info(f"Module '{module_name}' registered successfully.")

    @classmethod
    def get_module(cls, module_name):
        """
        Retrieves a registered module instance by its name.
        Returns None if the module is not found.
        """
        module = cls._registered_modules.get(module_name)
        if not module:
            logger.warning(f"Attempted to retrieve unregistered module: '{module_name}'.")
        return module

    @classmethod
    def list_registered_modules(cls):
        """
        Returns a list of all names of currently registered modules.
        """
        return list(cls._registered_modules.keys())

    @classmethod
    def load_module_from_file(cls, file_path, module_name=None):
        """
        Dynamically loads a Python module from a given file path.
        Optionally accepts a module_name; otherwise, derives it from the file name.
        Returns the loaded module object.
        """
        if not os.path.exists(file_path):
            logger.error(f"Module file not found: {file_path}")
            return None

        # Derive module name from file path if not provided
        if module_name is None:
            module_name = os.path.splitext(os.path.basename(file_path))[0]

        # Add the directory to Python's path to allow importlib.import_module
        module_dir = os.path.dirname(file_path)
        if module_dir not in importlib.sys.path:
            importlib.sys.path.insert(0, module_dir)
            logger.debug(f"Added '{module_dir}' to sys.path for module loading.")

        try:
            # Use importlib to load the module
            # The actual module name for importlib needs to be relative to the path added
            # For simplicity, we'll assume the module is directly in a path added to sys.path
            # For more complex package structures, use importlib.util.spec_from_file_location
            module = importlib.import_module(module_name)
            logger.info(f"Dynamically loaded module from {file_path} as '{module_name}'.")
            return module
        except ImportError as e:
            logger.error(f"Failed to import module '{module_name}' from '{file_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading module '{module_name}' from '{file_path}': {e}")
            return None

    @classmethod
    def initialize_and_register_modules(cls, module_paths_and_classes):
        """
        Initializes and registers multiple modules.
        module_paths_and_classes is a dictionary where keys are module names (e.g., 'integration')
        and values are tuples (file_path, class_name_in_module).
        """
        for mod_name, (file_path, class_name) in module_paths_and_classes.items():
            loaded_module = cls.load_module_from_file(file_path, mod_name)
            if loaded_module:
                try:
                    # Get the class from the loaded module and instantiate it
                    module_class = getattr(loaded_module, class_name)
                    # All modules are expected to handle their own dependencies (like db_manager)
                    # by importing them directly if they are singletons, or via other DI means.
                    # The registry's role is to load and provide access to the module's main class instance.
                    instance = module_class()
                    cls.register_module(mod_name, instance)
                except AttributeError:
                    logger.error(f"Class '{class_name}' not found in module '{mod_name}' from '{file_path}'.")
                except Exception as e:
                    logger.error(f"Error instantiating class '{class_name}' from module '{mod_name}': {e}")
            else:
                logger.error(f"Could not load module '{mod_name}' from '{file_path}'. Skipping registration.")

if __name__ == "__main__":
    # This block demonstrates how PluginRegistry would be used.
    # In a real scenario, main.py would call initialize_and_register_modules.

    print("--- Testing PluginRegistry ---")

    # Create dummy modules for testing
    dummy_module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dummy_modules')
    os.makedirs(dummy_module_dir, exist_ok=True)

    dummy_module_1_path = os.path.join(dummy_module_dir, 'dummy_module_1.py')
    with open(dummy_module_1_path, 'w') as f:
        f.write("""
class DummyModule1:
    def __init__(self):
        print("DummyModule1 initialized!")
    def run(self):
        return "DummyModule1 running!"
""")

    dummy_module_2_path = os.path.join(dummy_module_dir, 'dummy_module_2.py')
    with open(dummy_module_2_path, 'w') as f:
        f.write("""
class DummyModule2:
    def __init__(self):
        print("DummyModule2 initialized!")
    def process_data(self, data):
        return f"DummyModule2 processing: {data}"
""")

    # Define the modules to load and their main classes
    # Note: For actual system modules, file_path will be ../integration.py, etc.
    modules_to_load = {
        'dummy_module_1': (dummy_module_1_path, 'DummyModule1'),
        'dummy_module_2': (dummy_module_2_path, 'DummyModule2')
    }

    # Initialize and register the dummy modules
    PluginRegistry.initialize_and_register_modules(modules_to_load)

    # List registered modules
    print(f"\nRegistered modules: {PluginRegistry.list_registered_modules()}")

    # Retrieve and use a module
    mod1 = PluginRegistry.get_module('dummy_module_1')
    if mod1:
        print(f"Retrieved dummy_module_1: {mod1.run()}")

    mod2 = PluginRegistry.get_module('dummy_module_2')
    if mod2:
        print(f"Retrieved dummy_module_2: {mod2.process_data('test_data')}")

    # Try to retrieve a non-existent module
    non_existent_mod = PluginRegistry.get_module('non_existent_module')
    print(f"Retrieved non_existent_module: {non_existent_mod}")

    # Clean up dummy files and directory
    os.remove(dummy_module_1_path)
    os.remove(dummy_module_2_path)
    os.rmdir(dummy_module_dir)
    print("\nCleaned up dummy modules.")
