#!/usr/bin/env python3
"""
Day 11 - Attendance Calculation Integration Examples

Practical examples showing how to integrate the new attendance calculation
methods into real application scenarios.
"""

from services.attendance_service import AttendanceService
from typing import Dict, List, Any


class AttendanceCalculator:
    """Utility class for common attendance calculation tasks."""
    
    @staticmethod
    def get_student_grade_report(student_id: int, module_id: int) -> Dict[str, Any]:
        """
        Generate a comprehensive grade report for a student in a specific module.
        
        Args:
            student_id: Student ID
            module_id: Module ID
            
        Returns:
            Formatted grade report dictionary
        """
        # Get attendance data
        attendance_data = AttendanceService.calculate_student_attendance_percentage(
            student_id, module_id
        )
        
        if attendance_data.get("error"):
            return {
                "success": False,
                "error": attendance_data["error"],
                "report": None
            }
        
        # Calculate additional metrics
        missed_sessions = attendance_data["total_sessions"] - attendance_data["attended_sessions"]
        attendance_ratio = attendance_data["attended_sessions"] / attendance_data["total_sessions"]
        
        # Generate grade report
        report = {
            "student_info": {
                "id": attendance_data["student_id"],
                "name": attendance_data["student_name"]
            },
            "attendance_summary": {
                "total_sessions": attendance_data["total_sessions"],
                "attended_sessions": attendance_data["attended_sessions"],
                "missed_sessions": missed_sessions,
                "attendance_percentage": attendance_data["attendance_percentage"],
                "attendance_ratio": round(attendance_ratio, 3)
            },
            "grade_contribution": {
                "points": attendance_data["grade_contribution"],
                "max_points": 5.0,
                "percentage_of_total": round((attendance_data["grade_contribution"] / 5.0) * 100, 1)
            },
            "recommendations": AttendanceCalculator._generate_recommendations(attendance_data)
        }
        
        return {
            "success": True,
            "error": None,
            "report": report
        }
    
    @staticmethod
    def _generate_recommendations(attendance_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on attendance data."""
        recommendations = []
        percentage = attendance_data["attendance_percentage"]
        
        if percentage < 50:
            recommendations.append("Critical: Attendance below 50% - immediate intervention required")
            recommendations.append("Consider meeting with academic advisor")
        elif percentage < 75:
            recommendations.append("Warning: Attendance below 75% - improvement needed")
            recommendations.append("Review study schedule and commitments")
        elif percentage < 90:
            recommendations.append("Good: Attendance above 75% - minor improvement possible")
        else:
            recommendations.append("Excellent: Attendance above 90% - maintain current level")
        
        # Grade-specific recommendations
        grade = attendance_data["grade_contribution"]
        if grade < 2.5:
            recommendations.append(f"Grade impact: {grade}/5.0 points - significant grade penalty")
        elif grade < 4.0:
            recommendations.append(f"Grade impact: {grade}/5.0 points - moderate grade penalty")
        else:
            recommendations.append(f"Grade impact: {grade}/5.0 points - minimal grade penalty")
        
        return recommendations
    
    @staticmethod
    def get_module_performance_summary(module_id: int) -> Dict[str, Any]:
        """
        Generate a comprehensive performance summary for a module.
        
        Args:
            module_id: Module ID
            
        Returns:
            Module performance summary
        """
        # Get module attendance summary
        summary = AttendanceService.calculate_module_attendance_summary(module_id)
        
        if summary.get("error"):
            return {
                "success": False,
                "error": summary["error"],
                "summary": None
            }
        
        # Calculate additional metrics
        student_count = len(summary["student_attendance"])
        if student_count == 0:
            return {
                "success": False,
                "error": "No students found in module",
                "summary": None
            }
        
        # Performance categories
        excellent = len([s for s in summary["student_attendance"] if s["attendance_percentage"] >= 90])
        good = len([s for s in summary["student_attendance"] if 75 <= s["attendance_percentage"] < 90])
        fair = len([s for s in summary["student_attendance"] if 50 <= s["attendance_percentage"] < 75])
        poor = len([s for s in summary["student_attendance"] if s["attendance_percentage"] < 50])
        
        # Grade distribution
        grade_distribution = {
            "5.0": len([s for s in summary["student_attendance"] if s["grade_contribution"] == 5.0]),
            "4.0-4.9": len([s for s in summary["student_attendance"] if 4.0 <= s["grade_contribution"] < 5.0]),
            "3.0-3.9": len([s for s in summary["student_attendance"] if 3.0 <= s["grade_contribution"] < 4.0]),
            "2.0-2.9": len([s for s in summary["student_attendance"] if 2.0 <= s["grade_contribution"] < 3.0]),
            "1.0-1.9": len([s for s in summary["student_attendance"] if 1.0 <= s["grade_contribution"] < 2.0]),
            "0.0-0.9": len([s for s in summary["student_attendance"] if s["grade_contribution"] < 1.0])
        }
        
        performance_summary = {
            "module_info": summary["module_info"],
            "overview": {
                "total_sessions": summary["total_sessions"],
                "total_students": student_count,
                "module_average": summary["module_average"]
            },
            "attendance_categories": {
                "excellent_90_plus": excellent,
                "good_75_89": good,
                "fair_50_74": fair,
                "poor_below_50": poor
            },
            "grade_distribution": grade_distribution,
            "top_performers": sorted(
                summary["student_attendance"], 
                key=lambda x: x["attendance_percentage"], 
                reverse=True
            )[:5],
            "needs_attention": sorted(
                [s for s in summary["student_attendance"] if s["attendance_percentage"] < 75],
                key=lambda x: x["attendance_percentage"]
            )[:5]
        }
        
        return {
            "success": True,
            "error": None,
            "summary": performance_summary
        }


def example_usage():
    """Demonstrate practical usage of the attendance calculation methods."""
    print("🎯 Day 11 - Attendance Calculation Integration Examples")
    print("=" * 60)
    
    # Example 1: Generate student grade report
    print("\n📊 Example 1: Student Grade Report")
    print("-" * 40)
    
    # Replace with actual IDs from your database
    student_id = 905001234
    module_id = 1
    
    calculator = AttendanceCalculator()
    grade_report = calculator.get_student_grade_report(student_id, module_id)
    
    if grade_report["success"]:
        report = grade_report["report"]
        print(f"✅ Grade Report for {report['student_info']['name']}")
        print(f"   Attendance: {report['attendance_summary']['attendance_percentage']}%")
        print(f"   Grade Points: {report['grade_contribution']['points']}/5.0")
        print(f"   Recommendations:")
        for rec in report['recommendations']:
            print(f"     • {rec}")
    else:
        print(f"❌ Error: {grade_report['error']}")
    
    # Example 2: Module performance summary
    print("\n📚 Example 2: Module Performance Summary")
    print("-" * 40)
    
    module_summary = calculator.get_module_performance_summary(module_id)
    
    if module_summary["success"]:
        summary = module_summary["summary"]
        print(f"✅ Module: {summary['module_info']['module_code']}")
        print(f"   Total Students: {summary['overview']['total_students']}")
        print(f"   Module Average: {summary['overview']['module_average']}%")
        print(f"   Attendance Categories:")
        print(f"     • Excellent (90%+): {summary['attendance_categories']['excellent_90_plus']}")
        print(f"     • Good (75-89%): {summary['attendance_categories']['good_75_89']}")
        print(f"     • Fair (50-74%): {summary['attendance_categories']['fair_50_74']}")
        print(f"     • Poor (<50%): {summary['attendance_categories']['poor_below_50']}")
    else:
        print(f"❌ Error: {module_summary['error']}")
    
    print("\n" + "=" * 60)
    print("🎉 Integration Examples Complete!")
    print("\nThese examples show how to:")
    print("• Generate comprehensive student reports")
    print("• Create module performance summaries")
    print("• Integrate attendance calculations into your application")
    print("• Handle errors gracefully")


if __name__ == "__main__":
    example_usage()
