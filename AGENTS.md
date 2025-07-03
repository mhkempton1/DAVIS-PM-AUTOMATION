# AGENTS.md - Instructions for AI Agents

This document provides guidance for AI agents working with the `pm_system` repository.

## System Overview

The primary application is a Python-based Construction Project Management System located in `pm_system-main/project-management_system/`.

Key architectural points:
- **Database:** Uses an SQLite database.
    - Main database file: `pm_system-main/project-management_system/database/project_data.db`
    - Schema definition: `pm_system-main/project-management_system/database/schema.sql`. This file defines the structure for the SQLite database.
- **Database Manager:** The `database_manager.py` module handles database connections and operations. Core modules like `project_startup.py`, `integration.py`, and `data_processing.py` have been refactored to accept a `db_manager` instance via dependency injection (DI) in their `__init__` methods. This is the preferred pattern. Other modules (`execution_management.py`, `monitoring_control.py`, `reporting.py`, `closeout.py`) may still use a global import and would benefit from similar DI refactoring.
- **Unused SQL Files:** The SQL files located in the root directory of this repository (e.g., `RunAll.sql`, `00_Settings_and_Drops.sql`, etc.) appear to define a schema for SQL Server. These are **not directly used** by the Python application in `pm_system-main/project-management_system/` and seem to be for a separate system or an older version.

## Development & Testing

### Running Unit Tests
Unit tests are located in the `pm_system-main/project-management_system/tests/` directory.
To run the existing tests:
1. Navigate to the root of the repository.
2. Execute the test script: `./run_tests.sh`

This script changes to the `pm_system-main/project-management_system/` directory and runs `python -m unittest tests.test_project_startup`.

### Dependencies
Ensure all Python dependencies are installed. Core dependencies include `pandas` and `openpyxl`. Additional dependencies discovered and installed during recent work include `PyPDF2` and `tkPDFViewer` (which installs `PyMuPDF`). These should be added to the user-facing `README.md` if not already present.

### Current Known Issues / Limitations (Agent Context)
- **File Editing Tools:** During recent refactoring efforts (July 2025), the provided file editing tools (`overwrite_file_with_block` and `replace_with_git_merge_diff`) showed inconsistent behavior and frequently failed to apply changes to certain files, notably `execution_management.py`. This prevented a full DI refactor and schema alignment across all modules. If extensive changes are needed for such files, alternative editing strategies or manual intervention might be required.

## Coding Conventions & Best Practices
- When modifying modules that use the database, prefer passing the `db_manager` instance via dependency injection rather than relying on the global import.
- Ensure all new backend logic is covered by unit tests.
- Align database interactions with the definitions in `pm_system-main/project-management_system/database/schema.sql`. Pay attention to column names (case sensitivity in Python code, though SQLite is often forgiving) and data types.
- Update this `AGENTS.md` if new architectural patterns are introduced or significant new development practices are adopted.
