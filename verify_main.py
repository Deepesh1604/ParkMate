#!/usr/bin/env python3
"""
Quick test to verify Flask app starts without errors
"""

import sys
import os
sys.path.append(os.getcwd())

try:
    print("🔍 Testing Flask app import...")
    import main
    print("✅ Flask app imported successfully")
    
    print("🔍 Testing Celery app...")
    celery_app = main.celery
    print(f"✅ Celery app: {celery_app}")
    
    print("🔍 Testing database connection...")
    conn = main.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    print(f"✅ Database connection: {user_count} users")
    
    print("🔍 Testing Redis connection...")
    redis_client = main.redis_client
    ping_result = redis_client.ping()
    print(f"✅ Redis connection: {ping_result}")
    
    print("\n🎉 All components are working correctly!")
    print("\n💡 To start the full application:")
    print("   1. Start Celery: celery -A main.celery worker --loglevel=info")
    print("   2. Start Flask: python3 main.py")
    print("   3. Access frontend at: http://localhost:5000")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
