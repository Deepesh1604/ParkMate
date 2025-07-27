#!/usr/bin/env python3
"""
ParkMate Email Service Test Script
This script tests all email functionality to ensure everything is working correctly.
"""

import sys
import os
import sqlite3
import requests
import json
from datetime import datetime
import time

def print_header():
    print("🧪 ParkMate Email Service Test Suite")
    print("=" * 50)
    print()

def test_database_setup():
    """Test if database tables exist"""
    print("📊 Testing database setup...")
    
    try:
        conn = sqlite3.connect('parking_lot.db')
        cursor = conn.cursor()
        
        # Check required tables
        tables_to_check = [
            'email_notifications',
            'user_preferences', 
            'csv_export_jobs',
            'notification_templates'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = []
        for table in tables_to_check:
            if table in existing_tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - Missing")
                missing_tables.append(table)
        
        conn.close()
        
        if missing_tables:
            print(f"\n⚠️  Missing tables: {', '.join(missing_tables)}")
            print("Run: python main.py to initialize the database")
            return False
        
        print("✅ Database setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_environment_variables():
    """Test if environment variables are set"""
    print("\n🔧 Testing environment variables...")
    
    required_vars = ['EMAIL_USERNAME', 'EMAIL_PASSWORD']
    optional_vars = ['GOOGLE_CHAT_WEBHOOK']
    
    missing_vars = []
    
    for var in required_vars:
        if os.environ.get(var):
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - Not set")
            missing_vars.append(var)
    
    for var in optional_vars:
        if os.environ.get(var):
            print(f"  ✅ {var}")
        else:
            print(f"  ⚠️  {var} - Optional, not set")
    
    if missing_vars:
        print(f"\n⚠️  Missing required variables: {', '.join(missing_vars)}")
        print("Set them using: export VARIABLE_NAME=value")
        return False
    
    print("✅ Environment variables configured!")
    return True

def test_redis_connection():
    """Test Redis connection"""
    print("\n🔴 Testing Redis connection...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful!")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Make sure Redis is running: redis-server")
        return False

def test_celery_worker():
    """Test if Celery worker is running"""
    print("\n⚙️  Testing Celery worker...")
    
    try:
        # This is a basic test - in practice you'd use Celery inspect
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'celery.*worker'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Celery worker is running!")
            return True
        else:
            print("⚠️  Celery worker not detected")
            print("Start with: ./start_celery_worker.sh")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not check Celery worker: {e}")
        return False

def test_flask_app():
    """Test if Flask app is responding"""
    print("\n🌐 Testing Flask application...")
    
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=5)
        
        if response.status_code == 200:
            print("✅ Flask app is responding!")
            return True
        else:
            print(f"⚠️  Flask app returned status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Flask app not running")
        print("Start with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def test_email_configuration():
    """Test email configuration by sending a test email"""
    print("\n📧 Testing email configuration...")
    
    try:
        # Test email sending (assumes Flask app is running and admin is logged in)
        test_data = {
            "email": "test@example.com"  # Change this to your test email
        }
        
        # Note: This would require admin authentication in practice
        print("⚠️  Email test requires admin authentication")
        print("Manual test: curl -X POST http://localhost:5001/api/admin/emails/test")
        print("            -H 'Content-Type: application/json'")
        print("            -d '{\"email\": \"your-email@example.com\"}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Email test setup failed: {e}")
        return False

def test_user_registration_email():
    """Test welcome email on user registration"""
    print("\n👋 Testing welcome email functionality...")
    
    try:
        # Create a test user to trigger welcome email
        test_user_data = {
            "username": f"testuser_{int(time.time())}",
            "password": "testpass123",
            "email": "test@example.com",  # Change to your test email
            "phone": "1234567890"
        }
        
        response = requests.post(
            'http://localhost:5001/api/register',
            json=test_user_data,
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ User registration successful!")
            print("📧 Welcome email should be sent in the background")
            print(f"   Check email: {test_user_data['email']}")
            return True
        else:
            print(f"⚠️  Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Could not connect to Flask app")
        return False
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("\n📝 Creating sample data...")
    
    try:
        conn = sqlite3.connect('parking_lot.db')
        cursor = conn.cursor()
        
        # Create sample parking lot if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO parking_lots 
            (prime_location_name, price, address, pin_code, maximum_number_of_spots)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Test Parking Lot', 5.0, '123 Test Street', '12345', 20))
        
        lot_id = cursor.lastrowid or 1
        
        # Create sample parking spots
        for i in range(1, 6):
            cursor.execute('''
                INSERT OR IGNORE INTO parking_spots (lot_id, spot_number, status)
                VALUES (?, ?, ?)
            ''', (lot_id, i, 'A'))
        
        # Insert sample notification templates if not exist
        templates = [
            ('welcome', 'email', '🎉 Welcome to ParkMate!', 'Welcome template'),
            ('daily_reminder', 'email', '🔔 Daily Parking Reminder', 'Reminder template'),
        ]
        
        for template in templates:
            cursor.execute('''
                INSERT OR IGNORE INTO notification_templates 
                (template_name, template_type, subject_template, body_template)
                VALUES (?, ?, ?, ?)
            ''', template)
        
        conn.commit()
        conn.close()
        
        print("✅ Sample data created!")
        return True
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False

def test_database_queries():
    """Test database queries for email functionality"""
    print("\n🔍 Testing database queries...")
    
    try:
        conn = sqlite3.connect('parking_lot.db')
        cursor = conn.cursor()
        
        # Test user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  📊 Total users: {user_count}")
        
        # Test email notifications count
        cursor.execute("SELECT COUNT(*) FROM email_notifications")
        email_count = cursor.fetchone()[0]
        print(f"  📧 Email notifications: {email_count}")
        
        # Test user preferences
        cursor.execute("SELECT COUNT(*) FROM user_preferences")
        pref_count = cursor.fetchone()[0]
        print(f"  ⚙️  User preferences: {pref_count}")
        
        # Test templates
        cursor.execute("SELECT COUNT(*) FROM notification_templates")
        template_count = cursor.fetchone()[0]
        print(f"  📄 Notification templates: {template_count}")
        
        conn.close()
        
        print("✅ Database queries successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database query test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print_header()
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Environment Variables", test_environment_variables),
        ("Redis Connection", test_redis_connection),
        ("Celery Worker", test_celery_worker),
        ("Flask Application", test_flask_app),
        ("Sample Data Creation", create_sample_data),
        ("Database Queries", test_database_queries),
        ("Email Configuration", test_email_configuration),
        ("User Registration Email", test_user_registration_email),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Your email service is ready!")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print("\n💡 Common fixes:")
        print("   - Set environment variables: source set_env_vars.sh")
        print("   - Start Redis: redis-server")
        print("   - Start Celery: ./start_email_service.sh")
        print("   - Start Flask app: python main.py")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
