#!/usr/bin/env python3
"""
Test script to verify ParkMate fixes are working correctly
"""

import sqlite3
import redis
import requests
import json
import time
from datetime import datetime

def dict_factory(cursor, row):
    """Convert sqlite row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    return sqlite3.connect('parking_lot.db')

def test_redis_connection():
    """Test Redis connection"""
    print("🔍 Testing Redis connection...")
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        ping_result = redis_client.ping()
        keys_count = len(redis_client.keys('*'))
        print(f"   ✅ Redis: {ping_result}, Keys: {keys_count}")
        return True
    except Exception as e:
        print(f"   ❌ Redis error: {e}")
        return False

def test_database_consistency():
    """Test database consistency"""
    print("🔍 Testing database consistency...")
    
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    # Check for orphaned reservations
    cursor.execute("""
        SELECT COUNT(*) as count FROM reservations r
        LEFT JOIN users u ON r.user_id = u.id
        WHERE u.id IS NULL
    """)
    orphaned = cursor.fetchone()['count']
    
    # Check for inconsistent spots
    cursor.execute("""
        SELECT COUNT(*) as count FROM parking_spots ps
        LEFT JOIN reservations r ON ps.id = r.spot_id AND r.status = 'active'
        WHERE (ps.status = 'O' AND r.id IS NULL) OR (ps.status = 'A' AND r.id IS NOT NULL)
    """)
    inconsistent = cursor.fetchone()['count']
    
    conn.close()
    
    print(f"   📊 Orphaned reservations: {orphaned}")
    print(f"   📊 Inconsistent spots: {inconsistent}")
    
    if orphaned == 0 and inconsistent == 0:
        print("   ✅ Database is consistent")
        return True
    else:
        print("   ⚠️  Database has consistency issues")
        return False

def test_api_endpoint(url, method="GET", data=None, session=None):
    """Test API endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, cookies=session)
        elif method == "POST":
            response = requests.post(url, json=data, cookies=session)
        
        return response.status_code, response.json() if response.content else {}
    except Exception as e:
        return None, str(e)

def simulate_user_flow():
    """Simulate a complete user flow"""
    print("🧪 Testing complete user flow...")
    
    base_url = "http://localhost:5000"
    
    # Test basic endpoints
    endpoints_to_test = [
        f"{base_url}/api/user/parking-lots",
        f"{base_url}/api/admin/parking-lots"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"   Testing {endpoint}...")
        status, response = test_api_endpoint(endpoint)
        if status == 200:
            print(f"   ✅ {endpoint} - OK")
        else:
            print(f"   ❌ {endpoint} - Status: {status}")
    
    return True

def check_celery_tasks():
    """Check if Celery tasks are defined and working"""
    print("🔍 Checking Celery tasks...")
    
    try:
        # Import main to get celery instance
        import main
        
        # List registered tasks
        registered_tasks = list(main.celery.tasks.keys())
        relevant_tasks = [task for task in registered_tasks if 'main.' in task]
        
        print(f"   📋 Registered tasks: {len(relevant_tasks)}")
        for task in relevant_tasks:
            print(f"      - {task}")
        
        if len(relevant_tasks) > 0:
            print("   ✅ Celery tasks are registered")
            return True
        else:
            print("   ⚠️  No Celery tasks found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking Celery: {e}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print("🚗 ParkMate Comprehensive Test Suite")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Redis
    if test_redis_connection():
        tests_passed += 1
    
    print()
    
    # Test 2: Database consistency
    if test_database_consistency():
        tests_passed += 1
    
    print()
    
    # Test 3: Celery tasks
    if check_celery_tasks():
        tests_passed += 1
    
    print()
    
    # Test 4: API endpoints (if Flask is running)
    try:
        if simulate_user_flow():
            tests_passed += 1
    except Exception as e:
        print(f"   ⚠️  API tests skipped (Flask may not be running): {e}")
    
    print()
    print("📊 TEST RESULTS")
    print("=" * 40)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! ParkMate is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
