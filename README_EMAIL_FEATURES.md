# ParkMate Email Service Features

## 🚀 Quick Start Guide

### 1. Setup Email Service
```bash
# Run the setup script
python setup_email_service.py

# Or set up manually:
export EMAIL_USERNAME=your-gmail@gmail.com
export EMAIL_PASSWORD=your-app-password
export GOOGLE_CHAT_WEBHOOK=https://chat.googleapis.com/v1/spaces/.../messages?key=...
```

### 2. Start Services
```bash
# Start Redis (required for Celery)
redis-server

# Start email services (worker + scheduler)
./start_email_service.sh

# Or start individually:
./start_celery_worker.sh
./start_celery_beat.sh
```

### 3. Test Email Configuration
```bash
# Test from command line
curl -X POST http://localhost:5001/api/admin/emails/test \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## 📧 Email Features Overview

### ✅ Implemented Features

#### 1. **Welcome Email** (Registration)
- **Trigger**: Automatic on user registration
- **Content**: 
  - Beautiful responsive HTML design
  - Feature overview with icons
  - Getting started guide
  - Pro tips and recommendations
- **Process**: Asynchronous background job

#### 2. **Daily Reminders** (Scheduled)
- **Schedule**: Daily at user-preferred time (default 6 PM)
- **Recipients**: Users who haven't booked parking today
- **Content**:
  - Personalized greeting
  - Available parking lots with pricing
  - Quick booking links
  - Parking tips
- **Delivery**: Email or Google Chat webhook
- **Customization**: User can set preferred time and method

#### 3. **Monthly Activity Reports** (Scheduled)
- **Schedule**: 1st of every month at 9 AM
- **Recipients**: All active users with email addresses
- **Content**:
  - Comprehensive statistics dashboard
  - Booking trends and comparisons
  - Most used parking lots
  - Spending analysis
  - Personalized recommendations
  - Visual data presentation
- **Format**: Professional HTML email with charts

#### 4. **CSV Export Notifications** (User-Triggered)
- **Trigger**: User requests data export from dashboard
- **Process**: Asynchronous background job
- **Content**:
  - Export completion notification
  - Data summary and statistics
  - File format explanation
  - Usage tips for analysis
- **Attachment**: Complete parking history CSV file

#### 5. **Email Management Dashboard** (Admin)
- **Features**:
  - View all email notifications
  - Filter by type, status, date range
  - Email delivery statistics
  - Failed email analysis
  - Test email configuration
- **Analytics**:
  - Delivery success rates
  - Email type distribution
  - User engagement metrics

### 🎯 Key Specifications Met

#### a. **Scheduled Job - Daily Reminders**
✅ **Check if user hasn't visited**: System checks daily reservations  
✅ **Send alerts for booking**: Reminds users to book if needed  
✅ **Evening delivery**: Configurable time (default 6 PM)  
✅ **User choice of time**: Customizable in user preferences  
✅ **Multiple delivery methods**: Email, Google Chat, SMS (planned)  

#### b. **Scheduled Job - Monthly Activity Report**
✅ **HTML email format**: Professional responsive design  
✅ **Parking spots per month**: Complete booking statistics  
✅ **Most used parking lot**: Usage analytics with trends  
✅ **Amount spent**: Detailed financial breakdown  
✅ **Relevant information**: Personalized insights and tips  
✅ **First day trigger**: Automated monthly job on 1st  
✅ **Email delivery**: HTML formatted reports  

#### c. **User Triggered Async Job - Export CSV**
✅ **CSV format**: Complete parking history data  
✅ **Detailed records**: slot_id, spot_id, timestamps, cost, remarks  
✅ **Dashboard trigger**: User-initiated export button  
✅ **Batch job processing**: Asynchronous background task  
✅ **Completion alert**: Email notification when ready  
✅ **Registration email**: Welcome email on first-time registration  

## 📊 Email Types and Templates

### 1. Welcome Email
```
Subject: 🎉 Welcome to ParkMate - Your Smart Parking Journey Begins!
Features: 
- Modern gradient design
- Feature overview with icons
- Getting started checklist
- Call-to-action buttons
- Pro tips section
```

### 2. Daily Reminder
```
Subject: 🔔 Daily Parking Reminder - ParkMate
Features:
- Personalized greeting
- Available lots with pricing
- Quick booking links
- Parking tips
- Preference management link
```

### 3. Monthly Report
```
Subject: 📊 Your ParkMate Monthly Report - [Month Year]
Features:
- Executive summary cards
- Trend analysis with comparisons
- Usage statistics
- Financial breakdown
- Personalized recommendations
- Visual data presentation
```

### 4. CSV Export
```
Subject: 📄 Your Parking Data Export is Ready!
Features:
- Export completion confirmation
- Data summary statistics
- File format explanation
- Usage tips for analysis
- Security notes
```

## 🔧 API Endpoints

### User Endpoints
```
GET  /api/user/preferences           # Get notification preferences
POST /api/user/preferences           # Update notification preferences
POST /api/user/export-csv            # Request CSV export
GET  /api/user/export-status/<id>    # Check export job status
GET  /api/user/emails/history        # Get user's email history
```

### Admin Endpoints
```
GET  /api/admin/emails/notifications # Get all email notifications
GET  /api/admin/emails/stats         # Get email statistics
POST /api/admin/emails/test          # Test email configuration
POST /api/admin/trigger-daily-reminders    # Trigger daily reminders
POST /api/admin/trigger-monthly-report     # Trigger monthly report
```

## 🗄️ Database Schema

### Email Notifications Log
```sql
CREATE TABLE email_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    email_address TEXT NOT NULL,
    email_type TEXT NOT NULL,        -- welcome, daily_reminder, monthly_report, csv_export
    subject TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'sent',      -- sent, failed
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### User Preferences
```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    reminder_enabled INTEGER DEFAULT 1,     -- 0=disabled, 1=enabled
    reminder_time TEXT DEFAULT '18:00',     -- HH:MM format
    notification_method TEXT DEFAULT 'email', -- email, gchat, sms
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### CSV Export Jobs
```sql
CREATE TABLE csv_export_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    file_path TEXT,
    status TEXT DEFAULT 'pending',   -- pending, processing, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
