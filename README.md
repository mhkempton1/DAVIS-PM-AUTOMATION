# Project Management System (pm_system)

A modular, Python-based Construction Project Management System with a Graphical User Interface (GUI). The main application is located in the root directory of this repository.

This system is designed to manage construction projects from estimating through closeout, featuring role-based access control and a plugin architecture for extensibility.

## Key Features
- GUI for all operations, built with Tkinter.
- Modular architecture: Backend logic is separated into Python modules (e.g., `project_startup.py`, `user_management.py`) and GUI components are in `gui_frames/`.
- Role-Based Access Control (RBAC) for application features.
- User accounts (for application login) can be linked to Employee records (from the `Employees` table) for accountability in actions like document uploads, material requests, etc.
- Centralized SQLite database defined by `database/schema.sql`.

## Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Installation & Running
1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
    (Replace `<repository-url>` and `<repository-directory>` with actual values).

2.  **Set up a Virtual Environment (Recommended):**
    Navigate to the root directory of the repository (where this `README.md` and `main.py` are located).
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    With your virtual environment activated:
    ```bash
    pip install pandas openpyxl PyPDF2 tkPDFViewer
    ```
    *(Note: `tkPDFViewer` installs `PyMuPDF` as one of its dependencies).*

4.  **Run the Application:**
    Ensure you are in the root directory of the repository and your virtual environment is active.
    ```bash
    python main.py
    ```
    The application should start, presenting a login window. Default admin credentials are `admin` / `admin_password`.

## Directory Structure Overview
- `main.py`: Main application entry point.
- `database/`: Contains the SQLite database (`project_data.db`) and its schema definition (`schema.sql`).
- `gui_frames/`: Contains Python files for different GUI modules/frames.
- `logs/`: Application logs are stored here (e.g., `davinci_app.log`).
- `reports/`: Directory where generated reports are typically saved.
    - `reports/archive/`: For archived project data.
- `data/`: Can be used for sample data, user-uploaded data, or templates.
- `plugins/`: Contains the plugin registry.
- Root `.py` files (e.g., `project_startup.py`, `integration.py`, `user_management.py`, `configuration.py`, `utils.py`): Core backend modules.

## Development Notes
- The application uses Tkinter for its GUI. Styling is managed within `main.py` and `gui_frames/base_frame.py`.
- Backend logic is generally separated into module-specific Python files in the root directory.
- Global application configuration is managed in `configuration.py`.
- Database interactions are centralized through `database_manager.py`.
- The `project-management_system/` subdirectory has been removed; all relevant code is now in the root or its subdirectories as listed above.

## License
See the `LICENSE` file for details.
