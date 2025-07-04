import os

class Config:
    """
    Manages system-wide configurations for the Construction Project Management System.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    DATABASE_NAME = 'project_data.db'
    DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)
    SCHEMA_FILE = 'schema.sql' # Added for clarity
    SCHEMA_PATH = os.path.join(DATABASE_DIR, SCHEMA_FILE) # Standardized
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    ARCHIVE_DIR = os.path.join(REPORTS_DIR, 'archive')
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')

    # Ensure directories exist
    for directory in [DATABASE_DIR, DATA_DIR, REPORTS_DIR, ARCHIVE_DIR, LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)

    # User Roles and Module Access Permissions
    ROLE_PERMISSIONS = {
        'admin': [
            'integration', 'data_processing', 'project_startup',
            'integration_data_processing', 'execution_management',
            'monitoring_control', 'reporting', 'closeout',
            'reporting_closeout', 'project_scheduling', 'user_management',
            'configuration', 'purchasing_logistics', 'production_prefab', 'daily_log'
        ],
        'project_manager': [
            'integration', 'data_processing', 'project_startup',
            'integration_data_processing', 'execution_management',
            'monitoring_control', 'reporting', 'closeout',
            'reporting_closeout', 'project_scheduling', 'purchasing_logistics',
            'production_prefab', 'daily_log'
        ],
        'estimator': [
            'integration', 'data_processing', 'reporting',
            'integration_data_processing', 'reporting_closeout', 'project_startup'
        ],
        'foreman': [
            'project_startup', 'execution_management', 'monitoring_control',
            'reporting_closeout', 'project_scheduling', 'daily_log',
            'purchasing_logistics'
        ],
        'electrician': [
            'execution_management', 'daily_log'
        ],
        'office_staff': [
            'integration', 'reporting', 'user_management',
            'purchasing_logistics', 'production_prefab', 'project_startup'
        ],
        # Adding other roles from the original example for completeness
        'apprentice': ['execution_management', 'daily_log'],
        'operator': ['execution_management'],
        'lead': ['execution_management', 'project_startup', 'monitoring_control', 'daily_log'],
        'supervisor': [
            'project_startup', 'execution_management', 'monitoring_control',
            'reporting', 'closeout', 'integration'
        ],
        'superintendent': [
            'project_startup', 'execution_management', 'monitoring_control',
            'reporting', 'closeout', 'integration'
        ],
        'division_manager': ['reporting', 'monitoring_control', 'user_management'],
        'president': ['reporting', 'monitoring_control'],
        'ceo': ['reporting', 'monitoring_control'],
        'board_of_directors': ['reporting', 'monitoring_control'],
        'contractor': ['execution_management', 'reporting'],
        'Project Partner': ['execution_management', 'project_startup', 'reporting']
    }

    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'admin_password'

    ESTIMATE_COLUMN_MAPPING = {
        'Cost Code': 'cost_code',
        'Description': 'description',
        'Quantity': 'quantity',
        'Unit': 'unit',
        'Unit Cost': 'unit_cost',
        'Total Cost': 'total_cost',
        'Phase': 'phase'
    }

    REPORT_TEMPLATES = {
        'estimate_vs_actual': 'templates/estimate_vs_actual_template.xlsx'
    }

    @classmethod
    def get_database_path(cls):
        return cls.DATABASE_PATH

    @classmethod
    def get_schema_path(cls):
        return cls.SCHEMA_PATH

    @classmethod
    def get_data_dir(cls):
        return cls.DATA_DIR

    @classmethod
    def get_reports_dir(cls):
        return cls.REPORTS_DIR

    @classmethod
    def get_archive_dir(cls):
        return cls.ARCHIVE_DIR

    @classmethod
    def get_logs_dir(cls):
        return cls.LOGS_DIR

    @classmethod
    def get_role_permissions(cls):
        return cls.ROLE_PERMISSIONS

    @classmethod
    def get_default_admin_credentials(cls):
        return cls.DEFAULT_ADMIN_USERNAME, cls.DEFAULT_ADMIN_PASSWORD

    @classmethod
    def get_estimate_column_mapping(cls):
        return cls.ESTIMATE_COLUMN_MAPPING

    @classmethod
    def get_report_template(cls, template_name):
        return cls.REPORT_TEMPLATES.get(template_name)


if __name__ == "__main__":
    print(f"Database path: {Config.get_database_path()}")
    print(f"Schema path: {Config.get_schema_path()}")
    print(f"Data directory: {Config.get_data_dir()}")
    print(f"Reports directory: {Config.get_reports_dir()}")
    print(f"Archive directory: {Config.get_archive_dir()}")
    print(f"Logs directory: {Config.get_logs_dir()}")
    print(f"Admin permissions: {Config.get_role_permissions().get('admin')}")
    print(f"Project Manager permissions: {Config.get_role_permissions().get('project_manager')}")
