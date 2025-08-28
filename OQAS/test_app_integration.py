#!/usr/bin/env python3
"""
Integration tests for Day 11 attendance calculation endpoints in app.py

- GET /api/attendance/student/<student_id>/module/<module_id>
- GET /api/attendance/module/<module_id>/summary
"""

import os
import sys
import json
import sqlite3

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app import app  # Flask app
from config import DB_PATH


def get_any_module_and_lecturer():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT module_id, lecturer_id FROM modules LIMIT 1")
        row = cur.fetchone()
        if not row:
            return None, None
        return row[0], row[1]
    finally:
        conn.close()


def get_any_student_for_module(module_id: int):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT a.student_id
            FROM attendance a
            JOIN sessions s ON a.session_id = s.session_id
            WHERE s.module_id = ?
            LIMIT 1
            """,
            (module_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return row[0]
    finally:
        conn.close()


def run_tests():
    print("🎯 Running integration tests for attendance endpoints")

    module_id, lecturer_id = get_any_module_and_lecturer()
    if not module_id or not lecturer_id:
        print("❌ No modules/lecturers found in DB. Seed data and try again.")
        return

    student_id = get_any_student_for_module(module_id)
    if not student_id:
        print("ℹ️ No student attendance found for module; student endpoint will be skipped.")

    client = app.test_client()

    # Simulate lecturer session
    with client.session_transaction() as sess:
        sess['user'] = {
            'user_id': lecturer_id,
            'role': 'lecturer',
            'username': f'lecturer_{lecturer_id}'
        }

    # Test module summary endpoint
    print(f"\n📚 GET /api/attendance/module/{module_id}/summary")
    resp = client.get(f"/api/attendance/module/{module_id}/summary")
    print(f"Status: {resp.status_code}")
    try:
        data = resp.get_json()
        print(json.dumps(data, indent=2))
    except Exception:
        print(resp.data.decode()[:500])

    # Test student attendance endpoint if a student exists
    if student_id:
        print(f"\n👤 GET /api/attendance/student/{student_id}/module/{module_id}")
        resp2 = client.get(f"/api/attendance/student/{student_id}/module/{module_id}")
        print(f"Status: {resp2.status_code}")
        try:
            data2 = resp2.get_json()
            print(json.dumps(data2, indent=2))
        except Exception:
            print(resp2.data.decode()[:500])

    print("\n✅ Integration tests finished")


if __name__ == "__main__":
    run_tests()
