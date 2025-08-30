import sqlite3
from datetime import datetime, date
from config import DB_PATH
from typing import List, Dict, Optional

class ModuleService:
    @staticmethod
    def get_modules_by_lecturer(lecturer_id: int) -> List[Dict]:
        """Get all modules for a specific lecturer"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT module_id, module_code, module_name, planned_weeks, created_at
                FROM modules 
                WHERE lecturer_id = ?
                ORDER BY module_code
            """, (lecturer_id,))
            
            rows = cursor.fetchall()
            modules = []
            
            for row in rows:
                modules.append({
                    'module_id': row[0],
                    'module_code': row[1],
                    'module_name': row[2],
                    'planned_weeks': row[3],
                    'created_at': row[4]
                })
            
            return modules
        finally:
            conn.close()
    
    @staticmethod
    def get_active_session(module_id: int) -> Optional[Dict]:
        """Get the currently active session for a module"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT session_id, week_number, session_date, created_at
                FROM sessions 
                WHERE module_id = ? AND session_date = ? AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """, (module_id, date.today().isoformat()))
            
            row = cursor.fetchone()
            if row:
                return {
                    'session_id': row[0],
                    'week_number': row[1],
                    'session_date': row[2],
                    'created_at': row[3]
                }
            return None
        finally:
            conn.close()
    
    @staticmethod
    def start_session(module_id: int, week_number: int) -> bool:
        """Start a new session for a module.

        Enforces: at most one session per module per ISO week. Also expires any
        lingering active session older than 3 hours before attempting to start.
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Expire any active session older than 3 hours
            cursor.execute(
                """
                UPDATE sessions
                SET status = 'ended', ended_at = CURRENT_TIMESTAMP
                WHERE module_id = ? AND status = 'active'
                  AND (julianday('now') - julianday(created_at)) > (3.0/24.0)
                """,
                (module_id,)
            )

            # If a session exists for this module and week, reactivate it to continue
            cursor.execute(
                """
                SELECT session_id, status FROM sessions
                WHERE module_id = ? AND week_number = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (module_id, week_number)
            )
            existing = cursor.fetchone()
            if existing is not None:
                session_id, status = existing
                if status != 'active':
                    cursor.execute(
                        "UPDATE sessions SET status='active', ended_at=NULL WHERE session_id=?",
                        (session_id,)
                    )
                    conn.commit()
                return True

            # Insert new session (allow multiple per day)
            cursor.execute("""
                INSERT INTO sessions (module_id, week_number, session_date, status)
                VALUES (?, ?, ?, 'active')
            """, (module_id, week_number, date.today().isoformat()))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error starting session: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def close_session(module_id: int) -> bool:
        """Close the active session for a module"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Get the active session for today
            cursor.execute("""
                UPDATE sessions 
                SET status = 'ended', ended_at = CURRENT_TIMESTAMP
                WHERE module_id = ? AND session_date = ? AND status = 'active'
            """, (module_id, date.today().isoformat()))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            else:
                return False  # No active session found
        except Exception as e:
            print(f"Error closing session: {e}")
            return False
        finally:
            conn.close()
