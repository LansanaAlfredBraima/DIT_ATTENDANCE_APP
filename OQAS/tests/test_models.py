import sqlite3
from models.course import Course
from models.lecturer import Lecturer
from models.module import Module

DB_PATH = "db/oqas.db"

def test_models():
    # Test dataclass Course
    c = Course("Database Systems", "CS101", 3)
    print(c)

    # Test Lecturer
    lect = Lecturer(user_id=2, username="lect1", role="lecturer", full_name="Alisine Jalloh")
    lect.login()

    # Test fetching modules from DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT module_id, module_code, module_name, lecturer_id FROM modules")
    rows = cursor.fetchall()
    for row in rows:
        mod = Module(*row)
        mod.describe()

    conn.close()
    print("✅ Models working")

if __name__ == "__main__":
    test_models()
