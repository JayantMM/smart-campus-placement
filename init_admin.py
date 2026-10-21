"""
Helper utility to initialize or reset an Administrator account
for the Smart Campus Placement Management System.

Usage:
    python init_admin.py
    python init_admin.py <username> <password>
"""

import sys
from werkzeug.security import generate_password_hash
from config import get_db_connection


def init_admin(username="admin", password="Admin@12345"):
    print(f"\nInitializing administrator account: '{username}'...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        pw_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO admins (username, password_hash)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash)
        """, (username, pw_hash))

        conn.commit()
        cursor.close()
        conn.close()

        print("--------------------------------------------------")
        print(" [SUCCESS] Administrator account is ready!")
        print(f" Username: {username}")
        print(f" Password: {password}")
        print(" Login URL: http://127.0.0.1:5000/admin/login")
        print("--------------------------------------------------\n")
        return True
    except Exception as e:
        print(f"\n[ERROR] Could not configure administrator: {e}")
        print("Please check that MySQL is started in XAMPP and database schema has been executed.\n")
        return False


if __name__ == "__main__":
    u = sys.argv[1] if len(sys.argv) > 1 else "admin"
    p = sys.argv[2] if len(sys.argv) > 2 else "Admin@12345"
    init_admin(u, p)

