import sqlite3
from flask import g
from typing import Optional
from config import DB_PATH

# Request-scoped SQLite connection with foreign keys enabled
def get_db() -> sqlite3.Connection:
	conn: Optional[sqlite3.Connection] = getattr(g, "_db_conn", None)
	if conn is None:
		conn = sqlite3.connect(DB_PATH)
		conn.execute("PRAGMA foreign_keys = ON;")
		setattr(g, "_db_conn", conn)
	return conn

def close_db(_: Optional[BaseException] = None) -> None:
	conn: Optional[sqlite3.Connection] = getattr(g, "_db_conn", None)
	if conn is not None:
		conn.close()
		setattr(g, "_db_conn", None)

