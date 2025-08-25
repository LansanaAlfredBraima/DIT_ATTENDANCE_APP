import sqlite3
from typing import Optional, Tuple
from argon2 import PasswordHasher
from config import DB_PATH


class AttendanceService:
    @staticmethod
    def record_attendance(session_id: int, student_id: int, student_name: str) -> Tuple[bool, Optional[str]]:
        """Insert attendance record if not already present.

        Returns (ok, error_message).
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Ensure session exists and is active
            cursor.execute(
                "SELECT status FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return False, "Session not found."
            if row[0] != "active":
                return False, "Session is not active."

            # Ensure student exists; if not, create a student user with this ID
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?",
                (student_id,),
            )
            if cursor.fetchone() is None:
                ph = PasswordHasher()
                placeholder_password_hash = ph.hash("temp-password")
                username = str(student_id)
                cursor.execute(
                    """
                    INSERT INTO users (user_id, username, password_hash, role, full_name)
                    VALUES (?, ?, ?, 'student', ?)
                    """,
                    (student_id, username, placeholder_password_hash, student_name),
                )
                conn.commit()

            # Insert attendance (unique on session_id, student_id)
            try:
                cursor.execute(
                    """
                    INSERT INTO attendance (session_id, student_id, status)
                    VALUES (?, ?, 'present')
                    """,
                    (session_id, student_id),
                )
                conn.commit()
                return True, None
            except sqlite3.IntegrityError:
                return False, "Already checked in."
        except Exception as e:
            return False, str(e)
        finally:
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass

