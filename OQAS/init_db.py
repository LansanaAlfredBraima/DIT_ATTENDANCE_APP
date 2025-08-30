import sqlite3
import os
import sys

# Ensure project root is on sys.path so `from config import DB_PATH` works
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DB_PATH

# Ensure the database folder exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def create_tables(cursor: sqlite3.Cursor) -> None:
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Modules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            module_id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_code TEXT NOT NULL UNIQUE,
            module_name TEXT NOT NULL,
            lecturer_id INTEGER NOT NULL,
            planned_weeks INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lecturer_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            session_date DATE NOT NULL,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'ended')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP NULL,
            FOREIGN KEY (module_id) REFERENCES modules(module_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)

    # Attendance table
    cursor.execute("""
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
    """)

    # Ensure supporting unique index exists (for older DBs)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_session_student
        ON attendance (session_id, student_id);
    """)

    # App runs table to store per-run session_seed
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_seed TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Session audit trail (reopen/close actions, notes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_audit (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            actor_user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (actor_user_id) REFERENCES users(user_id) ON DELETE SET NULL ON UPDATE CASCADE
        );
    """)

    # Ensure sessions table has run_id column (backward-compatible migration)
    cursor.execute("PRAGMA table_info(sessions);")
    columns = [row[1] for row in cursor.fetchall()]
    if 'run_id' not in columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN run_id INTEGER NULL;")

    # If there is a UNIQUE index from an older schema, rebuild table without it
    cursor.execute("PRAGMA index_list('sessions');")
    unique_indexes = [row for row in cursor.fetchall() if row[2] == 1]
    if unique_indexes:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions_new (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER NOT NULL,
                week_number INTEGER NOT NULL,
                session_date DATE NOT NULL,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'ended')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP NULL,
                run_id INTEGER NULL,
                FOREIGN KEY (module_id) REFERENCES modules(module_id) ON DELETE CASCADE ON UPDATE CASCADE
            );
        """)
        cursor.execute("""
            INSERT INTO sessions_new(session_id, module_id, week_number, session_date, status, created_at, ended_at, run_id)
            SELECT session_id, module_id, week_number, session_date, status, created_at, ended_at, run_id FROM sessions;
        """)
        cursor.execute("DROP TABLE sessions;")
        cursor.execute("ALTER TABLE sessions_new RENAME TO sessions;")

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
