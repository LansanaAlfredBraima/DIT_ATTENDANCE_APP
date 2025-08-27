import sqlite3
from typing import Optional, Tuple
from argon2 import PasswordHasher
from config import DB_PATH
from datetime import datetime


class AttendanceService:
    @staticmethod
    def submit_attendance(session_id: int, student_id: int, student_name: str) -> Tuple[bool, Optional[str]]:
        """Submit attendance record with enhanced validation and error handling.
        
        This method:
        - Prevents duplicates using unique index + logic
        - Saves to SQLite with timestamp
        - Returns success/error status
        
        Args:
            session_id: The session ID to record attendance for
            student_id: The student's ID (must be 9 digits starting with 90500)
            student_name: The student's full name
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Validate student ID format
            if not (str(student_id).isdigit() and len(str(student_id)) == 9 and str(student_id).startswith("90500")):
                return False, "Invalid student ID format. Must be 9 digits starting with 90500."
            
            # Validate student name
            if not student_name or len(student_name.strip()) < 2:
                return False, "Student name must be at least 2 characters long."
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            try:
                # Ensure session exists and is active
                cursor.execute(
                    "SELECT status, module_id FROM sessions WHERE session_id = ?",
                    (session_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return False, "Session not found."
                if row[0] != "active":
                    return False, "Session is not active."
                
                module_id = row[1]
                
                # Check if attendance already exists (duplicate prevention)
                cursor.execute(
                    "SELECT attendance_id FROM attendance WHERE session_id = ? AND student_id = ?",
                    (session_id, student_id),
                )
                if cursor.fetchone():
                    return False, "Student has already checked in for this session."
                
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
                
                # Insert attendance record with explicit timestamp
                current_timestamp = datetime.now().isoformat()
                cursor.execute(
                    """
                    INSERT INTO attendance (session_id, student_id, status, checkin_time)
                    VALUES (?, ?, 'present', ?)
                    """,
                    (session_id, student_id, current_timestamp),
                )
                conn.commit()
                
                return True, None
                
            except sqlite3.IntegrityError as e:
                # This should not happen due to our duplicate check, but handle it anyway
                if "UNIQUE constraint failed" in str(e):
                    return False, "Student has already checked in for this session."
                return False, f"Database constraint error: {str(e)}"
            except Exception as e:
                conn.rollback()
                return False, f"Database error: {str(e)}"
                
        except Exception as e:
            return False, f"System error: {str(e)}"
        finally:
            try:
                if 'conn' in locals():
                    conn.close()
            except Exception:
                pass

    @staticmethod
    def record_attendance(session_id: int, student_id: int, student_name: str) -> Tuple[bool, Optional[str]]:
        """Insert attendance record if not already present.
        
        This is the legacy method kept for backward compatibility.
        Consider using submit_attendance() for new implementations.

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

    @staticmethod
    def list_attendance_for_session(session_id: int):
        """Return list of attendance rows for a given session ordered by checkin_time asc.

        Each row contains: student_id, student_name (from users), checkin_time (ISO string).
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.student_id, u.full_name AS student_name, a.checkin_time
                FROM attendance a
                JOIN users u ON a.student_id = u.user_id
                WHERE a.session_id = ?
                ORDER BY a.checkin_time ASC
                """,
                (session_id,),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "student_id": r[0],
                    "student_name": r[1],
                    "timestamp": r[2],
                })
            return results
        except Exception:
            return []
        finally:
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass
