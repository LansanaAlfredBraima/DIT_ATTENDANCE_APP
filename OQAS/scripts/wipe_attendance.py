import sqlite3
import os, sys

# Ensure project root is on sys.path so we can import config
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)

from config import DB_PATH

def main() -> None:
	conn = sqlite3.connect(DB_PATH)
	try:
		cur = conn.cursor()
		before = cur.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
		cur.execute("DELETE FROM attendance")
		conn.commit()
		after = cur.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
		print(f"Deleted rows: {before - after} (remaining: {after})")
	finally:
		conn.close()

if __name__ == "__main__":
	main()


