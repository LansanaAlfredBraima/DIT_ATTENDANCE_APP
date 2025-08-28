# Day 11 – Attendance Calculation

## Overview

Day 11 implements comprehensive attendance calculation functionality for the OQAS attendance system. This includes computing attendance percentages per student, applying grading rules, and providing detailed attendance analytics.

## 🎯 Features Implemented

### 1. Compute Attendance % Per Student
- **Method**: `calculate_student_attendance_percentage(student_id, module_id)`
- Calculates individual student attendance percentage for a specific module
- Returns comprehensive attendance data including grade contribution

### 2. Apply Grading Rule (Max 5%, Proportional)
- **Method**: `apply_grading_rule(attendance_percentage, max_grade=5.0)`
- Implements proportional grading: attendance percentage directly translates to grade contribution
- Maximum grade contribution capped at 5%
- Formula: `grade = (attendance_percentage / 100) * max_grade`

### 3. Additional Attendance Analytics
- **Module Summary**: `calculate_module_attendance_summary(module_id)`
- **Student History**: `get_student_attendance_history(student_id, limit=50)`

## 📊 Grading System

The grading system follows these principles:

| Attendance % | Grade Contribution | Description |
|--------------|-------------------|-------------|
| 0%           | 0.0/5.0          | No attendance |
| 25%          | 1.25/5.0         | Quarter attendance |
| 50%          | 2.5/5.0          | Half attendance |
| 75%          | 3.75/5.0         | Three-quarter attendance |
| 100%         | 5.0/5.0          | Perfect attendance |

**Key Features:**
- Proportional scaling: 1% attendance = 0.05 grade points
- Maximum cap: 5% of total grade
- Fair and transparent calculation

## 🔧 API Reference

### AttendanceService.calculate_student_attendance_percentage()

```python
def calculate_student_attendance_percentage(student_id: int, module_id: int) -> Dict[str, Any]:
    """
    Calculate attendance percentage for a specific student in a specific module.
    
    Returns:
        {
            "student_id": int,
            "student_name": str,
            "total_sessions": int,
            "attended_sessions": int,
            "attendance_percentage": float,
            "grade_contribution": float,
            "error": Optional[str]
        }
    """
```

**Example Usage:**
```python
from services.attendance_service import AttendanceService

result = AttendanceService.calculate_student_attendance_percentage(905001234, 1)
if result.get("error") is None:
    print(f"Attendance: {result['attendance_percentage']}%")
    print(f"Grade: {result['grade_contribution']}/5.0")
```

### AttendanceService.apply_grading_rule()

```python
def apply_grading_rule(attendance_percentage: float, max_grade: float = 5.0) -> float:
    """
    Apply the grading rule: max 5%, proportional to attendance percentage.
    
    Args:
        attendance_percentage: Student's attendance percentage (0-100)
        max_grade: Maximum grade contribution (default: 5.0)
    
    Returns:
        Grade contribution based on attendance (0 to max_grade)
    """
```

**Example Usage:**
```python
grade = AttendanceService.apply_grading_rule(75.0)  # Returns 3.75
grade = AttendanceService.apply_grading_rule(100.0) # Returns 5.0
grade = AttendanceService.apply_grading_rule(50.0)  # Returns 2.5
```

### AttendanceService.calculate_module_attendance_summary()

```python
def calculate_module_attendance_summary(module_id: int) -> Dict[str, Any]:
    """
    Calculate attendance summary for all students in a specific module.
    
    Returns:
        {
            "module_id": int,
            "module_info": Dict,
            "total_sessions": int,
            "student_attendance": List[Dict],
            "module_average": float,
            "error": Optional[str]
        }
    """
```

### AttendanceService.get_student_attendance_history()

```python
def get_student_attendance_history(student_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get detailed attendance history for a specific student.
    
    Returns:
        List of attendance records with session details
    """
```

## 🧪 Testing

### Run the Test Script
```bash
python test_attendance_calculation.py
```

This comprehensive test script demonstrates:
- Grading rule application
- Student attendance calculation
- Module attendance summary
- Student attendance history
- Error handling

### Run the Demo Script
```bash
python demo_attendance_calculation.py
```

Simple demonstration of basic usage patterns.

## 📁 File Structure

```
services/
├── attendance_service.py          # Main service with new methods
├── __init__.py
└── ...

test_attendance_calculation.py    # Comprehensive test suite
demo_attendance_calculation.py    # Basic usage demonstration
DAY_11_README.md                  # This documentation
```

## 🚀 Getting Started

1. **Ensure Database Setup**: Make sure you have students, modules, and attendance records in your database
2. **Import the Service**: `from services.attendance_service import AttendanceService`
3. **Calculate Attendance**: Use the methods to compute attendance percentages and grades
4. **Apply Grading**: Use the grading rule to determine grade contributions

## 🔍 Error Handling

All methods include comprehensive error handling:
- Database connection errors
- Missing students/modules
- Invalid data scenarios
- Graceful fallbacks with descriptive error messages

## 📈 Use Cases

### For Lecturers
- Monitor individual student attendance
- Calculate grade contributions
- Generate module attendance reports

### For Administrators
- Track attendance patterns across modules
- Generate institutional reports
- Monitor student engagement

### For Students
- View personal attendance history
- Understand grade implications
- Track progress over time

## 🔮 Future Enhancements

Potential areas for expansion:
- Weighted attendance (different session types)
- Attendance trends analysis
- Export functionality for reports
- Integration with learning management systems
- Advanced analytics and visualizations

## 📝 Notes

- All percentages are calculated as `(attended_sessions / total_sessions) * 100`
- Grade contributions are automatically capped at the maximum specified
- Database queries are optimized for performance
- All methods are thread-safe and can be used concurrently

---

**Day 11 Complete!** 🎉

The attendance calculation system is now fully functional with comprehensive grading rules and analytics capabilities.
