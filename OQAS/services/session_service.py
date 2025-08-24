import sqlite3, datetime, qrcode, io, base64, jwt
from config import DB_PATH, SECRET_KEY

class SessionController:

    @staticmethod
    def get_active_session(module_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, module_id, session_date, run_id, status 
            FROM sessions 
            WHERE module_id=? AND status='open'
        """, (module_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    @staticmethod
    def start_session(module_id: int, lecturer_id: int):
        # check if already active
        active = SessionController.get_active_session(module_id)
        if active:
            return None, "⚠️ Session already active."

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # get current run_id from app_runs
        cursor.execute("SELECT MAX(run_id) FROM app_runs")
        run_id = cursor.fetchone()[0]

        today = datetime.date.today().isoformat()

        cursor.execute("""
            INSERT INTO sessions(module_id, session_date, run_id, status) 
            VALUES (?, ?, ?, 'open')
        """, (module_id, today, run_id))
        conn.commit()

        session_id = cursor.lastrowid

        # generate QR token with PyJWT
        payload = {"module_id": module_id, "date": today, "run_id": run_id, "session_id": session_id}
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        # generate QR code image as base64
        img = qrcode.make(f"http://localhost:8000/checkin?tk={token}")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        conn.close()
        return {"session_id": session_id, "token": token, "qr": qr_b64}, None

    @staticmethod
    def close_session(session_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET status='closed' WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()
