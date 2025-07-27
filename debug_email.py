#!/usr/bin/env python3
"""
Email Debug Script - Test welcome email functionality
"""

import os
import sys
import sqlite3

# Set environment variables for testing
os.environ['EMAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with your Gmail
os.environ['EMAIL_PASSWORD'] = 'your-app-password'     # Replace with your app password

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

def test_direct_email():
    """Test sending email directly without Celery"""
    try:
        from main import send_email
        
        test_email = input("Enter email address to test: ").strip()
        if not test_email:
            test_email = "test@example.com"
        
        success = send_email(
            test_email,
            "🧪 ParkMate Email Test",
            """
            <html>
            <body>
                <h2>🎉 Email Test Successful!</h2>
                <p>Your ParkMate email configuration is working.</p>
                <p>Welcome emails should now work when users register.</p>
            </body>
            </html>
            """,
            email_type='test'
        )
        
        if success:
            print(f"✅ Email sent successfully to {test_email}")
            return True
        else:
            print(f"❌ Failed to send email to {test_email}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email: {e}")
        return False

def test_welcome_email_function():
    """Test the welcome email function directly"""
    try:
        from main import send_welcome_email
        
        # Test without Celery
        result = send_welcome_email(
            1,  # dummy user_id
            "TestUser",
            input("Enter test email: ").strip()
        )
        
        print(f"Welcome email function result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing welcome email function: {e}")
        return False

def check_database():
    """Check database for email logs"""
    try:
        conn = sqlite3.connect('parking_lot.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM email_notifications")
        count = cursor.fetchone()[0]
        
        print(f"📊 Total email notifications in database: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT email_type, status, COUNT(*) 
                FROM email_notifications 
                GROUP BY email_type, status
            """)
            
            results = cursor.fetchall()
            print("📈 Email statistics:")
            for email_type, status, count in results:
                print(f"  {email_type}: {status} = {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def main():
    print("🔧 ParkMate Email Debug Tool")
    print("=" * 30)
    
    print("\n1️⃣ Checking database...")
    check_database()
    
    print(f"\n2️⃣ Current environment:")
    print(f"EMAIL_USERNAME: {os.environ.get('EMAIL_USERNAME', 'NOT SET')}")
    print(f"EMAIL_PASSWORD: {'SET' if os.environ.get('EMAIL_PASSWORD') else 'NOT SET'}")
    
    print("\n3️⃣ Testing direct email...")
    if test_direct_email():
        print("✅ Direct email test passed")
    else:
        print("❌ Direct email test failed")
        print("\n🔧 To fix:")
        print("1. Set your Gmail credentials in this script")
        print("2. Use Gmail App Password, not regular password")
        print("3. Enable 2-Step Verification in Google Account")
    
    print("\n4️⃣ Testing welcome email function...")
    test_welcome_email_function()

if __name__ == "__main__":
    main()
