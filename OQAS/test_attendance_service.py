#!/usr/bin/env python3
"""
Test script for AttendanceService.submit_attendance()
This script demonstrates the new attendance submission functionality.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if your app runs on a different port

def test_api_submit_attendance():
    """Test the API endpoint for submitting attendance"""
    print("🧪 Testing API Attendance Submission")
    print("=" * 50)
    
    # Test data
    test_cases = [
        {
            "name": "Valid attendance submission",
            "data": {
                "session_id": 1,
                "student_id": 905001234,
                "student_name": "John Doe"
            },
            "expected_status": 200
        },
        {
            "name": "Duplicate attendance (should fail)",
            "data": {
                "session_id": 1,
                "student_id": 905001234,
                "student_name": "John Doe"
            },
            "expected_status": 400
        },
        {
            "name": "Invalid student ID format",
            "data": {
                "session_id": 1,
                "student_id": 12345,
                "student_name": "Jane Smith"
            },
            "expected_status": 400
        },
        {
            "name": "Missing required fields",
            "data": {
                "session_id": 1,
                "student_name": "Jane Smith"
            },
            "expected_status": 400
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print(f"   Data: {test_case['data']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/attendance/submit",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            if response.status_code == test_case['expected_status']:
                print("   ✅ PASS")
            else:
                print("   ❌ FAIL - Unexpected status code")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ FAIL - Could not connect to server. Make sure the Flask app is running.")
        except Exception as e:
            print(f"   ❌ FAIL - Error: {str(e)}")

def test_direct_service():
    """Test the AttendanceService directly (if running in same process)"""
    print("\n\n🔧 Testing Direct Service Call")
    print("=" * 50)
    
    try:
        from services.attendance_service import AttendanceService
        
        # Test the submit_attendance method directly
        print("Testing submit_attendance method...")
        
        # This would work if running in the same process as the Flask app
        # success, error = AttendanceService.submit_attendance(
        #     session_id=1,
        #     student_id=905001234,
        #     student_name="Test Student"
        # )
        # print(f"Direct call result: success={success}, error={error}")
        
        print("Note: Direct service testing requires running in the same process as the Flask app.")
        
    except ImportError:
        print("Could not import AttendanceService directly. This is expected when running as a separate script.")

def main():
    """Main test function"""
    print("🚀 Attendance Service Test Suite")
    print(f"Target URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test API endpoint
    test_api_submit_attendance()
    
    # Test direct service (if possible)
    test_direct_service()
    
    print("\n\n🏁 Test Suite Complete!")
    print("\nTo run these tests:")
    print("1. Make sure your Flask app is running")
    print("2. Adjust the BASE_URL if needed")
    print("3. Run: python test_attendance_service.py")

if __name__ == "__main__":
    main()
