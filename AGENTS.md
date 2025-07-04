# AGENTS.md - Instructions for AI Agents

This document provides guidance for AI agents working with the `pm_system` repository.

## System Overview

The primary application is a Python-based Construction Project Management System located in the **root directory** of this repository. The main entry point is `main.py`.

The `project-management_system/` subdirectory, which contained a separate or older version of an application, **has been removed** (as of July 2025 refactoring). All development focus is on the application in the root directory.

Key architectural points:
- **Database:** Uses an SQLite database.
    - Main database file is `database/project_data.db` (relative to the repository root).
    - Schema definition is in `database/schema.sql`.
- **Database Manager:** `database_manager.py` (in root) handles database connections and operations. Dependency Injection (DI) for the `db_manager` is preferred.
- **User Management & Employee Linking:**
    - Application users are managed in a `users` table (for login, roles).
    - The `users` table now has an `EmployeeID` column, which is a foreign key to the `Employees.EmployeeID` table. This links an application user account to a specific employee record.
    - The `UserManagement` module and its corresponding GUI frame (`UserManagementModuleFrame`) allow administrators to create these links.
    - Actions within the application that require an `EmployeeID` (e.g., for logging who performed an action) now rely on this link being established. If a user is not linked to an employee, such actions will be blocked with an error message.
- **Outdated Files:** Any SQL files in the root directory (e.g., `RunAll.sql`) that define SQL Server schemas are not used by the current Python application.

## Development & Testing

### Running Unit Tests
The previous unit test script (`run_tests.sh`) targeted tests within the now-deleted `project-management_system/` directory and is no longer applicable. New unit tests for the main application should be created in a `tests/` directory at the root if desired. Currently, primary testing is manual.

### Dependencies
Core Python dependencies include `pandas` and `openpyxl`. GUI and PDF functionalities require `PyPDF2` and `tkPDFViewer` (which installs `PyMuPDF`). Ensure these are installed, preferably in a virtual environment.

### Current Known Issues / Limitations (Agent Context)
- **File Editing Tools:** The `overwrite_file_with_block` tool has shown inconsistency with very large files. `replace_with_git_merge_diff` is sensitive to exact matches. For extensive changes to large files, incremental edits are recommended.

## Coding Conventions & Best Practices
- Prioritize Dependency Injection for `db_manager`.
- Ensure new backend logic is covered by unit tests where feasible.
- Adhere to definitions in `database/schema.sql`.
- When an action needs to be attributed to an employee, use the linked `EmployeeID` from the `users` table (via `UserManagement.get_user_details_by_username()`).
- Update this `AGENTS.md` with any significant architectural changes or new development practices.
