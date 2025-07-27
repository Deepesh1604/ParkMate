#!/usr/bin/env python3
"""
ParkMate Email Service Setup Script
This script helps set up and configure the email service for the ParkMate application.
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime
import json

def print_header():
    print("=" * 70)
    print("🚗 ParkMate Email Service Setup")
    print("=" * 70)
    print()

def check_dependencies():
    """Check if required packages are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'flask',
        'celery',
        'redis',
        'requests',
        'smtplib',  # Built-in
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'smtplib':
                import smtplib
            else:
                __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them using: pip install " + ' '.join(missing_packages))
        return False
    
    print("✅ All dependencies are installed!")
    return True

def setup_environment_variables():
    """Guide user through setting up environment variables"""
    print("\n📧 Email Configuration Setup")
    print("-" * 40)
    
    env_vars = {}
    
    # Email configuration
    print("\n1. Gmail SMTP Configuration:")
    print("   - Use your Gmail address and app password")
    print("   - Enable 2FA and create an app password: https://support.google.com/accounts/answer/185833")
    
    email_user = input("   Enter your Gmail address: ").strip()
    if email_user:
        env_vars['EMAIL_USERNAME'] = email_user
    
    email_pass = input("   Enter your Gmail app password: ").strip()
    if email_pass:
        env_vars['EMAIL_PASSWORD'] = email_pass
    
    # Google Chat webhook (optional)
    print("\n2. Google Chat Webhook (Optional):")
    print("   - Create a webhook in your Google Chat space")
    print("   - Leave empty to skip Google Chat notifications")
    
    gchat_webhook = input("   Enter Google Chat webhook URL (optional): ").strip()
    if gchat_webhook:
        env_vars['GOOGLE_CHAT_WEBHOOK'] = gchat_webhook
    
    # Create .env file
    if env_vars:
        print("\n📝 Creating .env file...")
        with open('.env', 'w') as f:
            f.write("# ParkMate Email Service Configuration\n")
            f.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print("✅ Environment variables saved to .env file")
        
        # Also create a shell script for easy sourcing
        with open('set_env_vars.sh', 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# ParkMate Email Service Environment Variables\n")
            f.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for key, value in env_vars.items():
                f.write(f"export {key}='{value}'\n")
        
        os.chmod('set_env_vars.sh', 0o755)
        print("✅ Shell script created: set_env_vars.sh")
        
        return True
    else:
        print("⚠️  No environment variables configured")
        return False

def check_redis_connection():
    """Check if Redis is running"""
    print("\n🔴 Checking Redis connection...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running and accessible!")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n💡 To install and start Redis:")
        print("   Ubuntu/Debian: sudo apt-get install redis-server")
        print("   macOS: brew install redis && brew services start redis")
        print("   Windows: Download from https://redis.io/download")
        return False

def initialize_database():
    """Initialize the database with email-related tables"""
    print("\n🗄️  Initializing database...")
    
    try:
        conn = sqlite3.connect('parking_lot.db')
        cursor = conn.cursor()
        
        # Check if email_notifications table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='email_notifications'
        """)
        
        if cursor.fetchone():
            print("✅ Email tables already exist")
        else:
            print("📊 Creating email notification tables...")
            
            # Create tables (this should match what's in main.py)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    email_address TEXT NOT NULL,
                    email_type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'sent',
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT UNIQUE NOT NULL,
                    template_type TEXT NOT NULL,
                    subject_template TEXT NOT NULL,
                    body_template TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("✅ Email tables created successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_test_data():
    """Create some test data for demonstration"""
    print("\n🧪 Setting up test data...")
    
    try:
        conn = sqlite3.connect('parking_lot.db')
        cursor = conn.cursor()
        
        # Insert sample notification templates
        templates = [
            ('welcome', 'email', '🎉 Welcome to ParkMate!', 'Welcome template'),
            ('daily_reminder', 'email', '🔔 Daily Parking Reminder', 'Reminder template'),
            ('monthly_report', 'email', '📊 Monthly Report', 'Monthly report template'),
            ('csv_export', 'email', '📄 Data Export Ready', 'Export template')
        ]
        
        for template in templates:
            cursor.execute('''
                INSERT OR IGNORE INTO notification_templates 
                (template_name, template_type, subject_template, body_template)
                VALUES (?, ?, ?, ?)
            ''', template)
        
        conn.commit()
        conn.close()
        
        print("✅ Test data created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test data creation failed: {e}")
        return False

def create_celery_scripts():
    """Create Celery startup scripts"""
    print("\n⚙️  Creating Celery startup scripts...")
    
    # Celery worker script
    worker_script = '''#!/bin/bash
# ParkMate Celery Worker Startup Script

echo "🔄 Starting ParkMate Celery Worker..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Celery worker
celery -A main.celery worker --loglevel=info --concurrency=4
'''
    
    with open('start_celery_worker.sh', 'w') as f:
        f.write(worker_script)
    os.chmod('start_celery_worker.sh', 0o755)
    
    # Celery beat script
    beat_script = '''#!/bin/bash
# ParkMate Celery Beat (Scheduler) Startup Script

echo "⏰ Starting ParkMate Celery Beat Scheduler..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Celery beat
celery -A main.celery beat --loglevel=info --scheduler=celery.beat:PersistentScheduler
'''
    
    with open('start_celery_beat.sh', 'w') as f:
        f.write(beat_script)
    os.chmod('start_celery_beat.sh', 0o755)
    
    # Combined script
    combined_script = '''#!/bin/bash
# ParkMate Complete Email Service Startup Script

echo "🚀 Starting ParkMate Email Service Components..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  No .env file found. Please run setup_email_service.py first"
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first."
    exit 1
fi

echo "✅ Redis is running"

# Start Celery worker in background
echo "🔄 Starting Celery worker..."
celery -A main.celery worker --loglevel=info --concurrency=4 --detach --pidfile=celery_worker.pid --logfile=celery_worker.log

# Start Celery beat in background
echo "⏰ Starting Celery beat scheduler..."
celery -A main.celery beat --loglevel=info --detach --pidfile=celery_beat.pid --logfile=celery_beat.log

echo "✅ All email service components started!"
echo ""
echo "📊 Service Status:"
echo "   - Celery Worker: Started (PID file: celery_worker.pid)"
echo "   - Celery Beat: Started (PID file: celery_beat.pid)"
echo "   - Logs: celery_worker.log, celery_beat.log"
echo ""
echo "🛑 To stop services: ./stop_email_service.sh"
'''
    
    with open('start_email_service.sh', 'w') as f:
        f.write(combined_script)
    os.chmod('start_email_service.sh', 0o755)
    
    # Stop script
    stop_script = '''#!/bin/bash
# ParkMate Email Service Stop Script

echo "🛑 Stopping ParkMate Email Service Components..."

# Stop Celery worker
if [ -f celery_worker.pid ]; then
    PID=$(cat celery_worker.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Celery worker stopped"
    fi
    rm -f celery_worker.pid
fi

# Stop Celery beat
if [ -f celery_beat.pid ]; then
    PID=$(cat celery_beat.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Celery beat stopped"
    fi
    rm -f celery_beat.pid
fi

# Clean up any remaining Celery processes
pkill -f "celery.*main.celery" 2>/dev/null

echo "✅ All email service components stopped!"
'''
    
    with open('stop_email_service.sh', 'w') as f:
        f.write(stop_script)
    os.chmod('stop_email_service.sh', 0o755)
    
    print("✅ Celery scripts created:")
    print("   - start_celery_worker.sh")
    print("   - start_celery_beat.sh") 
    print("   - start_email_service.sh (combined)")
    print("   - stop_email_service.sh")

def create_documentation():
    """Create documentation file"""
    print("\n📚 Creating documentation...")
    
    doc_content = """# ParkMate Email Service Documentation

## Overview
The ParkMate email service provides comprehensive email functionality including:
- Welcome emails for new users
- Daily parking reminders
- Monthly activity reports
- CSV export notifications
- Admin email management

## Features

### 1. Scheduled Jobs

#### Daily Reminders
- **Frequency**: Daily at 6 PM (configurable per user)
- **Recipients**: Users who haven't booked parking today
- **Content**: Personalized reminders with available parking lots
- **Delivery Methods**: Email, Google Chat webhook

#### Monthly Activity Reports  
- **Frequency**: 1st of every month at 9 AM
- **Recipients**: All active users
- **Content**: Comprehensive HTML reports with:
  - Booking statistics and trends
  - Most used parking lots
  - Spending analysis
  - Personalized recommendations
  - Visual charts and graphs

### 2. User Triggered Jobs

#### CSV Export
- **Trigger**: User dashboard export button
- **Process**: Asynchronous background job
- **Content**: Complete parking history in CSV format
- **Notification**: Email with attachment when ready

#### Welcome Email
- **Trigger**: New user registration
- **Process**: Automatic background job
- **Content**: Welcome message with feature overview

### 3. Admin Features

#### Email Management Dashboard
- View all email notifications
- Filter by type, status, date
- Email statistics and analytics
- Test email configuration

#### Notification Templates
- Customizable email templates
- Template versioning
- A/B testing capabilities

## API Endpoints

### User Endpoints
- `GET/POST /api/user/preferences` - Manage notification preferences
- `POST /api/user/export-csv` - Request CSV export
- `GET /api/user/export-status/<id>` - Check export status
- `GET /api/user/emails/history` - Get email history

### Admin Endpoints
- `GET /api/admin/emails/notifications` - Get email notifications
- `GET /api/admin/emails/stats` - Get email statistics
- `POST /api/admin/emails/test` - Test email configuration
- `POST /api/admin/trigger-daily-reminders` - Manual reminder trigger
- `POST /api/admin/trigger-monthly-report` - Manual report trigger

## Setup Instructions

### 1. Environment Variables
```bash
export EMAIL_USERNAME=your-gmail@gmail.com
export EMAIL_PASSWORD=your-app-password
export GOOGLE_CHAT_WEBHOOK=https://chat.googleapis.com/v1/spaces/.../messages?key=...
```

### 2. Start Services
```bash
# Start Redis
redis-server

# Start Celery worker
./start_celery_worker.sh

# Start Celery beat scheduler  
./start_celery_beat.sh

# Or start both with one command
./start_email_service.sh
```

### 3. Test Configuration
```bash
# Test email sending
curl -X POST http://localhost:5001/api/admin/emails/test \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## Email Templates

### Welcome Email
- Modern responsive design
- Feature overview with icons
- Getting started guide
- Call-to-action buttons

### Daily Reminders
- Personalized content
- Available parking lots
- Quick booking links
- Preference management

### Monthly Reports
- Comprehensive statistics
- Visual data presentation
- Trend analysis
- Personalized recommendations

### CSV Export Notifications
- Export summary
- Data description
- Usage tips
- Security notes

## Monitoring and Logging

### Email Logging
All email activities are logged to the database:
- Recipient information
- Email type and subject
- Delivery status
- Error messages
- Timestamps

### Admin Dashboard
- Real-time email statistics
- Delivery success rates
- Failed email analysis
- User engagement metrics

## Troubleshooting

### Common Issues

1. **Emails not sending**
   - Check Gmail app password
   - Verify SMTP settings
   - Check firewall/network restrictions

2. **Celery tasks not running**
   - Ensure Redis is running
   - Check Celery worker status
   - Verify task registration

3. **Database errors**
   - Check database permissions
   - Verify table schema
   - Run database migrations

### Log Files
- `celery_worker.log` - Worker process logs
- `celery_beat.log` - Scheduler logs
- Application logs in terminal output

## Security Considerations

1. **Email Credentials**
   - Use app passwords, not account passwords
   - Store credentials in environment variables
   - Rotate passwords regularly

2. **Data Privacy**
   - Email content follows privacy policies
   - User consent for notifications
   - Secure data transmission

3. **Rate Limiting**
   - Implement email sending limits
   - Monitor for abuse
   - Graceful error handling

## Performance Optimization

1. **Email Queuing**
   - Asynchronous processing
   - Batch email sending
   - Retry mechanisms

2. **Template Caching**
   - Cache compiled templates
   - Optimize template rendering
   - Minimize database queries

3. **Resource Management**
   - Connection pooling
   - Memory optimization
   - Error recovery

## Future Enhancements

1. **Advanced Features**
   - Email personalization
   - A/B testing
   - Unsubscribe management
   - Email analytics

2. **Integration**
   - SMS notifications
   - Push notifications
   - Third-party email services

3. **Performance**
   - Advanced queuing
   - Load balancing
   - Scalability improvements
"""
    
    with open('EMAIL_SERVICE_DOCS.md', 'w') as f:
        f.write(doc_content)
    
    print("✅ Documentation created: EMAIL_SERVICE_DOCS.md")

def main():
    """Main setup function"""
    print_header()
    
    success_steps = []
    
    # Step 1: Check dependencies
    if check_dependencies():
        success_steps.append("Dependencies")
    
    # Step 2: Setup environment variables
    if setup_environment_variables():
        success_steps.append("Environment Variables")
    
    # Step 3: Check Redis
    if check_redis_connection():
        success_steps.append("Redis Connection")
    
    # Step 4: Initialize database
    if initialize_database():
        success_steps.append("Database Setup")
    
    # Step 5: Create test data
    if create_test_data():
        success_steps.append("Test Data")
    
    # Step 6: Create scripts
    create_celery_scripts()
    success_steps.append("Startup Scripts")
    
    # Step 7: Create documentation
    create_documentation()
    success_steps.append("Documentation")
    
    # Summary
    print("\n" + "=" * 70)
    print("🎉 ParkMate Email Service Setup Complete!")
    print("=" * 70)
    
    print(f"\n✅ Completed steps: {', '.join(success_steps)}")
    
    print("\n📋 Next Steps:")
    print("1. Source environment variables: source set_env_vars.sh")
    print("2. Start Redis: redis-server") 
    print("3. Start email services: ./start_email_service.sh")
    print("4. Test the setup: python -c \"from main import app; print('✅ Import successful')\"")
    print("5. Start your Flask app: python main.py")
    
    print("\n📚 Documentation: EMAIL_SERVICE_DOCS.md")
    print("🔧 Scripts created: start_email_service.sh, stop_email_service.sh")
    
    print("\n🚀 Your ParkMate email service is ready!")

if __name__ == "__main__":
    main()
