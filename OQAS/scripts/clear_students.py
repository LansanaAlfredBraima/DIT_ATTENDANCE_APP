import os
import sys
import sqlite3

# Ensure project root is on sys.path so we can import config
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DB_PATH


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        # Count current students and related attendance
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'")
        student_count_before = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*) FROM attendance
            WHERE student_id IN (SELECT user_id FROM users WHERE role='student')
            """
        )
        attendance_count_before = cursor.fetchone()[0]

        # Delete attendance for student users
        cursor.execute(
            """
            DELETE FROM attendance
            WHERE student_id IN (SELECT user_id FROM users WHERE role='student')
            """
        )
        conn.commit()

        # Delete student users
        cursor.execute("DELETE FROM users WHERE role='student'")
        conn.commit()

        # Report after
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'")
        student_count_after = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*) FROM attendance
            WHERE student_id IN (SELECT user_id FROM users WHERE role='student')
            """
        )
        attendance_count_after = cursor.fetchone()[0]

        print(
            f"Deleted students: {student_count_before - student_count_after} (remaining: {student_count_after})"
        )
        print(
            f"Deleted attendance rows: {attendance_count_before} (remaining linked to students: {attendance_count_after})"
        )

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()


