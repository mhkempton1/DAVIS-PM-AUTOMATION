import os
import subprocess

project_dir = r"C:\Users\mkempton\Documents\01-Davinci\MK ULTRA\pm_system-main\project-management_system"

os.chdir(project_dir)

subprocess.run(["python", "main.py"])