import sqlite3
from typing import Optional, Tuple, List, Dict, Any
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

    @staticmethod
    def calculate_student_attendance_percentage(student_id: int, module_id: int) -> Dict[str, Any]:
        """
        Calculate attendance percentage for a specific student in a specific module.
        
        Args:
            student_id: The student's ID
            module_id: The module ID to calculate attendance for
            
        Returns:
            Dictionary containing:
            - student_id: Student ID
            - student_name: Student's full name
            - total_sessions: Total number of sessions for the module
            - attended_sessions: Number of sessions attended
            - attendance_percentage: Calculated percentage (0-100)
            - grade_contribution: Grade contribution based on grading rules (0-5)
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get student name
            cursor.execute(
                "SELECT full_name FROM users WHERE user_id = ? AND role = 'student'",
                (student_id,)
            )
            student_row = cursor.fetchone()
            if not student_row:
                return {
                    "student_id": student_id,
                    "student_name": "Unknown Student",
                    "total_sessions": 0,
                    "attended_sessions": 0,
                    "attendance_percentage": 0.0,
                    "grade_contribution": 0.0,
                    "error": "Student not found"
                }
            
            student_name = student_row[0]
            
            # Get total sessions for the module
            cursor.execute(
                "SELECT COUNT(*) FROM sessions WHERE module_id = ?",
                (module_id,)
            )
            total_sessions = cursor.fetchone()[0]
            
            if total_sessions == 0:
                return {
                    "student_id": student_id,
                    "student_name": student_name,
                    "total_sessions": 0,
                    "attended_sessions": 0,
                    "attendance_percentage": 0.0,
                    "grade_contribution": 0.0,
                    "error": "No sessions found for this module"
                }
            
            # Get attended sessions for the student in this module
            cursor.execute(
                """
                SELECT COUNT(*) FROM attendance a
                JOIN sessions s ON a.session_id = s.session_id
                WHERE a.student_id = ? AND s.module_id = ?
                """,
                (student_id, module_id)
            )
            attended_sessions = cursor.fetchone()[0]
            
            # Calculate attendance percentage
            attendance_percentage = (attended_sessions / total_sessions) * 100 if total_sessions > 0 else 0.0
            
            # Apply grading rule: max 5%, proportional to attendance
            grade_contribution = min(5.0, (attendance_percentage / 100) * 5.0)
            
            return {
                "student_id": student_id,
                "student_name": student_name,
                "total_sessions": total_sessions,
                "attended_sessions": attended_sessions,
                "attendance_percentage": round(attendance_percentage, 2),
                "grade_contribution": round(grade_contribution, 2),
                "error": None
            }
            
        except Exception as e:
            return {
                "student_id": student_id,
                "student_name": "Error",
                "total_sessions": 0,
                "attended_sessions": 0,
                "attendance_percentage": 0.0,
                "grade_contribution": 0.0,
                "error": f"Calculation error: {str(e)}"
            }
        finally:
            try:
                if 'conn' in locals():
                    conn.close()
            except Exception:
                pass

    @staticmethod
    def calculate_module_attendance_summary(module_id: int) -> Dict[str, Any]:
        """
        Calculate attendance summary for all students in a specific module.
        
        Args:
            module_id: The module ID to calculate attendance for
            
        Returns:
            Dictionary containing:
            - module_id: Module ID
            - module_info: Module details
            - total_sessions: Total number of sessions
            - student_attendance: List of student attendance records
            - module_average: Average attendance percentage for the module
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get module information
            cursor.execute(
                "SELECT module_code, module_name FROM modules WHERE module_id = ?",
                (module_id,)
            )
            module_row = cursor.fetchone()
            if not module_row:
                return {
                    "module_id": module_id,
                    "module_info": None,
                    "total_sessions": 0,
                    "student_attendance": [],
                    "module_average": 0.0,
                    "error": "Module not found"
                }
            
            module_code, module_name = module_row
            module_info = {
                "module_code": module_code,
                "module_name": module_name
            }
            
            # Get total sessions for the module
            cursor.execute(
                "SELECT COUNT(*) FROM sessions WHERE module_id = ?",
                (module_id,)
            )
            total_sessions = cursor.fetchone()[0]
            
            if total_sessions == 0:
                return {
                    "module_id": module_id,
                    "module_info": module_info,
                    "total_sessions": 0,
                    "student_attendance": [],
                    "module_average": 0.0,
                    "error": "No sessions found for this module"
                }
            
            # Get all students enrolled in this module (have attended at least one session)
            cursor.execute(
                """
                SELECT DISTINCT u.user_id, u.full_name
                FROM users u
                JOIN attendance a ON u.user_id = a.student_id
                JOIN sessions s ON a.session_id = s.session_id
                WHERE s.module_id = ? AND u.role = 'student'
                ORDER BY u.full_name
                """,
                (module_id,)
            )
            students = cursor.fetchall()
            
            student_attendance = []
            total_percentage = 0.0
            student_count = 0
            
            for student_id, student_name in students:
                # Calculate individual student attendance
                student_data = AttendanceService.calculate_student_attendance_percentage(student_id, module_id)
                if student_data.get("error") is None:
                    student_attendance.append(student_data)
                    total_percentage += student_data["attendance_percentage"]
                    student_count += 1
            
            # Calculate module average
            module_average = round(total_percentage / student_count, 2) if student_count > 0 else 0.0
            
            return {
                "module_id": module_id,
                "module_info": module_info,
                "total_sessions": total_sessions,
                "student_attendance": student_attendance,
                "module_average": module_average,
                "error": None
            }
            
        except Exception as e:
            return {
                "module_id": module_id,
                "module_info": None,
                "total_sessions": 0,
                "student_attendance": [],
                "module_average": 0.0,
                "error": f"Calculation error: {str(e)}"
            }
        finally:
            try:
                if 'conn' in locals():
                    conn.close()
            except Exception:
                pass

    @staticmethod
    def get_student_attendance_history(student_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get detailed attendance history for a specific student.
        
        Args:
            student_id: The student's ID
            limit: Maximum number of records to return (default: 50)
            
        Returns:
            List of attendance records with session details
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT 
                    a.session_id,
                    s.module_id,
                    m.module_code,
                    m.module_name,
                    s.week_number,
                    s.session_date,
                    a.checkin_time,
                    a.status
                FROM attendance a
                JOIN sessions s ON a.session_id = s.session_id
                JOIN modules m ON s.module_id = m.module_id
                WHERE a.student_id = ?
                ORDER BY s.session_date DESC, s.week_number DESC
                LIMIT ?
                """,
                (student_id, limit)
            )
            
            rows = cursor.fetchall()
            history = []
            
            for row in rows:
                history.append({
                    "session_id": row[0],
                    "module_id": row[1],
                    "module_code": row[2],
                    "module_name": row[3],
                    "week_number": row[4],
                    "session_date": row[5],
                    "checkin_time": row[6],
                    "status": row[7]
                })
            
            return history
            
        except Exception as e:
            return []
        finally:
            try:
                if 'conn' in locals():
                    conn.close()
            except Exception:
                pass

    @staticmethod
    def apply_grading_rule(attendance_percentage: float, max_grade: float = 5.0) -> float:
        """
        Apply the grading rule: max 5%, proportional to attendance percentage.
        
        Args:
            attendance_percentage: Student's attendance percentage (0-100)
            max_grade: Maximum grade contribution (default: 5.0)
            
        Returns:
            Grade contribution based on attendance (0 to max_grade)
        """
        if attendance_percentage < 0 or attendance_percentage > 100:
            return 0.0
        
        # Proportional grading: attendance_percentage / 100 * max_grade
        grade_contribution = (attendance_percentage / 100) * max_grade
        
        # Ensure it doesn't exceed max_grade
        return min(max_grade, grade_contribution)
