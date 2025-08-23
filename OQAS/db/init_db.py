import sqlite3
import os
import sys

# Ensure project root is on sys.path so `from config import DB_PATH` works when running this file directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DB_PATH


def create_tables(cursor: sqlite3.Cursor) -> None:
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Modules table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS modules (
            module_id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_code TEXT NOT NULL UNIQUE,
            module_name TEXT NOT NULL,
            lecturer_id INTEGER NOT NULL,
            planned_weeks INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lecturer_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
        """
    )

    # Sessions table (each teaching session for a module)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            session_date DATE NOT NULL,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'ended')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP NULL,
            FOREIGN KEY (module_id) REFERENCES modules(module_id) ON DELETE CASCADE ON UPDATE CASCADE,
            UNIQUE (module_id, week_number, session_date)
        );
        """
    )

    # Attendance table (student check-ins per session)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT DEFAULT 'present',
            checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
            UNIQUE (session_id, student_id)
        );
        """
    )


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        create_tables(cursor)
        conn.commit()
        print(f"✅ Database initialized at: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()


