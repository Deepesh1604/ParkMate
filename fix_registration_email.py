#!/usr/bin/env python3
"""
Complete Email Service Fix for ParkMate Registration Issue
This script fixes the Redis connection errors and Celery task failures
"""

import os
import sys
import subprocess
import time

def check_redis_status():
    """Check if Redis is running"""
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0 and 'PONG' in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def start_redis_service():
    """Start Redis service"""
    try:
        print("🔄 Starting Redis server...")
        subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], check=True)
        time.sleep(2)
        
        if check_redis_status():
            print("✅ Redis server started successfully")
            return True
        else:
            print("❌ Redis server failed to start")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Redis service: {e}")
        return False

def create_env_file():
    """Create a basic .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("📧 Creating default .env file...")
        with open('.env', 'w') as f:
            f.write("""# Email Configuration for ParkMate
# IMPORTANT: Replace with your actual Gmail credentials

EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password

# Optional: Google Chat Webhook URL
# GOOGLE_CHAT_WEBHOOK=your_webhook_url_here

# Instructions:
# 1. Go to https://myaccount.google.com/security
# 2. Enable 2-Step Verification
# 3. Go to Security → App Passwords
# 4. Generate app password for "Mail"
# 5. Replace values above with your credentials
""")
        print("✅ Created .env file - PLEASE UPDATE WITH YOUR GMAIL CREDENTIALS")
        return False
    else:
        print("✅ Found existing .env file")
        return True

def test_application_startup():
    """Test if the main application can start without Redis errors"""
    print("🧪 Testing application startup...")
    
    # Set environment variables to avoid Redis connection on startup
    env = os.environ.copy()
    env['REDIS_SKIP_STARTUP_CHECK'] = '1'
    
    try:
        # Test import of main module
        test_code = """
import sys
sys.path.insert(0, '.')

try:
    print("Testing main.py import...")
    # Import main components without starting Flask
    from main import init_db, hash_password
    print("✅ Main module imported successfully")
    
    # Test database connection
    init_db()
    print("✅ Database initialized successfully")
    
    # Test password hashing
    test_hash = hash_password("test123")
    print("✅ Password hashing works")
    
    print("✅ Application core components working")
    
except Exception as e:
    print(f"❌ Application test failed: {e}")
    sys.exit(1)
"""
        
        result = subprocess.run([sys.executable, '-c', test_code], 
                              capture_output=True, text=True, env=env, timeout=30)
        
        if result.returncode == 0:
            print("✅ Application startup test passed")
            print(result.stdout)
            return True
        else:
            print("❌ Application startup test failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Application startup test timed out")
        return False
    except Exception as e:
        print(f"❌ Error during application test: {e}")
        return False

def main():
    """Main fix routine"""
    print("🔧 ParkMate Email Service Fix")
    print("=" * 40)
    
    # Step 1: Create .env file
    env_configured = create_env_file()
    
    # Step 2: Check and start Redis
    print("\n📊 Checking Redis status...")
    if not check_redis_status():
        if not start_redis_service():
            print("\n❌ Redis setup failed. Manual steps:")
            print("1. Install Redis: sudo apt install redis-server")
            print("2. Start Redis: sudo systemctl start redis-server")
            print("3. Test Redis: redis-cli ping")
            return False
    else:
        print("✅ Redis is already running")
    
    # Step 3: Test application
    print("\n🧪 Testing application components...")
    if not test_application_startup():
        print("\n❌ Application test failed")
        return False
    
    # Step 4: Final status and instructions
    print("\n🎉 Email Service Fix Complete!")
    print("\n📋 Next Steps:")
    
    if not env_configured:
        print("1. ⚠️  IMPORTANT: Update .env file with your Gmail credentials")
        print("   - Edit .env file")
        print("   - Replace 'your-email@gmail.com' with your Gmail address")
        print("   - Replace 'your-16-char-app-password' with your Gmail App Password")
        print("   - Get App Password from: https://myaccount.google.com/security")
    
    print("\n2. 🚀 Start the application:")
    print("   Terminal 1: python main.py")
    print("   Terminal 2: ./start_celery_worker.sh  (optional, for background tasks)")
    
    print("\n3. 🧪 Test user registration:")
    print("   - Register a new user through the frontend")
    print("   - Check for welcome email in inbox")
    
    print("\n📧 Email Features Available:")
    print("   ✅ Welcome emails (works without Celery now)")
    print("   ✅ Daily reminders (requires Celery worker)")
    print("   ✅ Monthly reports (requires Celery worker)")
    print("   ✅ CSV export notifications (requires Celery worker)")
    
    print("\n🔧 Troubleshooting:")
    print("   - Redis errors: sudo systemctl restart redis-server")
    print("   - Email errors: Check Gmail App Password in .env file")
    print("   - Celery errors: ./start_celery_worker.sh")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Fix completed successfully!")
        else:
            print("\n❌ Fix completed with errors - check the steps above")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Fix interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during fix: {e}")
        sys.exit(1)
