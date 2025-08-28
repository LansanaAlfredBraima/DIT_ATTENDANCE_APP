#!/usr/bin/env python3
"""
Day 11 - Attendance Calculation Demo

Simple demonstration of how to use the new attendance calculation methods.
"""

from services.attendance_service import AttendanceService


def demo_basic_usage():
    """Demonstrate basic usage of attendance calculation methods."""
    print("🎯 Day 11 - Attendance Calculation Demo")
    print("=" * 50)
    
    # Example 1: Calculate attendance for a specific student and module
    print("\n📊 Example 1: Student Attendance Calculation")
    print("-" * 40)
    
    # Replace these with actual IDs from your database
    student_id = 905001234  # Example student ID
    module_id = 1           # Example module ID
    
    print(f"Calculating attendance for Student ID: {student_id}, Module ID: {module_id}")
    
    result = AttendanceService.calculate_student_attendance_percentage(student_id, module_id)
    
    if result.get("error"):
        print(f"❌ Error: {result['error']}")
        print("💡 Make sure you have students and modules in your database")
    else:
        print(f"✅ Student: {result['student_name']}")
        print(f"   Attendance: {result['attendance_percentage']}%")
        print(f"   Grade Contribution: {result['grade_contribution']}/5.0")
    
    # Example 2: Apply grading rule manually
    print("\n📈 Example 2: Manual Grading Rule Application")
    print("-" * 40)
    
    attendance_percentages = [0, 25, 50, 75, 100]
    for percentage in attendance_percentages:
        grade = AttendanceService.apply_grading_rule(percentage)
        print(f"Attendance: {percentage:3}% → Grade: {grade:4.2f}/5.0")
    
    # Example 3: Module summary (if data exists)
    print("\n📚 Example 3: Module Attendance Summary")
    print("-" * 40)
    
    module_id = 1  # Example module ID
    print(f"Getting summary for Module ID: {module_id}")
    
    summary = AttendanceService.calculate_module_attendance_summary(module_id)
    
    if summary.get("error"):
        print(f"❌ Error: {summary['error']}")
        print("💡 Make sure you have modules and attendance data in your database")
    else:
        print(f"✅ Module: {summary['module_info']['module_code']} - {summary['module_info']['module_name']}")
        print(f"   Total Sessions: {summary['total_sessions']}")
        print(f"   Students: {len(summary['student_attendance'])}")
        print(f"   Module Average: {summary['module_average']}%")
    
    print("\n" + "=" * 50)
    print("🎉 Demo Complete!")
    print("\nTo test with real data:")
    print("1. Make sure your database has students, modules, and attendance records")
    print("2. Update the student_id and module_id variables with real values")
    print("3. Run the test script: python test_attendance_calculation.py")


if __name__ == "__main__":
    demo_basic_usage()
