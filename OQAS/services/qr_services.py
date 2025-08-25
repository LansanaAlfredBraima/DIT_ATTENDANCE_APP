import qrcode, io, base64, jwt
from typing import Dict, Tuple, Optional
from config import SECRET_KEY, PORT, LAN_HOST

class QRService:
    @staticmethod
    def generate_token(payload: Dict) -> str:
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  # type: ignore[no-any-return]
        except Exception:
            return None

    @staticmethod
    def make_qr_png_b64(url: str) -> str:
        img = qrcode.make(url)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def build_checkin_url(token: str) -> str:
        host = LAN_HOST or "localhost"
        return f"http://{host}:{PORT}/checkin?tk={token}"

    @staticmethod
    def build_for_session(module_id: int, run_id: int, session_id: int, date: str) -> Tuple[str, str]:
        payload = {"module_id": module_id, "run_id": run_id, "session_id": session_id, "date": date}
        token = QRService.generate_token(payload)
        url = QRService.build_checkin_url(token)
        return token, QRService.make_qr_png_b64(url)
