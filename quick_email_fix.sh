#!/bin/bash
# Quick Email Service Fix for ParkMate

echo "🚗 ParkMate Email Service Quick Fix"
echo "=================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📧 Setting up email configuration..."
    echo ""
    read -p "Enter your Gmail address: " EMAIL_USERNAME
    read -s -p "Enter your Gmail App Password (16 chars): " EMAIL_PASSWORD
    echo ""
    
    # Create .env file
    cat > .env << EOF
# Email Configuration for ParkMate
EMAIL_USERNAME=$EMAIL_USERNAME
EMAIL_PASSWORD=$EMAIL_PASSWORD

# Optional: Google Chat Webhook URL
# GOOGLE_CHAT_WEBHOOK=your_webhook_url_here
EOF
    
    echo "✅ Email configuration saved to .env file"
else
    echo "✅ Found existing .env file"
fi

# Load environment variables
export $(cat .env | grep -v '#' | awk '/=/ {print $1}')

# Install required packages
echo "📦 Installing required packages..."
pip install python-dotenv celery redis

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "🔄 Starting Redis server..."
    redis-server --daemonize yes
    sleep 2
fi

if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis server is running"
else
    echo "❌ Redis server failed to start. Please install Redis:"
    echo "   Ubuntu/Debian: sudo apt install redis-server"
    echo "   macOS: brew install redis"
    exit 1
fi

# Create Celery worker start script
cat > start_celery_worker.sh << 'EOF'
#!/bin/bash
# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo "🚀 Starting Celery worker..."
echo "📧 Email Username: $EMAIL_USERNAME"
celery -A main.celery worker --loglevel=info --pool=solo
EOF

chmod +x start_celery_worker.sh

# Test email configuration
echo "📧 Testing email configuration..."
python3 << EOF
import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    email_username = os.environ.get('EMAIL_USERNAME')
    email_password = os.environ.get('EMAIL_PASSWORD')
    
    if not email_username or not email_password:
        print("❌ Email credentials not found")
        exit(1)
    
    msg = MIMEMultipart()
    msg['From'] = email_username
    msg['To'] = email_username
    msg['Subject'] = "ParkMate Email Test"
    
    body = "<h2>🎉 ParkMate Email Service is Working!</h2><p>Welcome emails will now be sent successfully.</p>"
    msg.attach(MIMEText(body, 'html'))
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_username, email_password)
    server.sendmail(email_username, email_username, msg.as_string())
    server.quit()
    
    print("✅ Test email sent successfully!")
    print(f"📬 Check {email_username} for the test email")
    
except Exception as e:
    print(f"❌ Email test failed: {e}")
    print("🔧 Please check your Gmail credentials and app password")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Email service setup completed successfully!"
    echo ""
    echo "📋 To start the complete system:"
    echo "1. Terminal 1: python main.py"
    echo "2. Terminal 2: ./start_celery_worker.sh"
    echo ""
    echo "✨ Now try registering a new user to test welcome emails!"
    echo ""
    echo "📧 Email troubleshooting:"
    echo "- Make sure you're using Gmail App Password, not regular password"
    echo "- Enable 2-Step Verification in Google Account"
    echo "- Generate App Password in Google Account Security settings"
else
    echo "❌ Setup failed. Please check your email configuration."
fi
