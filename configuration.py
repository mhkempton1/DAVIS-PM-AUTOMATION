import os

class Config:
    """
    Manages system-wide configurations for the Construction Project Management System.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    DATABASE_NAME = 'project_data.db'
    DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    ARCHIVE_DIR = os.path.join(REPORTS_DIR, 'archive') # Added ARCHIVE_DIR
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')

    # Ensure directories exist
    # Added ARCHIVE_DIR to the list of directories to be created.
    for directory in [DATABASE_DIR, DATA_DIR, REPORTS_DIR, ARCHIVE_DIR, LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)

    # User Roles and Module Access Permissions
    # This dictionary maps roles to a list of modules they can access.
    # Note: Module names here should match the module filenames (without .py)
    # or the names used in the plugin registry.
    ROLE_PERMISSIONS = {
        'admin': [
            'integration', 'data_processing', 'project_startup',
            'integration_data_processing', 'execution_management', 'monitoring_control',
            'reporting', 'closeout', 'reporting_closeout', 'project_scheduling',
            'user_management', 'configuration',
            'purchasing_logistics', 'production_prefab' # Added new modules
        ],
        'apprentice': [
            'execution_management' # Execute Project Tasks, Quality Control (R)
        ],
        'operator': [
            'execution_management' # Execute Project Tasks, Quality Control (R)
        ],
        'lead': [
            'execution_management', # Assign Tasks & Resources (A), Execute Project Tasks (R), Quality Control (A)
            'project_startup',      # For WBS/task assignment if assisting PM (I)
            'monitoring_control'    # For basic progress tracking (I)
        ],
        'foreman': [
            'project_startup',      # Create Detailed Project Plan (WBS) (R), Archive Project Documents (R)
            'execution_management', # Assign Tasks & Resources (A), Manage Project Team (A), Track Progress & Performance (A), Quality Control (A)
            'monitoring_control',   # Track Progress & Performance (C)
            'reporting_closeout',   # For project reports (C) and archiving (C)
            'project_scheduling'    # For scheduling (C)
        ],
        'supervisor': [
            'project_startup',      # Planning (R)
            'execution_management', # Manage Communications (A)
            'monitoring_control',   # Monitor & Control Budget (R), Manage Changes (R)
            'reporting',            # Reporting (R)
            'closeout',             # Close Contracts (R), Conduct Post-Project Review (R)
            'integration'           # Procurement Planning (R)
        ],
        'superintendent': [
            'project_startup',      # Planning (A)
            'execution_management', # Execution (I)
            'monitoring_control',   # Monitoring & Control (A)
            'reporting',            # Reporting (A)
            'closeout',             # Closing (A)
            'integration'           # Integration (I)
        ],
        'project_manager': [
            'integration', 'data_processing', 'project_startup',
            'integration_data_processing', 'execution_management', 'monitoring_control',
            'reporting', 'closeout', 'reporting_closeout', 'project_scheduling',
            'purchasing_logistics', 'production_prefab' # Added new modules
        ],
        'division_manager': [
            'reporting',
            'monitoring_control',
            'user_management' # For managing users within their division
        ],
        'president': [
            'reporting',
            'monitoring_control'
        ],
        'ceo': [
            'reporting',
            'monitoring_control'
        ],
        'board_of_directors': [
            'reporting',
            'monitoring_control'
        ],
        'estimator': [
            'integration', 'data_processing', 'reporting',
            'integration_data_processing', 'reporting_closeout'
        ],
        'contractor': [
            'execution_management', 'reporting'
        ],
        'electrician': [
            'execution_management', # Execute Project Tasks, Quality Control (R)
            'daily_log'             # Submit daily log entries
        ],
        'Project Partner': [
            'execution_management', 'project_startup', 'reporting'
        ],
        'office_staff': [
            'integration', 'reporting', 'user_management',
            'purchasing_logistics', 'production_prefab' # Added new modules
        ]
    }

    # Default Admin User
    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'admin_password' # In a real system, hash this!

    # Data Mappings (example for estimate data)
    # This can be extended to map columns from different input formats
    ESTIMATE_COLUMN_MAPPING = {
        'Cost Code': 'cost_code',
        'Description': 'description',
        'Quantity': 'quantity',
        'Unit': 'unit',
        'Unit Cost': 'unit_cost',
        'Total Cost': 'total_cost',
        'Phase': 'phase'
    }

    # Report Templates (example)
    REPORT_TEMPLATES = {
        'estimate_vs_actual': 'templates/estimate_vs_actual_template.xlsx'
    }

    def __init__(self):
        """Initializes the Config class."""
        pass

    @classmethod
    def get_database_path(cls):
        """Returns the full path to the SQLite database file."""
        return cls.DATABASE_PATH

    @classmethod
    def get_data_dir(cls):
        """Returns the path to the data directory."""
        return cls.DATA_DIR

    @classmethod
    def get_reports_dir(cls):
        """Returns the path to the reports directory."""
        return cls.REPORTS_DIR

    @classmethod
    def get_archive_dir(cls): # Added getter for ARCHIVE_DIR
        """Returns the path to the archive directory."""
        return cls.ARCHIVE_DIR

    @classmethod
    def get_logs_dir(cls):
        """Returns the path to the logs directory."""
        return cls.LOGS_DIR

    @classmethod
    def get_role_permissions(cls):
        """Returns the dictionary of role-based module permissions."""
        return cls.ROLE_PERMISSIONS

    @classmethod
    def get_default_admin_credentials(cls):
        """Returns the default admin username and password."""
        return cls.DEFAULT_ADMIN_USERNAME, cls.DEFAULT_ADMIN_PASSWORD

    @classmethod
    def get_estimate_column_mapping(cls):
        """Returns the mapping for estimate data columns."""
        return cls.ESTIMATE_COLUMN_MAPPING

    @classmethod
    def get_report_template(cls, template_name):
        """Returns the path to a specific report template."""
        return cls.REPORT_TEMPLATES.get(template_name)

    @classmethod
    def get_schema_path(cls):
        """Returns the full path to the SQL schema file."""
        # Schema file is located in 'database' subdirectory relative to BASE_DIR
        return os.path.join(cls.DATABASE_DIR, 'schema.sql')

if __name__ == "__main__":
    # Example usage:
    print(f"Database path: {Config.get_database_path()}")
    print(f"Data directory: {Config.get_data_dir()}")
    print(f"Reports directory: {Config.get_reports_dir()}")
    print(f"Archive directory: {Config.get_archive_dir()}")
    print(f"Logs directory: {Config.get_logs_dir()}")
    print(f"Admin permissions: {Config.get_role_permissions().get('admin')}")
