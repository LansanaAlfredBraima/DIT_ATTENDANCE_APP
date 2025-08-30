import sqlite3, datetime, qrcode, io, base64, jwt, secrets
from config import DB_PATH, SECRET_KEY, PORT
from services.qr_services import QRService

class SessionController:

    @staticmethod
    def get_active_session(module_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, module_id, session_date, run_id, status 
            FROM sessions 
            WHERE module_id=? AND session_date=? AND status='active'
        """, (module_id, datetime.date.today().isoformat()))
        row = cursor.fetchone()
        conn.close()
        return row

    @staticmethod
    def start_session(module_id: int, lecturer_id: int, week_number: int | None = None):
        # enforce one session per ISO week; expire lingering active >3h
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # ensure an app run exists with a session_seed
        cursor.execute("SELECT run_id, session_seed FROM app_runs ORDER BY run_id DESC LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            session_seed = secrets.token_urlsafe(24)
            cursor.execute("INSERT INTO app_runs(session_seed) VALUES (?)", (session_seed,))
            conn.commit()
            run_id = cursor.lastrowid
        else:
            run_id = row[0]

        today = datetime.date.today().isoformat()
        # Use provided week number if valid, otherwise default to current ISO week
        try:
            if week_number is not None:
                week_number = int(week_number)
                if week_number < 1:
                    week_number = datetime.date.today().isocalendar()[1]
            else:
                week_number = datetime.date.today().isocalendar()[1]
        except Exception:
            week_number = datetime.date.today().isocalendar()[1]

        # expire any active session older than 3 hours
        cursor.execute(
            """
            UPDATE sessions
            SET status='ended', ended_at=CURRENT_TIMESTAMP
            WHERE module_id=? AND status='active'
              AND (julianday('now') - julianday(created_at)) > (3.0/24.0)
            """,
            (module_id,)
        )

        # If a session already exists for this module and week, reuse it.
        cursor.execute(
            """
            SELECT session_id, status FROM sessions
            WHERE module_id=? AND week_number=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (module_id, week_number)
        )
        existing = cursor.fetchone()
        if existing is not None:
            existing_session_id, existing_status = existing
            if existing_status != 'active':
                cursor.execute(
                    """
                    UPDATE sessions
                    SET status='active', ended_at=NULL
                    WHERE session_id=?
                    """,
                    (existing_session_id,)
                )
                conn.commit()
            # Build QR for the reused session
            token, qr_b64 = QRService.build_for_session(module_id=module_id, run_id=run_id, session_id=existing_session_id, date=today)
            conn.close()
            return {"session_id": existing_session_id, "token": token, "qr": qr_b64}, None
        cursor.execute("""
            INSERT INTO sessions(module_id, week_number, session_date, status, run_id) 
            VALUES (?, ?, ?, 'active', ?)
        """, (module_id, week_number, today, run_id))
        conn.commit()

        session_id = cursor.lastrowid

        # generate token + QR via QRService
        token, qr_b64 = QRService.build_for_session(module_id=module_id, run_id=run_id, session_id=session_id, date=today)

        conn.close()
        return {"session_id": session_id, "token": token, "qr": qr_b64}, None

    @staticmethod
    def close_session(session_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET status='ended', ended_at = CURRENT_TIMESTAMP WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()
