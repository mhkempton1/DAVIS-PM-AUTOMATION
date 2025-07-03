import os
import subprocess

project_path = r"C:\Users\mkempton\Documents\01-Davinci\MK ULTRA\pm_system-main\pm_system-main\project-management_system"
os.chdir(project_path)

subprocess.run(["python", "main.py"])