import os
import socket

# Base project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(BASE_DIR, "db", "oqas.db")

# Secret key for Flask (sessions/CSRF). In production, set SECRET_KEY env var.
# Falling back to a fixed dev key avoids logging out all users on every restart.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

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