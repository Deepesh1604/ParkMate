#!/usr/bin/env python3
"""
Email Service Fix Script for ParkMate
This script will help you configure and start the email service
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime

def check_redis():
    """Check if Redis is running"""
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0 and 'PONG' in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def start_redis():
    """Start Redis server"""
    try:
        print("🔄 Starting Redis server...")
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import time
        time.sleep(3)  # Wait for Redis to start
        if check_redis():
            print("✅ Redis server started successfully")
            return True
        else:
            print("❌ Failed to start Redis server")
            return False
    except FileNotFoundError:
        print("❌ Redis not found. Please install Redis: sudo apt install redis-server")
        return False

def setup_environment_variables():
    """Setup email environment variables"""
    print("\n📧 Email Configuration Setup")
    print("=" * 50)
    
    email_username = input("Enter your Gmail address: ").strip()
    if not email_username or '@gmail.com' not in email_username:
        print("❌ Please enter a valid Gmail address")
        return False
    
    print("\n📝 To get Gmail App Password:")
    print("1. Go to Google Account settings")
    print("2. Security → 2-Step Verification → App passwords")
    print("3. Generate an app password for 'Mail'")
    print("4. Use that 16-character password below")
    
    email_password = input("Enter your Gmail App Password (16 characters): ").strip()
    if not email_password or len(email_password) != 16:
        print("❌ Please enter a valid 16-character app password")
        return False
    
    # Create or update .env file
    env_content = f"""# Email Configuration for ParkMate
EMAIL_USERNAME={email_username}
EMAIL_PASSWORD={email_password}

# Optional: Google Chat Webhook URL
# GOOGLE_CHAT_WEBHOOK=your_webhook_url_here
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Set environment variables for current session
    os.environ['EMAIL_USERNAME'] = email_username
    os.environ['EMAIL_PASSWORD'] = email_password
    
    print("✅ Email configuration saved to .env file")
    return True

def test_email_configuration():
    """Test email sending"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        email_username = os.environ.get('EMAIL_USERNAME')
        email_password = os.environ.get('EMAIL_PASSWORD')
        
        if not email_username or not email_password:
            print("❌ Email credentials not found in environment")
            return False
        
        print(f"📧 Testing email configuration for {email_username}...")
        
        msg = MIMEMultipart()
        msg['From'] = email_username
        msg['To'] = email_username
        msg['Subject'] = "ParkMate Email Test"
        
        body = """
        <html>
        <body>
            <h2>🎉 Email Configuration Test Successful!</h2>
            <p>Your ParkMate email service is working correctly.</p>
            <p><strong>Timestamp:</strong> {}</p>
        </body>
        </html>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_username, email_password)
        server.sendmail(email_username, email_username, msg.as_string())
        server.quit()
        
        print("✅ Test email sent successfully!")
        print(f"📬 Check {email_username} for the test email")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return False

def create_celery_start_script():
    """Create script to start Celery worker"""
    script_content = """#!/bin/bash
# Celery Worker Start Script for ParkMate

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo "🚀 Starting Celery worker for ParkMate..."
echo "📧 Email Username: $EMAIL_USERNAME"

# Start Celery worker
celery -A main.celery worker --loglevel=info --pool=solo
"""
    
    with open('start_celery.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('start_celery.sh', 0o755)
    print("✅ Celery start script created: start_celery.sh")

def create_celery_beat_script():
    """Create script to start Celery beat scheduler"""
    script_content = """#!/bin/bash
# Celery Beat Start Script for ParkMate

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo "⏰ Starting Celery beat scheduler for ParkMate..."

# Start Celery beat
celery -A main.celery beat --loglevel=info
"""
    
    with open('start_celery_beat.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('start_celery_beat.sh', 0o755)
    print("✅ Celery beat start script created: start_celery_beat.sh")

def update_main_py_for_env_loading():
    """Update main.py to load environment variables from .env file"""
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Check if python-dotenv is already imported
        if 'from dotenv import load_dotenv' not in content:
            # Add dotenv import and load after existing imports
            import_section = content.find('from flask import')
            if import_section != -1:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('from flask import'):
                        lines.insert(i, 'from dotenv import load_dotenv')
                        lines.insert(i+1, 'load_dotenv()  # Load environment variables from .env file')
                        break
                
                updated_content = '\n'.join(lines)
                
                with open('main.py', 'w') as f:
                    f.write(updated_content)
                
                print("✅ Updated main.py to load .env file")
                return True
        else:
            print("✅ main.py already configured for .env loading")
            return True
            
    except Exception as e:
        print(f"❌ Failed to update main.py: {e}")
        return False

def install_required_packages():
    """Install required Python packages"""
    required_packages = ['python-dotenv', 'celery', 'redis']
    
    for package in required_packages:
        try:
            print(f"📦 Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         check=True, capture_output=True)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def test_database_connection():
    """Test database connection and email tables"""
    try:
        conn = sqlite3.connect('parking_lot.db')
        cursor = conn.cursor()
        
        # Check if email_notifications table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='email_notifications'
        """)
        
        if cursor.fetchone():
            print("✅ Database connection successful")
            print("✅ Email notifications table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(email_notifications)")
            columns = cursor.fetchall()
            print(f"📊 Email notifications table has {len(columns)} columns")
            
            conn.close()
            return True
        else:
            print("❌ Email notifications table not found")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚗 ParkMate Email Service Fix")
    print("=" * 40)
    
    # Step 1: Install required packages
    print("\n1️⃣ Installing required packages...")
    if not install_required_packages():
        print("❌ Package installation failed. Please run: pip install python-dotenv celery redis")
        return False
    
    # Step 2: Setup environment variables
    print("\n2️⃣ Setting up email configuration...")
    if not setup_environment_variables():
        return False
    
    # Step 3: Update main.py for .env loading
    print("\n3️⃣ Updating main.py configuration...")
    update_main_py_for_env_loading()
    
    # Step 4: Test database
    print("\n4️⃣ Testing database connection...")
    if not test_database_connection():
        print("❌ Database setup incomplete. Please run the main application first.")
        return False
    
    # Step 5: Start Redis
    print("\n5️⃣ Setting up Redis server...")
    if not check_redis():
        if not start_redis():
            print("❌ Please start Redis manually: redis-server")
            return False
    else:
        print("✅ Redis server is already running")
    
    # Step 6: Test email configuration
    print("\n6️⃣ Testing email configuration...")
    if not test_email_configuration():
        print("❌ Email configuration test failed. Please check your credentials.")
        return False
    
    # Step 7: Create start scripts
    print("\n7️⃣ Creating service start scripts...")
    create_celery_start_script()
    create_celery_beat_script()
    
    print("\n🎉 Email service setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start the main Flask application: python main.py")
    print("2. In another terminal, start Celery worker: ./start_celery.sh")
    print("3. In another terminal, start Celery beat: ./start_celery_beat.sh")
    print("4. Try registering a new user to test welcome emails")
    
    print("\n📧 Email configuration saved in .env file")
    print("🔧 Service scripts created: start_celery.sh, start_celery_beat.sh")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
