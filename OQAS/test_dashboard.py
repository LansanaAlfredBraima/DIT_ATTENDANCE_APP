#!/usr/bin/env python3
"""
Test script for the dashboard functionality
"""
import sqlite3
from config import DB_PATH
from services.module_service import ModuleService

def test_module_service():
    """Test the module service functionality"""
    print("Testing Module Service...")
    
    # Test getting modules for lecturer 1 (assuming they exist)
    try:
        modules = ModuleService.get_modules_by_lecturer(2)  # lect1 should have ID 2
        print(f"✅ Found {len(modules)} modules for lecturer 1:")
        for module in modules:
            print(f"   - {module['module_code']}: {module['module_name']}")
            
        # Test getting active session
        if modules:
            module_id = modules[0]['module_id']
            active_session = ModuleService.get_active_session(module_id)
            print(f"✅ Active session for module {module_id}: {active_session}")
            
    except Exception as e:
        print(f"❌ Error testing module service: {e}")

def test_database_connection():
    """Test database connection and table structure"""
    print("\nTesting Database Connection...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Found tables: {[table[0] for table in tables]}")
        
        # Check modules data
        cursor.execute("SELECT COUNT(*) FROM modules")
        module_count = cursor.fetchone()[0]
        print(f"✅ Total modules in database: {module_count}")
        
        # Check users data
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'lecturer'")
        lecturer_count = cursor.fetchone()[0]
        print(f"✅ Total lecturers in database: {lecturer_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    print("🧪 Testing OQAS Dashboard Functionality\n")
    
    test_database_connection()
    test_module_service()
    
    print("\n✅ Testing completed!")
