"""
Custom exceptions for the Project Management System application.
"""

class AppError(Exception):
    """Base class for application-specific errors."""
    pass

class AppValidationError(AppError, ValueError):
    """
    Raised when a validation rule within the business logic is violated.
    This is distinct from basic input type validation.
    Example: Trying to approve a document that is not in a 'Pending Approval' state.
    """
    pass

class AppOperationConflictError(AppError, RuntimeError):
    """
    Raised when an operation cannot be performed due to a conflict with the current state
    of the system, often related to data integrity or duplication where it's not allowed.
    Example: Trying to create a unique resource that already exists.
    """
    pass

class AppDatabaseError(AppError, RuntimeError):
    """
    Raised for application-specific database operation failures that are not
    covered by lower-level sqlite3.Error directly, or to wrap them.
    """
    pass
