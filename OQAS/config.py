import os
import secrets

# Base project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database path
DB_PATH = os.path.join(BASE_DIR, "db", "oqas.db")

# Secret key for Flask (used later for sessions/JWT)
SECRET_KEY = secrets.token_hex(32)

# Default app port
PORT = 8000
