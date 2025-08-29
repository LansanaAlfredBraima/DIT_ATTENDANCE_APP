import os
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from argon2 import PasswordHasher
from config import DB_PATH


ph = PasswordHasher()


class AdminService:
    """Administrative operations for users (lecturers) and modules, and DB backup/restore."""

    # ---------------------- Lecturers ----------------------
    @staticmethod
    def list_lecturers() -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT user_id, username, full_name
                FROM users
                WHERE role = 'lecturer'
                ORDER BY username
                """
            )
            rows = cursor.fetchall()
            return [
                {"user_id": r[0], "username": r[1], "full_name": r[2]} for r in rows
            ]
        finally:
            conn.close()

    @staticmethod
    def create_lecturer(username: str, full_name: str, password: str) -> Tuple[bool, Optional[str]]:
        if not username or not full_name or not password:
            return False, "All fields are required"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, full_name)
                VALUES (?, ?, 'lecturer', ?)
                """,
                (username, ph.hash(password), full_name),
            )
            conn.commit()
            return True, None
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        finally:
            conn.close()

    @staticmethod
    def reset_lecturer_password(user_id: int, new_password: str) -> Tuple[bool, Optional[str]]:
        if not new_password:
            return False, "New password is required"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE user_id = ? AND role = 'lecturer'",
                (ph.hash(new_password), user_id),
            )
            if cursor.rowcount == 0:
                return False, "Lecturer not found"
            conn.commit()
            return True, None
        finally:
            conn.close()

    @staticmethod
    def delete_lecturer(user_id: int) -> Tuple[bool, Optional[str]]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE user_id = ? AND role = 'lecturer'", (user_id,))
            if cursor.rowcount == 0:
                return False, "Lecturer not found"
            conn.commit()
            return True, None
        except sqlite3.IntegrityError as e:
            return False, f"Cannot delete lecturer: {str(e)}"
        finally:
            conn.close()

    # ---------------------- Modules ----------------------
    @staticmethod
    def list_modules() -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT m.module_id, m.module_code, m.module_name, m.planned_weeks,
                       u.user_id, u.full_name
                FROM modules m
                JOIN users u ON m.lecturer_id = u.user_id
                ORDER BY m.module_code
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "module_id": r[0],
                    "module_code": r[1],
                    "module_name": r[2],
                    "planned_weeks": r[3],
                    "lecturer_id": r[4],
                    "lecturer_name": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()

    @staticmethod
    def create_module(module_code: str, module_name: str, lecturer_id: int, planned_weeks: int = 14) -> Tuple[bool, Optional[str]]:
        if not module_code or not module_name or not lecturer_id:
            return False, "module_code, module_name, lecturer_id are required"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO modules (module_code, module_name, lecturer_id, planned_weeks)
                VALUES (?, ?, ?, ?)
                """,
                (module_code, module_name, lecturer_id, planned_weeks or 14),
            )
            conn.commit()
            return True, None
        except sqlite3.IntegrityError:
            return False, "Module code already exists"
        finally:
            conn.close()

    @staticmethod
    def update_module(module_id: int, module_code: str, module_name: str, lecturer_id: int, planned_weeks: int) -> Tuple[bool, Optional[str]]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE modules
                SET module_code = ?, module_name = ?, lecturer_id = ?, planned_weeks = ?
                WHERE module_id = ?
                """,
                (module_code, module_name, lecturer_id, planned_weeks, module_id),
            )
            if cursor.rowcount == 0:
                return False, "Module not found"
            conn.commit()
            return True, None
        except sqlite3.IntegrityError:
            return False, "Module code already exists"
        finally:
            conn.close()

    @staticmethod
    def delete_module(module_id: int) -> Tuple[bool, Optional[str]]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM modules WHERE module_id = ?", (module_id,))
            if cursor.rowcount == 0:
                return False, "Module not found"
            conn.commit()
            return True, None
        finally:
            conn.close()

    # ---------------------- Backup/Restore ----------------------
    @staticmethod
    def backup_database(target_dir: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Create a copy of the SQLite DB file in target_dir. Returns (ok, error, filepath)."""
        try:
            os.makedirs(target_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"oqas_backup_{timestamp}.sqlite3"
            dest_path = os.path.join(target_dir, filename)
            # Use shutil.copy2 for metadata preservation
            shutil.copy2(DB_PATH, dest_path)
            return True, None, dest_path
        except Exception as e:
            return False, str(e), None

    @staticmethod
    def restore_database(source_path: str) -> Tuple[bool, Optional[str]]:
        """Replace current DB with the provided file, after making an automatic backup."""
        if not os.path.isfile(source_path):
            return False, "Source file does not exist"
        try:
            # Auto-backup current DB next to it
            current_dir = os.path.dirname(DB_PATH)
            os.makedirs(current_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(current_dir, f"auto_backup_before_restore_{timestamp}.sqlite3")
            if os.path.exists(DB_PATH):
                shutil.copy2(DB_PATH, backup_path)
            # Replace
            shutil.copy2(source_path, DB_PATH)
            return True, None
        except Exception as e:
            return False, str(e)


