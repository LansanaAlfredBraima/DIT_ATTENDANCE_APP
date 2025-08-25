import os
import secrets
import socket

# Base project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(BASE_DIR, "db", "oqas.db")

# Secret key for Flask (used later for sessions/JWT)
SECRET_KEY = secrets.token_hex(32)

# Default app port
PORT = 8000

def _detect_lan_ip() -> str:
    try:
        # This opens a dummy UDP socket to a public IP to discover the outbound interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

# Optional LAN host/IP for building external URLs (e.g., QR scan from phone)
# Can be overridden by environment variable LAN_HOST; otherwise auto-detects.
LAN_HOST = os.environ.get("LAN_HOST", _detect_lan_ip())