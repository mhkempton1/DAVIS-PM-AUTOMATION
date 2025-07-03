import sqlite3
import os

# Path to the database file
db_path = os.path.join("pm_system-main", "project-management_system", "database", "project_data.db")

def check_admin_user():
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if cursor.fetchone() is None:
            print("Table 'users' does not exist.")
            return

        # Check for admin user
        cursor.execute("SELECT username, role FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()

        if admin_user:
            print(f"Admin user found: Username='{admin_user[0]}', Role='{admin_user[1]}'")
        else:
            print("Admin user 'admin' not found.")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_admin_user()
