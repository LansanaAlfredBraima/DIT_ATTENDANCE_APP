#!/usr/bin/env python3
"""
Day 11 - Attendance Calculation Test Script

This script demonstrates the new attendance calculation functionality:
1. Compute attendance % per student
2. Apply grading rule (max 5%, proportional)
3. Test all new AttendanceService methods

Run this script to test the attendance calculation features.
"""

import sys
import os

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.attendance_service import AttendanceService
from config import DB_PATH
import sqlite3


def test_attendance_calculation():
    """Test the attendance calculation functionality."""
    print("🎯 Day 11 - Attendance Calculation Test")
    print("=" * 50)
    
    # Test 1: Apply grading rule function
    print("\n📊 Test 1: Grading Rule Application")
    print("-" * 40)
    
    test_percentages = [0, 25, 50, 75, 100, 120, -10]
    for percentage in test_percentages:
        grade = AttendanceService.apply_grading_rule(percentage)
        print(f"Attendance: {percentage:3}% → Grade: {grade:4.2f}/5.0")
    
    # Test 2: Calculate student attendance percentage
    print("\n👤 Test 2: Student Attendance Percentage")
    print("-" * 40)
    
    # Get a sample student and module from the database
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get first available student
        cursor.execute(
            "SELECT user_id, full_name FROM users WHERE role = 'student' LIMIT 1"
        )
        student_row = cursor.fetchone()
        
        if student_row:
            student_id, student_name = student_row
            print(f"Testing with student: {student_name} (ID: {student_id})")
            
            # Get first available module
            cursor.execute("SELECT module_id, module_code, module_name FROM modules LIMIT 1")
            module_row = cursor.fetchone()
            
            if module_row:
                module_id, module_code, module_name = module_row
                print(f"Testing with module: {module_code} - {module_name}")
                
                # Calculate attendance percentage
                result = AttendanceService.calculate_student_attendance_percentage(student_id, module_id)
                
                if result.get("error"):
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"✅ Student: {result['student_name']}")
                    print(f"   Total Sessions: {result['total_sessions']}")
                    print(f"   Attended Sessions: {result['attended_sessions']}")
                    print(f"   Attendance Percentage: {result['attendance_percentage']}%")
                    print(f"   Grade Contribution: {result['grade_contribution']}/5.0")
            else:
                print("❌ No modules found in database")
        else:
            print("❌ No students found in database")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # Test 3: Module attendance summary
    print("\n📚 Test 3: Module Attendance Summary")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get first available module
        cursor.execute("SELECT module_id, module_code, module_name FROM modules LIMIT 1")
        module_row = cursor.fetchone()
        
        if module_row:
            module_id, module_code, module_name = module_row
            print(f"Testing with module: {module_code} - {module_name}")
            
            # Calculate module attendance summary
            summary = AttendanceService.calculate_module_attendance_summary(module_id)
            
            if summary.get("error"):
                print(f"❌ Error: {summary['error']}")
            else:
                print(f"✅ Module: {summary['module_info']['module_code']} - {summary['module_info']['module_name']}")
                print(f"   Total Sessions: {summary['total_sessions']}")
                print(f"   Students with Attendance: {len(summary['student_attendance'])}")
                print(f"   Module Average: {summary['module_average']}%")
                
                # Show top 3 students by attendance
                if summary['student_attendance']:
                    print("\n   Top Students by Attendance:")
                    sorted_students = sorted(
                        summary['student_attendance'], 
                        key=lambda x: x['attendance_percentage'], 
                        reverse=True
                    )
                    for i, student in enumerate(sorted_students[:3], 1):
                        print(f"     {i}. {student['student_name']}: {student['attendance_percentage']}% (Grade: {student['grade_contribution']}/5.0)")
        else:
            print("❌ No modules found in database")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # Test 4: Student attendance history
    print("\n📅 Test 4: Student Attendance History")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get first available student
        cursor.execute(
            "SELECT user_id, full_name FROM users WHERE role = 'student' LIMIT 1"
        )
        student_row = cursor.fetchone()
        
        if student_row:
            student_id, student_name = student_row
            print(f"Testing with student: {student_name} (ID: {student_id})")
            
            # Get attendance history
            history = AttendanceService.get_student_attendance_history(student_id, limit=5)
            
            if history:
                print(f"✅ Found {len(history)} attendance records:")
                for i, record in enumerate(history, 1):
                    print(f"   {i}. Week {record['week_number']}: {record['module_code']} - {record['session_date']}")
            else:
                print("ℹ️  No attendance history found for this student")
        else:
            print("❌ No students found in database")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Day 11 Attendance Calculation Tests Complete!")
    print("\nImplemented Features:")
    print("✅ Compute attendance % per student")
    print("✅ Apply grading rule (max 5%, proportional)")
    print("✅ Module attendance summary")
    print("✅ Student attendance history")
    print("✅ Comprehensive error handling")


def demonstrate_grading_calculation():
    """Demonstrate the grading calculation with examples."""
    print("\n📈 Grading Calculation Examples")
    print("=" * 40)
    
    examples = [
        (0, "No attendance"),
        (25, "Quarter attendance"),
        (50, "Half attendance"),
        (75, "Three-quarter attendance"),
        (100, "Perfect attendance"),
        (85, "Good attendance"),
        (60, "Moderate attendance")
    ]
    
    print(f"{'Attendance %':<15} {'Grade/5.0':<12} {'Description':<25}")
    print("-" * 52)
    
    for percentage, description in examples:
        grade = AttendanceService.apply_grading_rule(percentage)
        print(f"{percentage:>3}%{'':<12} {grade:>6.2f}/5.0{'':<6} {description}")


if __name__ == "__main__":
    try:
        test_attendance_calculation()
        demonstrate_grading_calculation()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
