import sqlite3
import os
import sys
from argon2 import PasswordHasher

# Ensure project root is on sys.path so `from config import DB_PATH` works when running this file directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DB_PATH

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ph = PasswordHasher()

    try:
        # Insert admin
        cursor.execute("""
        INSERT INTO users (username, password_hash, role, full_name)
        VALUES (?, ?, ?, ?)
        """, ("LAB", ph.hash("Lansadmin123"), "admin", "Lansana Alfred Braima"))

        # Insert lecturer 1
        cursor.execute("""
        INSERT INTO users (username, password_hash, role, full_name)
        VALUES (?, ?, ?, ?)
        """, ("lect1", ph.hash("lect123"), "lecturer", "Alisine Jalloh"))

        # Insert lecturer 2
        cursor.execute("""
        INSERT INTO users (username, password_hash, role, full_name)
        VALUES (?, ?, ?, ?)
        """, ("lect2", ph.hash("lect123"), "lecturer", "A.J Conteh"))

        # Fetch lecturer IDs
        cursor.execute("SELECT user_id FROM users WHERE username = 'lect1'")
        lect1_id = cursor.fetchone()[0]

        cursor.execute("SELECT user_id FROM users WHERE username = 'lect2'")
        lect2_id = cursor.fetchone()[0]

        # Insert sample modules
        cursor.execute("""
        INSERT INTO modules (module_code, module_name, lecturer_id, planned_weeks)
        VALUES (?, ?, ?, ?)
        """, ("DB101", "Database Systems", lect1_id, 14))

        cursor.execute("""
        INSERT INTO modules (module_code, module_name, lecturer_id, planned_weeks)
        VALUES (?, ?, ?, ?)
        """, ("MATH201", "Mathematics", lect2_id, 14))

        conn.commit()
        print("✅ Database seeded successfully.")

    except sqlite3.IntegrityError:
        print("⚠️ Data already exists, skipping...")

    finally:
        conn.close()


if __name__ == "__main__":
    seed_data()
