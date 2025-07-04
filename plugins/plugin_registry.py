import importlib
import os
import logging
import sys # Added sys for sys.path manipulation

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Manages dynamic loading and registration of system modules (plugins).
    """
    _registered_modules = {}

    @classmethod
    def register_module(cls, module_name, module_instance):
        """
        Registers a module instance.
        """
        if module_name in cls._registered_modules:
            logger.warning(f"Module '{module_name}' is already registered. Overwriting.")
        cls._registered_modules[module_name] = module_instance
        logger.info(f"Module '{module_name}' registered successfully.")

    @classmethod
    def get_module(cls, module_name):
        """
        Retrieves a registered module instance. Returns None if not found.
        """
        module = cls._registered_modules.get(module_name)
        if not module:
            logger.warning(f"Attempted to retrieve unregistered module: '{module_name}'.")
        return module

    @classmethod
    def list_registered_modules(cls):
        """Returns a list of names of registered modules."""
        return list(cls._registered_modules.keys())

    @classmethod
    def load_module_from_file(cls, file_path, module_name=None):
        """
        Dynamically loads a Python module from a file path.
        """
        if not os.path.exists(file_path):
            logger.error(f"Module file not found: {file_path}")
            return None

        if module_name is None:
            module_name = os.path.splitext(os.path.basename(file_path))[0]

        module_dir = os.path.dirname(file_path)
        # Ensure module_dir is absolute and in sys.path for reliable import
        if module_dir not in sys.path: # Use sys.path directly
            sys.path.insert(0, module_dir) # Add to beginning for higher precedence
            logger.debug(f"Added '{module_dir}' to sys.path for module loading.")

        # If file_path is relative, make it absolute relative to some known base if necessary
        # For now, assuming file_path is either absolute or correctly relative from CWD

        try:
            module = importlib.import_module(module_name)
            logger.info(f"Dynamically loaded module from {file_path} as '{module_name}'.")
            return module
        except ImportError as e:
            logger.error(f"Failed to import module '{module_name}' from '{file_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading module '{module_name}' from '{file_path}': {e}")
            return None
        finally:
            # Clean up sys.path if it was modified, though this can be tricky
            # if other imports depend on this path later.
            # For a simple script-like plugin loader, it might be okay to leave it.
            # If this registry is long-lived, consider removing the path carefully.
            # if module_dir in sys.path and module_dir == sys.path[0]:
            #    sys.path.pop(0)
            #    logger.debug(f"Removed '{module_dir}' from sys.path after attempt.")
            pass


    @classmethod
    def initialize_and_register_modules(cls, module_paths_and_classes):
        """
        Initializes and registers multiple modules.
        module_paths_and_classes: dict {module_name: (file_path, class_name)}
        """
        for mod_name, (file_path, class_name) in module_paths_and_classes.items():
            loaded_module = cls.load_module_from_file(file_path, mod_name)
            if loaded_module:
                try:
                    module_class = getattr(loaded_module, class_name)
                    # Assuming modules handle their own dependencies (e.g., db_manager)
                    instance = module_class()
                    cls.register_module(mod_name, instance)
                except AttributeError:
                    logger.error(f"Class '{class_name}' not found in module '{mod_name}'.")
                except Exception as e:
                    logger.error(f"Error instantiating class '{class_name}' from '{mod_name}': {e}")
            else:
                logger.error(f"Could not load module '{mod_name}'. Skipping registration.")


if __name__ == "__main__":
    print("--- Testing PluginRegistry ---")

    # Create dummy module directory relative to this script's location
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_module_dir = os.path.join(current_script_dir, 'dummy_modules_test')
    os.makedirs(dummy_module_dir, exist_ok=True)

    # Create __init__.py to make it a package (helps with predictable imports)
    with open(os.path.join(dummy_module_dir, '__init__.py'), 'w') as f:
        f.write('') # Empty __init__.py

    dummy_module_1_filename = 'dummy_module_1.py'
    dummy_module_1_path = os.path.join(dummy_module_dir, dummy_module_1_filename)
    with open(dummy_module_1_path, 'w') as f:
        f.write("""
class DummyModule1:
    def __init__(self):
        print("DummyModule1 instance created!")
    def run(self):
        return "DummyModule1 running!"
""")

    dummy_module_2_filename = 'dummy_module_2.py'
    dummy_module_2_path = os.path.join(dummy_module_dir, dummy_module_2_filename)
    with open(dummy_module_2_path, 'w') as f:
        f.write("""
class DummyModule2:
    def __init__(self):
        print("DummyModule2 instance created!")
    def process_data(self, data):
        return f"DummyModule2 processing: {data}"
""")

    # Add the parent of dummy_modules_test to sys.path so it can be found as a package
    # This simulates if dummy_modules_test was a top-level package in the project
    # For this test, plugin_registry.py is in 'plugins', dummy_modules_test is in 'plugins/dummy_modules_test'
    # So, 'plugins' directory should be in sys.path for 'import dummy_modules_test.dummy_module_1'
    # The load_module_from_file method temporarily adds the direct parent of the module file.

    # Modules to load are specified by their Python importable name, not file path directly here.
    # The load_module_from_file method handles path manipulation for importlib.

    # Re-think: initialize_and_register_modules expects file_path.
    # The module name passed to import_module should be the filename without .py if it's in sys.path.

    modules_to_load = {
        # module_name_for_registry: (path_to_file, ClassNameInFile)
        'dummy_module_1': (dummy_module_1_path, 'DummyModule1'),
        'dummy_module_2': (dummy_module_2_path, 'DummyModule2')
    }

    PluginRegistry.initialize_and_register_modules(modules_to_load)

    print(f"\nRegistered modules: {PluginRegistry.list_registered_modules()}")

    mod1 = PluginRegistry.get_module('dummy_module_1')
    if mod1:
        print(f"Test dummy_module_1: {mod1.run()}")

    mod2 = PluginRegistry.get_module('dummy_module_2')
    if mod2:
        print(f"Test dummy_module_2: {mod2.process_data('sample data')}")

    non_existent = PluginRegistry.get_module('non_existent')
    print(f"Test non_existent_module: {non_existent}")

    # Cleanup
    os.remove(dummy_module_1_path)
    os.remove(dummy_module_2_path)
    os.remove(os.path.join(dummy_module_dir, '__init__.py'))
    os.rmdir(dummy_module_dir)
    print("\nCleaned up dummy_modules_test.")
