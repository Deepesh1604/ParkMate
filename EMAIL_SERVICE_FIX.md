# 🚨 Email Service Fix for ParkMate

## Problem Identified
Users are not receiving welcome emails when registering because:

1. **❌ Email credentials not configured** - Environment variables `EMAIL_USERNAME` and `EMAIL_PASSWORD` are not set
2. **❌ Redis server not running** - Required for Celery task queue
3. **❌ Celery worker not running** - Required to process background email tasks

## 🛠️ Quick Fix Solutions

### Option 1: Automated Setup (Recommended)
Run the automated fix script:
```bash
./quick_email_fix.sh
```

### Option 2: Manual Setup

#### Step 1: Install Required Packages
```bash
pip install python-dotenv celery redis
```

#### Step 2: Create Email Configuration
Create a `.env` file in your project root:
```bash
# Email Configuration for ParkMate
EMAIL_USERNAME=your-gmail@gmail.com
EMAIL_PASSWORD=your-16-char-app-password

# Optional: Google Chat Webhook URL
# GOOGLE_CHAT_WEBHOOK=your_webhook_url_here
```

#### Step 3: Get Gmail App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification (if not already enabled)
3. Go to Security → App Passwords
4. Generate an app password for "Mail"
5. Use the 16-character password in your `.env` file

#### Step 4: Start Redis Server
```bash
# Ubuntu/Debian
sudo systemctl start redis-server

# Or start manually
redis-server --daemonize yes
```

#### Step 5: Start Celery Worker
```bash
# Load environment variables and start Celery
export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
celery -A main.celery worker --loglevel=info --pool=solo
```

## 🧪 Testing the Fix

### Test 1: Check Email Configuration
```bash
python debug_email.py
```

### Test 2: Register a New User
1. Start the Flask app: `python main.py`
2. Start Celery worker: `./start_celery_worker.sh` (created by quick_email_fix.sh)
3. Register a new user through the frontend
4. Check the email inbox for welcome email

### Test 3: Check Email Logs
```bash
sqlite3 parking_lot.db "SELECT * FROM email_notifications ORDER BY sent_at DESC LIMIT 5;"
```

## 🔧 Troubleshooting

### Issue: "Authentication failed"
- **Solution**: Make sure you're using Gmail App Password, not your regular password
- **Check**: 2-Step Verification must be enabled in Google Account

### Issue: "Connection refused"
- **Solution**: Redis server is not running
- **Fix**: `redis-server --daemonize yes`

### Issue: "Task not executed"
- **Solution**: Celery worker is not running
- **Fix**: Start Celery worker as shown above

### Issue: "ModuleNotFoundError: No module named 'dotenv'"
- **Solution**: Install python-dotenv
- **Fix**: `pip install python-dotenv`

## 📋 Service Start Order

For the email service to work properly, start services in this order:

1. **Redis Server**
   ```bash
   redis-server --daemonize yes
   ```

2. **Celery Worker** (in separate terminal)
   ```bash
   export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
   celery -A main.celery worker --loglevel=info --pool=solo
   ```

3. **Flask Application** (in separate terminal)
   ```bash
   python main.py
   ```

## 📧 Email Types Supported

After fixing, these email types will work:

- ✅ **Welcome Email** - Sent when users register
- ✅ **Daily Reminders** - Scheduled daily notifications
- ✅ **Monthly Reports** - HTML activity reports
- ✅ **CSV Export Notifications** - When CSV export is ready

## 🔍 Verification Steps

1. **Check Redis**: `redis-cli ping` should return "PONG"
2. **Check Environment**: `echo $EMAIL_USERNAME` should show your email
3. **Check Database**: Email logs should appear in `email_notifications` table
4. **Check Email Inbox**: Test emails should be received

## 📞 Support

If issues persist:
1. Run `python debug_email.py` for detailed diagnostics
2. Check Celery worker logs for error messages
3. Verify Gmail App Password is correct and 2-Step Verification is enabled

---

**🎉 Once fixed, users will receive beautiful HTML welcome emails upon registration!**
