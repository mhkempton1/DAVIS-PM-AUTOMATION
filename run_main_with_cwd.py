import subprocess
import os

project_path = r"C:\Users\mkempton\Documents\01-Davinci\MK ULTRA\pm_system-main\project-management_system"

# Run main.py from the project directory
subprocess.run(["python", "main.py"], cwd=project_path)