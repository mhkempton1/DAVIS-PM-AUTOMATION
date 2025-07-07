"""
Application-wide constants for statuses, types, and other categorical data.
"""

# Project Statuses (should align with values in 'ProjectStatuses' table in schema.sql)
PROJECT_STATUS_PENDING = "Pending"
PROJECT_STATUS_PLANNING = "Planning"
PROJECT_STATUS_ACTIVE = "Active" # Assuming 'Execution' might be an alias or similar
PROJECT_STATUS_ON_HOLD = "On Hold"
PROJECT_STATUS_COMPLETED = "Completed" # schema.sql has 'Completed'
PROJECT_STATUS_CLOSED = "Closed"     # schema.sql has 'Closed'
PROJECT_STATUS_CANCELLED = "Cancelled" # schema.sql has 'Cancelled'


# WBS Element Statuses (example, schema may vary or not have this explicitly)
WBS_STATUS_PLANNED = "Planned"
WBS_STATUS_IN_PROGRESS = "In Progress"
WBS_STATUS_COMPLETED = "Completed"
WBS_STATUS_ON_HOLD = "On Hold"


# Task Statuses (should align with 'TaskStatuses' table in schema.sql)
TASK_STATUS_PENDING = "Pending"
TASK_STATUS_IN_PROGRESS = "In Progress"
TASK_STATUS_COMPLETED = "Completed"
TASK_STATUS_BLOCKED = "Blocked"
TASK_STATUS_DEFERRED = "Deferred"


# Document Types
DOC_TYPE_DESIGN_DRAWING = "Design Drawing"
DOC_TYPE_ESTIMATE_CSV = "Estimate CSV" # Example for raw data
DOC_TYPE_REPORT_PDF = "Report PDF"
DOC_TYPE_GENERAL_DOCUMENT = "General Document"


# Resource Types (for WBSElementResources, etc.)
RESOURCE_TYPE_LABOR = "Labor"
RESOURCE_TYPE_MATERIAL = "Material"
RESOURCE_TYPE_EQUIPMENT = "Equipment"
RESOURCE_TYPE_SUBCONTRACTOR = "Subcontractor"
RESOURCE_TYPE_LUMP_SUM = "Lump Sum"
RESOURCE_TYPE_OTHER = "Other"


# Purchasing Log Statuses (align with domain logic for Purchasing_Log.Status)
PURCHASE_STATUS_REQUESTED = "Requested"
PURCHASE_STATUS_APPROVED = "Approved"
PURCHASE_STATUS_ORDERED = "Ordered"
PURCHASE_STATUS_SHIPPED = "Shipped"
PURCHASE_STATUS_RECEIVED_PARTIAL = "Received Partial"
PURCHASE_STATUS_RECEIVED_FULL = "Received Full"
PURCHASE_STATUS_CANCELLED = "Cancelled"
PURCHASE_STATUS_CLOSED = "Closed" # If applicable


# Production Assembly Tracking Statuses (align with Production_Assembly_Tracking.Status)
PRODUCTION_STATUS_PLANNED = "Planned"
PRODUCTION_STATUS_IN_PROGRESS = "In Progress"
PRODUCTION_STATUS_COMPLETED = "Completed"
PRODUCTION_STATUS_SHIPPED = "Shipped" # If distinct from completed before shipping
PRODUCTION_STATUS_CANCELLED = "Cancelled"


# User Roles (already in Config.ROLE_PERMISSIONS keys, but can be aliased here for direct use if preferred)
# Example: ROLE_ADMIN = "admin"
# For now, rely on Config.ROLE_PERMISSIONS.keys() for roles.

# Default Admin User (already in Config)
# DEFAULT_ADMIN_USERNAME = "admin"
# DEFAULT_ADMIN_PASSWORD = "admin_password" # Not for here, just for reference
# This is more configuration than a fixed constant.

# User Roles (align with Config.ROLE_PERMISSIONS keys)
ROLE_ADMIN = "admin"
ROLE_PROJECT_MANAGER = "project_manager"
ROLE_ESTIMATOR = "estimator"
ROLE_FIELD_STAFF = "field_staff"
# Add other roles as defined in Config.ROLE_PERMISSIONS


# Observation Types (for Daily Logs or similar)
OBS_TYPE_SAFETY = "Safety"
OBS_TYPE_ISSUE = "Issue" # e.g., blockers, RFIs
OBS_TYPE_TOOL = "Tool"   # e.g., tool/equipment notes
OBS_TYPE_GENERAL = "General"


# Material Log Types (for Daily Logs, distinct from general Resource Types if needed)
MATERIAL_LOG_TYPE_USED = "Used"
MATERIAL_LOG_TYPE_NEEDED = "Needed"
MATERIAL_LOG_TYPE_DELIVERED = "Delivered"


# Note: It's important that the string values here EXACTLY match what's expected
# in the database schema (e.g., in ProjectStatuses, TaskStatuses tables) or
# in application logic that relies on these specific strings.
# If the database has IDs for these statuses, then these constants might map to those IDs,
# or the application logic would fetch the ID based on these string constants.
# For this refactoring, we are replacing magic strings.
# The schema.sql defines ProjectStatuses like:
# (1, 'Pending'), (2, 'Planning'), (3, 'Active'), (4, 'On Hold'), (5, 'Completed'), (6, 'Closed'), (7, 'Cancelled')
# So, the string values here must match those.
# The same applies to TaskStatuses.
# For other statuses not in dedicated DB tables (e.g. WBS_STATUS_PLANNED), these constants define the standard.

# Core Module Names (used as keys and for navigation/registration)
MODULE_INTEGRATION = "integration"
MODULE_DATA_PROCESSING = "data_processing"
MODULE_PROJECT_STARTUP = "project_startup"
MODULE_EXECUTION_MANAGEMENT = "execution_management"
MODULE_MONITORING_CONTROL = "monitoring_control"
MODULE_REPORTING = "reporting"
MODULE_CLOSEOUT = "closeout"
MODULE_USER_MANAGEMENT = "user_management"
MODULE_CONFIGURATION = "configuration" # Though this is often just the Config class
MODULE_CRM = "crm" # Added CRM module key

# GUI Frame / Activity Bar Identifiers (might overlap with module names or be specific UI identifiers)
FRAME_IDP = "integration_data_processing" # Integration & Data Processing
FRAME_PROJECT_STARTUP = "project_startup" # Matches module name
FRAME_EXEC_MGMT = "execution_management" # Matches module name
FRAME_MON_CTRL = "monitoring_control" # Matches module name
FRAME_REP_CLOSE = "reporting_closeout" # Reporting & Closeout
FRAME_SCHEDULING = "project_scheduling"
FRAME_DAILY_LOG = "daily_log"
FRAME_PURCH_LOGISTICS = "purchasing_logistics"
FRAME_PROD_PREFAB = "production_prefab"
FRAME_USER_MGMT = "user_management" # Matches module name
FRAME_CRM = "crm_frame" # Added CRM frame identifier
