import sqlite3
from argon2 import PasswordHasher
from config import DB_PATH

ph = PasswordHasher()

class AuthService:
    @staticmethod
    def login(username: str, password: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, username, password_hash, role, full_name FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            raise ValueError("Invalid credentials")

        user_id, db_username, password_hash, role, full_name = row

        try:
            ph.verify(password_hash, password)
        except Exception:
            raise ValueError("Invalid credentials")

        # Return user as dict
        return {
            "user_id": user_id,
            "username": db_username,
            "role": role,
            "full_name": full_name
        }

    @staticmethod
    def is_admin(user: dict) -> bool:
        return user.get("role") == "admin"

    @staticmethod
    def is_lecturer(user: dict) -> bool:
        return user.get("role") == "lecturer"

    @staticmethod
    def change_password(user_id: int, current_password: str, new_password: str) -> bool:
        """Verify current password and update to a new password for the given user_id."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False
            try:
                ph.verify(row[0], current_password)
            except Exception:
                return False
            new_hash = ph.hash(new_password)
            cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_hash, user_id))
            conn.commit()
            return True
        finally:
            conn.close()