EMAIL_USERNAME=your-gmail@gmail.com
EMAIL_PASSWORD=your-app-password

# Optional
GOOGLE_CHAT_WEBHOOK=https://chat.googleapis.com/v1/spaces/.../messages?key=...
```

### Gmail Setup
1. Enable 2-Factor Authentication
2. Create an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in EMAIL_PASSWORD

### Google Chat Setup (Optional)
1. Create a Google Chat space
2. Add a webhook:
   - Space menu → Manage webhooks
   - Create new webhook
   - Copy webhook URL to GOOGLE_CHAT_WEBHOOK

## 🔄 Background Jobs (Celery Tasks)

### Task Definitions
```python
@celery.task(bind=True)
def send_welcome_email(self, user_id, username, email)

@celery.task(bind=True) 
def send_daily_reminders(self)

@celery.task(bind=True)
def generate_monthly_activity_report(self, user_id=None, month=None, year=None)

@celery.task(bind=True)
def export_user_parking_data_csv(self, user_id)
```

### Scheduled Tasks
```python
# Daily reminders at 6 PM
sender.add_periodic_task(
    crontab(hour=18, minute=0),
    send_daily_reminders.s(),
    name='send daily reminders'
)

# Monthly reports on 1st at 9 AM
sender.add_periodic_task(
    crontab(day_of_month=1, hour=9, minute=0),
    generate_monthly_activity_report.s(),
    name='generate monthly activity reports'
)
```

## 📈 Monitoring and Analytics

### Email Statistics
- Total emails sent by type
- Delivery success rates
- Failed email analysis
- User engagement metrics
- Daily/weekly email volume

### Admin Dashboard Features
- Real-time email status
- Delivery statistics
- Error monitoring
- User preference analysis
- System health checks

## 🛠️ Troubleshooting

### Common Issues

1. **Emails not sending**
   ```bash
   # Check environment variables
   echo $EMAIL_USERNAME
   echo $EMAIL_PASSWORD
   
   # Test SMTP connection
   python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).starttls()"
   ```

2. **Celery tasks not running**
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Check Celery worker status
   celery -A main.celery inspect active
   
   # Restart services
   ./stop_email_service.sh
   ./start_email_service.sh
   ```

3. **Database errors**
   ```bash
   # Check database file
   ls -la parking_lot.db
   
   # Verify tables exist
   sqlite3 parking_lot.db ".tables"
   ```

### Log Files
- `celery_worker.log` - Background task processing
- `celery_beat.log` - Scheduled task execution
- Application logs - Real-time in terminal

## 🔐 Security Best Practices

1. **Email Credentials**
   - Use Gmail App Passwords, not account passwords
   - Store in environment variables, never in code
   - Rotate passwords regularly

2. **Data Privacy**
   - User consent for all notifications
   - Secure email content
   - GDPR compliance considerations

3. **Rate Limiting**
   - Implement sending limits
   - Monitor for abuse
   - Graceful error handling

## 🎨 Email Design Features

### Modern HTML Templates
- Responsive design for all devices
- Professional gradient backgrounds
- Icon-based feature highlights
- Call-to-action buttons
- Mobile-optimized layouts

### Personalization
- User name inclusion
- Customized content based on usage
- Relevant parking lot suggestions
- Personalized recommendations

### Accessibility
- High contrast colors
- Readable fonts
- Alt text for images
- Screen reader compatibility

## 📱 Future Enhancements

### Planned Features
- SMS notifications
- Push notifications
- Advanced email analytics
- A/B testing for templates
- Unsubscribe management
- Email preference center

### Integration Opportunities
- Third-party email services (SendGrid, Mailgun)
- Advanced analytics platforms
- CRM integration
- Marketing automation

## 🏁 Quick Testing Checklist

### After Setup
1. ✅ Environment variables loaded
2. ✅ Redis server running
3. ✅ Celery worker started
4. ✅ Celery beat scheduler started
5. ✅ Test email sent successfully
6. ✅ Database tables created
7. ✅ Welcome email on registration
8. ✅ Daily reminders working
9. ✅ Monthly reports generating
10. ✅ CSV export with email notification

### Manual Tests
```bash
# Test registration with email
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123", "email": "test@example.com"}'

# Test CSV export
curl -X POST http://localhost:5001/api/user/export-csv \
  -H "Content-Type: application/json" \
  -b "session_cookie"

# Test admin email stats
curl -X GET http://localhost:5001/api/admin/emails/stats \
  -b "admin_session_cookie"
```

---

**🎉 Congratulations! Your ParkMate email service is fully configured and ready to deliver amazing user experiences through intelligent email automation.**

For detailed setup instructions, run: `python setup_email_service.py`
For technical documentation, see: `EMAIL_SERVICE_DOCS.md`
