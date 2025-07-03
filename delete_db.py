import os

db_path = r"C:\Users\mkempton\Documents\01-Davinci\MK ULTRA\pm_system-main\project-management_system\project_data.db"

if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"Successfully deleted {db_path}")
    except Exception as e:
        print(f"Error deleting {db_path}: {e}")
else:
    print(f"Database file not found at {db_path}")