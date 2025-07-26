import sqlite3
import hashlib
import json
import redis
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from celery import Celery
from functools import wraps
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import csv
import io
import requests
import os
from celery.schedules import crontab
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import base64
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'parking_lot_secret_key_2024'

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME', 'your-email@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your-app-password')
EMAIL_FROM = EMAIL_USERNAME

# Google Chat Webhook URL (set via environment variable)
GOOGLE_CHAT_WEBHOOK = os.environ.get('GOOGLE_CHAT_WEBHOOK')

# Redis configuration
redis_client = redis.Redis(
    host='localhost', 
    port=6379, 
    db=0, 
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)

# Celery configuration
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend='redis://localhost:6379/1',
        broker='redis://localhost:6379/2'
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# Cache configuration
CACHE_TIMEOUT = 300  # 5 minutes
ANALYTICS_CACHE_TIMEOUT = 900  # 15 minutes

def cache_key(*args):
    """Generate cache key from arguments"""
    return ':'.join(str(arg) for arg in args)

def cached(timeout=CACHE_TIMEOUT, key_prefix=''):
    """Decorator for caching function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key_name = f"{key_prefix}:{f.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            try:
                # Try to get from cache
                cached_result = redis_client.get(cache_key_name)
                if cached_result:
                    logger.info(f"Cache hit for {cache_key_name}")
                    return json.loads(cached_result)
            except redis.RedisError as e:
                logger.warning(f"Redis cache read error: {e}")
            
            # Execute function
            result = f(*args, **kwargs)
            
            try:
                # Store in cache
                redis_client.setex(cache_key_name, timeout, json.dumps(result, default=str))
                logger.info(f"Cached result for {cache_key_name}")
            except redis.RedisError as e:
                logger.warning(f"Redis cache write error: {e}")
            
            return result
        return decorated_function
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate cache keys matching pattern"""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching {pattern}")
    except redis.RedisError as e:
        logger.warning(f"Cache invalidation error: {e}")

# Database initialization
def init_db():
    conn = sqlite3.connect('parking_lot.db')
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Parking Lots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prime_location_name TEXT NOT NULL,
            price REAL NOT NULL,
            address TEXT NOT NULL,
            pin_code TEXT NOT NULL,
            maximum_number_of_spots INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Parking Spots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            spot_number INTEGER NOT NULL,
            status TEXT DEFAULT 'A',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lot_id) REFERENCES parking_lots (id)
        )
    ''')
    
    # Create Reservations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            parking_timestamp TIMESTAMP,
            leaving_timestamp TIMESTAMP,
            parking_cost REAL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (spot_id) REFERENCES parking_spots (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create Batch Jobs table for tracking background tasks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            task_id TEXT,
            parameters TEXT,
            result TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create User Preferences table for reminder settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reminder_enabled INTEGER DEFAULT 1,
            reminder_time TEXT DEFAULT '18:00',
            notification_method TEXT DEFAULT 'email',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create CSV Export Jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS csv_export_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_path TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create admin user if not exists
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, email, is_admin) 
        VALUES (?, ?, ?, ?)
    ''', ('admin', admin_password, 'admin@parkinglot.com', 1))
    
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect('parking_lot.db')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def dict_factory(cursor, row):
    """Convert sqlite row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# Celery Tasks
@celery.task(bind=True)
def cleanup_expired_reservations(self):
    """Background task to cleanup expired reservations"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Find reservations that are active but haven't been used for 24 hours
        expiry_time = datetime.now() - timedelta(hours=24)
        
        cursor.execute('''
            SELECT r.id, r.spot_id FROM reservations r
            WHERE r.status = 'active' 
            AND r.parking_timestamp IS NULL 
            AND r.created_at < ?
        ''', (expiry_time,))
        
        expired_reservations = cursor.fetchall()
        
        if expired_reservations:
            # Update reservation status and free spots
            reservation_ids = [r[0] for r in expired_reservations]
            spot_ids = [r[1] for r in expired_reservations]
            
            # Update reservations to expired
            cursor.executemany(
                'UPDATE reservations SET status = "expired" WHERE id = ?',
                [(rid,) for rid in reservation_ids]
            )
            
            # Free up the spots
            cursor.executemany(
                'UPDATE parking_spots SET status = "A" WHERE id = ?',
                [(sid,) for sid in spot_ids]
            )
            
            conn.commit()
            
            # Invalidate relevant caches
            invalidate_cache_pattern('*parking_lots*')
            invalidate_cache_pattern('*analytics*')
            
            logger.info(f"Cleaned up {len(expired_reservations)} expired reservations")
            
        conn.close()
        return f"Cleaned up {len(expired_reservations)} expired reservations"
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_reservations: {e}")
        raise

@celery.task(bind=True)
def generate_daily_report(self, date_str=None):
    """Generate daily parking report"""
    try:
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Daily statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_reservations,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_reservations,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_reservations,
                SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired_reservations,
                COALESCE(SUM(parking_cost), 0) as total_revenue
            FROM reservations 
            WHERE DATE(created_at) = ?
        ''', (date_str,))
        
        daily_stats = cursor.fetchone()
        
        # Lot-wise statistics
        cursor.execute('''
            SELECT 
                pl.prime_location_name,
                COUNT(r.id) as reservations_count,
                COALESCE(SUM(r.parking_cost), 0) as revenue
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            LEFT JOIN reservations r ON ps.id = r.spot_id AND DATE(r.created_at) = ?
            GROUP BY pl.id, pl.prime_location_name
            ORDER BY reservations_count DESC
        ''', (date_str,))
        
        lot_stats = cursor.fetchall()
        
        report = {
            'date': date_str,
            'daily_summary': daily_stats,
            'lot_statistics': lot_stats,
            'generated_at': datetime.now().isoformat()
        }
        
        # Store report in cache for quick access
        report_key = f"daily_report:{date_str}"
        redis_client.setex(report_key, 86400, json.dumps(report, default=str))  # Cache for 24 hours
        
        conn.close()
        logger.info(f"Generated daily report for {date_str}")
        return report
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise

@celery.task(bind=True)
def optimize_parking_allocation(self):
    """Analyze and optimize parking spot allocation"""
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Analyze usage patterns
        cursor.execute('''
            SELECT 
                pl.id,
                pl.prime_location_name,
                pl.maximum_number_of_spots,
                COUNT(r.id) as total_reservations,
                AVG(CASE 
                    WHEN r.parking_timestamp AND r.leaving_timestamp 
                    THEN (julianday(r.leaving_timestamp) - julianday(r.parking_timestamp)) * 24 
                    ELSE NULL 
                END) as avg_duration_hours,
                SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as currently_occupied
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            LEFT JOIN reservations r ON ps.id = r.spot_id 
                AND r.created_at >= date('now', '-7 days')
            GROUP BY pl.id
        ''', ())
        
        lot_analysis = cursor.fetchall()
        
        recommendations = []
        for lot in lot_analysis:
            utilization_rate = (lot['total_reservations'] / (lot['maximum_number_of_spots'] * 7)) if lot['maximum_number_of_spots'] > 0 else 0
            
            if utilization_rate > 0.8:
                recommendations.append({
                    'lot_id': lot['id'],
                    'lot_name': lot['prime_location_name'],
                    'recommendation': 'Consider adding more spots - high utilization',
                    'utilization_rate': round(utilization_rate, 2),
                    'priority': 'high'
                })
            elif utilization_rate < 0.3:
                recommendations.append({
                    'lot_id': lot['id'],
                    'lot_name': lot['prime_location_name'],
                    'recommendation': 'Low utilization - consider marketing or pricing adjustment',
                    'utilization_rate': round(utilization_rate, 2),
                    'priority': 'medium'
                })
        
        # Cache recommendations
        redis_client.setex('parking_optimization', 3600, json.dumps(recommendations, default=str))
        
        conn.close()
        logger.info(f"Generated {len(recommendations)} optimization recommendations")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error in parking optimization: {e}")
        raise

# Helper functions for notifications
def send_email(to_email, subject, body, attachment=None):
    """Send email notification"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        if attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment['data'])
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment["filename"]}'
            )
            msg.attach(part)
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, to_email, text)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def send_google_chat_message(message):
    """Send message to Google Chat webhook"""
    try:
        if not GOOGLE_CHAT_WEBHOOK:
            logger.warning("Google Chat webhook URL not configured")
            return False
            
        payload = {'text': message}
        response = requests.post(GOOGLE_CHAT_WEBHOOK, json=payload)
        
        if response.status_code == 200:
            logger.info("Google Chat message sent successfully")
            return True
        else:
            logger.error(f"Failed to send Google Chat message: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error sending Google Chat message: {e}")
        return False

# New Celery Tasks
@celery.task(bind=True)
def send_daily_reminders(self):
    """Send daily reminders to users who haven't visited or need to book parking"""
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get all users with reminder preferences
        cursor.execute('''
            SELECT 
                u.id, u.username, u.email, u.phone,
                up.reminder_enabled, up.notification_method,
                up.reminder_time
            FROM users u
            LEFT JOIN user_preferences up ON u.id = up.user_id
            WHERE u.is_admin = 0 AND (up.reminder_enabled = 1 OR up.reminder_enabled IS NULL)
        ''')
        
        users = cursor.fetchall()
        reminders_sent = 0
        
        for user in users:
            # Check if user has active reservation
            cursor.execute('''
                SELECT COUNT(*) as active_count
                FROM reservations 
                WHERE user_id = ? AND status = 'active'
            ''', (user['id'],))
            
            active_reservations = cursor.fetchone()['active_count']
            
            # Check if user has visited today
            cursor.execute('''
                SELECT COUNT(*) as today_visits
                FROM reservations 
                WHERE user_id = ? AND DATE(created_at) = DATE('now')
            ''', (user['id'],))
            
            today_visits = cursor.fetchone()['today_visits']
            
            # Send reminder if user hasn't visited today and has no active reservations
            if today_visits == 0 and active_reservations == 0:
                message = f"Hi {user['username']},\n\nReminder: You haven't booked a parking spot today. If you need parking, please book a spot through our app.\n\nBest regards,\nParking Management System"
                
                notification_method = user.get('notification_method', 'email')
                
                if notification_method == 'email' and user['email']:
                    if send_email(user['email'], "Daily Parking Reminder", message):
                        reminders_sent += 1
                elif notification_method == 'gchat':
                    chat_message = f"📅 Daily Reminder: {user['username']}, you haven't booked parking today. Book now if needed!"
                    if send_google_chat_message(chat_message):
                        reminders_sent += 1
        
        conn.close()
        logger.info(f"Sent {reminders_sent} daily reminders")
        return f"Sent {reminders_sent} daily reminders"
        
    except Exception as e:
        logger.error(f"Error sending daily reminders: {e}")
        raise

@celery.task(bind=True)
def generate_monthly_activity_report(self, user_id=None, month=None, year=None):
    """Generate monthly activity report for user(s)"""
    try:
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
            
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get users to generate reports for
        if user_id:
            cursor.execute('SELECT * FROM users WHERE id = ? AND is_admin = 0', (user_id,))
            users = cursor.fetchall()
        else:
            cursor.execute('SELECT * FROM users WHERE is_admin = 0')
            users = cursor.fetchall()
        
        reports_generated = 0
        
        for user in users:
            # Generate monthly statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_bookings,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_bookings,
                    COALESCE(SUM(parking_cost), 0) as total_spent,
                    AVG(CASE 
                        WHEN parking_timestamp IS NOT NULL AND leaving_timestamp IS NOT NULL 
                        THEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24 
                        ELSE NULL 
                    END) as avg_duration_hours
                FROM reservations 
                WHERE user_id = ? 
                    AND strftime('%Y', created_at) = ? 
                    AND strftime('%m', created_at) = ?
            ''', (user['id'], str(year), str(month).zfill(2)))
            
            monthly_stats = cursor.fetchone()
            
            # Most used parking lot
            cursor.execute('''
                SELECT 
                    pl.prime_location_name,
                    COUNT(*) as usage_count
                FROM reservations r
                JOIN parking_spots ps ON r.spot_id = ps.id
                JOIN parking_lots pl ON ps.lot_id = pl.id
                WHERE r.user_id = ? 
                    AND strftime('%Y', r.created_at) = ? 
                    AND strftime('%m', r.created_at) = ?
                GROUP BY pl.id, pl.prime_location_name
                ORDER BY usage_count DESC
                LIMIT 1
            ''', (user['id'], str(year), str(month).zfill(2)))
            
            most_used_lot = cursor.fetchone()
            
            # Daily usage pattern
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as bookings
                FROM reservations
                WHERE user_id = ? 
                    AND strftime('%Y', created_at) = ? 
                    AND strftime('%m', created_at) = ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (user['id'], str(year), str(month).zfill(2)))
            
            daily_usage = cursor.fetchall()
            
            # Generate HTML report
            html_report = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Monthly Parking Activity Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .stat-box {{ background-color: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                    .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    .table th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Monthly Parking Activity Report</h1>
                    <p><strong>User:</strong> {user['username']}</p>
                    <p><strong>Period:</strong> {month}/{year}</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="stat-box">
                    <h2>Monthly Summary</h2>
                    <p><strong>Total Bookings:</strong> {monthly_stats['total_bookings']}</p>
                    <p><strong>Completed Bookings:</strong> {monthly_stats['completed_bookings']}</p>
                    <p><strong>Total Amount Spent:</strong> ${monthly_stats['total_spent']:.2f}</p>
                    <p><strong>Average Parking Duration:</strong> {monthly_stats['avg_duration_hours']:.2f} hours</p>
                </div>
                
                <div class="stat-box">
                    <h2>Most Used Parking Lot</h2>
                    <p>{most_used_lot['prime_location_name'] if most_used_lot else 'No parking lot usage this month'}</p>
                    <p>Usage Count: {most_used_lot['usage_count'] if most_used_lot else 0}</p>
                </div>
                
                <div class="stat-box">
                    <h2>Daily Usage Pattern</h2>
                    <table class="table">
                        <tr><th>Date</th><th>Bookings</th></tr>
            """
            
            for day in daily_usage:
                html_report += f"<tr><td>{day['date']}</td><td>{day['bookings']}</td></tr>"
            
            html_report += """
                    </table>
                </div>
                
                <div class="stat-box">
                    <h2>Tips for Next Month</h2>
                    <ul>
                        <li>Book parking spots in advance to ensure availability</li>
                        <li>Consider off-peak hours for better rates</li>
                        <li>Check for monthly parking passes for regular users</li>
                    </ul>
                </div>
            </body>
            </html>
            """
            
            # Send report via email
            if user['email']:
                if send_email(
                    user['email'], 
                    f"Monthly Parking Report - {month}/{year}",
                    html_report
                ):
                    reports_generated += 1
        
        conn.close()
        logger.info(f"Generated {reports_generated} monthly reports")
        return f"Generated {reports_generated} monthly reports for {month}/{year}"
        
    except Exception as e:
        logger.error(f"Error generating monthly reports: {e}")
        raise

@celery.task(bind=True)
def export_user_parking_data_csv(self, user_id):
    """Export user's parking data to CSV format"""
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get user data
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Get all parking data for the user
        cursor.execute('''
            SELECT 
                r.id as reservation_id,
                ps.id as slot_id,
                ps.spot_number as spot_id,
                pl.prime_location_name as parking_lot,
                r.created_at as booking_timestamp,
                r.parking_timestamp,
                r.leaving_timestamp,
                r.parking_cost,
                r.status,
                pl.address,
                pl.pin_code,
                CASE 
                    WHEN r.parking_timestamp IS NOT NULL AND r.leaving_timestamp IS NOT NULL 
                    THEN (julianday(r.leaving_timestamp) - julianday(r.parking_timestamp)) * 24 
                    ELSE NULL 
                END as duration_hours,
                'Regular booking' as remarks
            FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
        ''', (user_id,))
        
        parking_data = cursor.fetchall()
        
        # Create CSV data
        csv_data = io.StringIO()
        fieldnames = [
            'reservation_id', 'slot_id', 'spot_id', 'parking_lot', 'booking_timestamp',
            'parking_timestamp', 'leaving_timestamp', 'duration_hours', 'parking_cost',
            'status', 'address', 'pin_code', 'remarks'
        ]
        
        writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in parking_data:
            writer.writerow(row)
        
        csv_content = csv_data.getvalue()
        csv_data.close()
        
        # Save to file system
        filename = f"parking_data_{user['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join('exports', filename)
        
        # Create exports directory if it doesn't exist
        os.makedirs('exports', exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            f.write(csv_content)
        
        # Update CSV export job status
        cursor.execute('''
            UPDATE csv_export_jobs 
            SET status = 'completed', file_path = ?, completed_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'processing'
        ''', (filepath, user_id))
        
        conn.commit()
        
        # Send notification to user
        cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
        user_email = cursor.fetchone()['email']
        
        if user_email:
            with open(filepath, 'rb') as f:
                csv_bytes = f.read()
            
            attachment = {
                'filename': filename,
                'data': csv_bytes
            }
            
            email_body = f"""
            <html>
            <body>
                <h2>Your Parking Data Export is Ready!</h2>
                <p>Dear {user['username']},</p>
                <p>Your parking data export has been completed successfully.</p>
                <p>The attached CSV file contains:</p>
                <ul>
                    <li>All your parking reservations</li>
                    <li>Booking timestamps</li>
                    <li>Parking duration and costs</li>
                    <li>Location details</li>
                </ul>
                <p>Total records: {len(parking_data)}</p>
                <p>Export generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <br>
                <p>Best regards,<br>Parking Management System</p>
            </body>
            </html>
            """
            
            send_email(user_email, "Your Parking Data Export", email_body, attachment)
        
        conn.close()
        logger.info(f"CSV export completed for user {user_id}: {filename}")
        return {
            'filename': filename,
            'filepath': filepath,
            'records_count': len(parking_data)
        }
        
    except Exception as e:
        logger.error(f"Error exporting CSV for user {user_id}: {e}")
        # Update job status to failed
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE csv_export_jobs 
                SET status = 'failed'
                WHERE user_id = ? AND status = 'processing'
            ''', (user_id,))
            conn.commit()
            conn.close()
        except:
            pass
        raise

# Authentication APIs
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone', '')
        
        if not username or not password or not email:
            return jsonify({'error': 'Username, password, and email are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create new user
        hashed_password = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password, email, phone, is_admin) 
            VALUES (?, ?, ?, ?, 0)
        ''', (username, hashed_password, email, phone))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Invalidate user-related caches and analytics
        invalidate_cache_pattern('*users*')
        invalidate_cache_pattern('*admin*')
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        hashed_password = hash_password(password)
        cursor.execute('''
            SELECT id, username, email, phone, is_admin 
            FROM users WHERE username = ? AND password = ?
        ''', (username, hashed_password))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        session['user_id'] = user['id']
        session['is_admin'] = user['is_admin']
        
        return jsonify({
            'message': 'Login successful',
            'user': user
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# Admin APIs with caching
@app.route('/api/admin/parking-lots', methods=['GET', 'POST'])
def admin_parking_lots():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    if request.method == 'GET':
        @cached(timeout=CACHE_TIMEOUT, key_prefix='admin')
        def get_parking_lots():
            cursor.execute('''
                SELECT 
                    pl.*,
                    COUNT(ps.id) as total_spots,
                    SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots,
                    SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots
                FROM parking_lots pl
                LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
                GROUP BY pl.id
                ORDER BY pl.created_at DESC
            ''')
            return cursor.fetchall()
        
        lots = get_parking_lots()
        conn.close()
        return jsonify({'parking_lots': lots}), 200
    
    elif request.method == 'POST':
        try:
            data = request.json
            location_name = data.get('prime_location_name')
            price = data.get('price')
            address = data.get('address')
            pin_code = data.get('pin_code')
            max_spots = data.get('maximum_number_of_spots')
            
            if not all([location_name, price, address, pin_code, max_spots]):
                return jsonify({'error': 'All fields are required'}), 400
            
            # Create parking lot
            cursor.execute('''
                INSERT INTO parking_lots (prime_location_name, price, address, pin_code, maximum_number_of_spots)
                VALUES (?, ?, ?, ?, ?)
            ''', (location_name, price, address, pin_code, max_spots))
            
            lot_id = cursor.lastrowid
            
            # Create parking spots for this lot
            for spot_num in range(1, max_spots + 1):
                cursor.execute('''
                    INSERT INTO parking_spots (lot_id, spot_number, status)
                    VALUES (?, ?, 'A')
                ''', (lot_id, spot_num))
            
            conn.commit()
            conn.close()
            
            # Invalidate related caches and analytics
            invalidate_cache_pattern('*parking_lots*')
            invalidate_cache_pattern('*admin*')
            
            return jsonify({
                'message': 'Parking lot created successfully',
                'lot_id': lot_id
            }), 201
            
        except Exception as e:
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/admin/parking-lots/<int:lot_id>', methods=['PUT'])
def update_parking_lot(lot_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.json
        location_name = data.get('prime_location_name')
        price = data.get('price')
        address = data.get('address')
        pin_code = data.get('pin_code')
        max_spots = data.get('maximum_number_of_spots')
        
        if not all([location_name, price, address, pin_code, max_spots]):
            return jsonify({'error': 'All fields are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if lot exists
        cursor.execute('SELECT * FROM parking_lots WHERE id = ?', (lot_id,))
        existing_lot = cursor.fetchone()
        if not existing_lot:
            conn.close()
            return jsonify({'error': 'Parking lot not found'}), 404
        
        # Update parking lot
        cursor.execute('''
            UPDATE parking_lots 
            SET prime_location_name = ?, price = ?, address = ?, pin_code = ?, maximum_number_of_spots = ?
            WHERE id = ?
        ''', (location_name, price, address, pin_code, max_spots, lot_id))
        
        # Get current spots count
        cursor.execute('SELECT COUNT(*) as count FROM parking_spots WHERE lot_id = ?', (lot_id,))
        current_spots_count = cursor.fetchone()[0]
        
        # Add or remove spots if needed
        if max_spots > current_spots_count:
            # Add new spots
            for spot_num in range(current_spots_count + 1, max_spots + 1):
                cursor.execute('''
                    INSERT INTO parking_spots (lot_id, spot_number, status)
                    VALUES (?, ?, 'A')
                ''', (lot_id, spot_num))
        elif max_spots < current_spots_count:
            # Remove excess spots (only if they're not occupied)
            cursor.execute('''
                SELECT COUNT(*) as occupied FROM parking_spots 
                WHERE lot_id = ? AND spot_number > ? AND status = 'O'
            ''', (lot_id, max_spots))
            occupied_excess = cursor.fetchone()[0]
            
            if occupied_excess > 0:
                conn.close()
                return jsonify({'error': 'Cannot reduce spots: some excess spots are occupied'}), 400
            
            cursor.execute('''
                DELETE FROM parking_spots 
                WHERE lot_id = ? AND spot_number > ?
            ''', (lot_id, max_spots))
        
        conn.commit()
        conn.close()
        
        # Invalidate related caches
        invalidate_cache_pattern('*parking_lots*')
        invalidate_cache_pattern('*admin*')
        
        return jsonify({'message': 'Parking lot updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/parking-lots/<int:lot_id>', methods=['DELETE'])
def delete_parking_lot(lot_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if lot exists
        cursor.execute('SELECT * FROM parking_lots WHERE id = ?', (lot_id,))
        existing_lot = cursor.fetchone()
        if not existing_lot:
            conn.close()
            return jsonify({'error': 'Parking lot not found'}), 404
        
        # Check if lot has any occupied spots
        cursor.execute('SELECT COUNT(*) as occupied FROM parking_spots WHERE lot_id = ? AND status = "O"', (lot_id,))
        occupied_spots = cursor.fetchone()[0]
        
        if occupied_spots > 0:
            conn.close()
            return jsonify({'error': 'Cannot delete lot: it has occupied spots'}), 400
        
        # Check if lot has any active reservations
        cursor.execute('''
            SELECT COUNT(*) as active_reservations 
            FROM reservations r 
            JOIN parking_spots ps ON r.spot_id = ps.id 
            WHERE ps.lot_id = ? AND r.status = 'active'
        ''', (lot_id,))
        active_reservations = cursor.fetchone()[0]
        
        if active_reservations > 0:
            conn.close()
            return jsonify({'error': 'Cannot delete lot: it has active reservations'}), 400
        
        # Delete all spots first (foreign key constraint)
        cursor.execute('DELETE FROM parking_spots WHERE lot_id = ?', (lot_id,))
        
        # Delete the parking lot
        cursor.execute('DELETE FROM parking_lots WHERE id = ?', (lot_id,))
        
        conn.commit()
        conn.close()
        
        # Invalidate related caches
        invalidate_cache_pattern('*parking_lots*')
        invalidate_cache_pattern('*admin*')
        
        return jsonify({'message': 'Parking lot deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/parking-spots', methods=['GET'])
def admin_parking_spots():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        lot_id = request.args.get('lot_id')
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        if lot_id:
            # Get spots for specific lot
            cursor.execute('''
                SELECT 
                    ps.id,
                    ps.spot_number,
                    ps.status,
                    pl.id as lot_id,
                    pl.prime_location_name as lot_name,
                    r.id as reservation_id,
                    r.parking_timestamp,
                    r.parking_cost,
                    u.username,
                    u.email,
                    u.phone
                FROM parking_spots ps
                JOIN parking_lots pl ON ps.lot_id = pl.id
                LEFT JOIN reservations r ON ps.id = r.spot_id AND r.status = 'active'
                LEFT JOIN users u ON r.user_id = u.id
                WHERE pl.id = ?
                ORDER BY ps.spot_number
            ''', (lot_id,))
        else:
            # Get all spots
            cursor.execute('''
                SELECT 
                    ps.id,
                    ps.spot_number,
                    ps.status,
                    pl.id as lot_id,
                    pl.prime_location_name as lot_name,
                    r.id as reservation_id,
                    r.parking_timestamp,
                    r.parking_cost,
                    u.username,
                    u.email,
                    u.phone
                FROM parking_spots ps
                JOIN parking_lots pl ON ps.lot_id = pl.id
                LEFT JOIN reservations r ON ps.id = r.spot_id AND r.status = 'active'
                LEFT JOIN users u ON r.user_id = u.id
                ORDER BY pl.prime_location_name, ps.spot_number
            ''')
        
        spots_data = cursor.fetchall()
        conn.close()
        
        # Format the data
        parking_spots = []
        for spot in spots_data:
            spot_data = {
                'id': spot['id'],
                'spot_number': spot['spot_number'],
                'status': spot['status'],
                'lot_id': spot['lot_id'],
                'lot_name': spot['lot_name'],
                'reservation': None
            }
            
            if spot['reservation_id']:
                spot_data['reservation'] = {
                    'id': spot['reservation_id'],
                    'username': spot['username'],
                    'email': spot['email'],
                    'phone': spot['phone'],
                    'parking_timestamp': spot['parking_timestamp'],
                    'parking_cost': spot['parking_cost']
                }
            
            parking_spots.append(spot_data)
        
        return jsonify({'parking_spots': parking_spots}), 200
        
    except Exception as e:
        logger.error(f"Error in admin_parking_spots: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/parking-spots/<int:spot_id>/free', methods=['PATCH'])
def free_parking_spot(spot_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if spot exists
        cursor.execute('SELECT * FROM parking_spots WHERE id = ?', (spot_id,))
        spot = cursor.fetchone()
        if not spot:
            conn.close()
            return jsonify({'error': 'Parking spot not found'}), 404
        
        # Update spot status to available
        cursor.execute('UPDATE parking_spots SET status = ? WHERE id = ?', ('A', spot_id))
        
        # End any active reservations for this spot
        cursor.execute('''
            UPDATE reservations 
            SET status = 'completed', end_timestamp = CURRENT_TIMESTAMP 
            WHERE spot_id = ? AND status = 'active'
        ''', (spot_id,))
        
        conn.commit()
        conn.close()
        
        # Invalidate related caches
        invalidate_cache_pattern('*admin*')
        
        return jsonify({'message': 'Parking spot freed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error freeing parking spot: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    @cached(timeout=CACHE_TIMEOUT, key_prefix='admin:users')
    def get_users_with_stats():
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get all users with their statistics
        cursor.execute('''
            SELECT 
                u.id,
                u.username,
                u.email,
                u.phone,
                u.created_at,
                COUNT(DISTINCT r.id) as total_reservations,
                COUNT(DISTINCT CASE WHEN r.status = 'active' THEN r.id END) as active_reservations,
                SUM(CASE WHEN r.parking_cost IS NOT NULL THEN r.parking_cost ELSE 0 END) as total_spent,
                MAX(r.created_at) as last_reservation_date
            FROM users u
            LEFT JOIN reservations r ON u.id = r.user_id
            WHERE u.is_admin = 0
            GROUP BY u.id, u.username, u.email, u.phone, u.created_at
            ORDER BY u.created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        return users
    
    users = get_users_with_stats()
    return jsonify({'users': users}), 200

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists and is not an admin
        cursor.execute('SELECT id, username, is_admin FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user[2]:  # is_admin check
            return jsonify({'error': 'Cannot delete admin users'}), 400
        
        # First, delete all reservations for this user
        cursor.execute('DELETE FROM reservations WHERE user_id = ?', (user_id,))
        
        # Then delete the user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        # Clear cache to ensure updated data
        try:
            redis_client.delete('admin:users')
            redis_client.delete('admin:analytics')
        except:
            pass  # Cache clearing is optional
        
        logger.info(f"Admin deleted user: {user[1]} (ID: {user_id})")
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500

@app.route('/api/admin/analytics', methods=['GET'])
def admin_analytics():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Total statistics
        cursor.execute('SELECT COUNT(*) as total_lots FROM parking_lots')
        total_lots = cursor.fetchone()['total_lots']
        
        cursor.execute('SELECT COUNT(*) as total_spots FROM parking_spots')
        total_spots = cursor.fetchone()['total_spots']
        
        cursor.execute('SELECT COUNT(*) as occupied_spots FROM parking_spots WHERE status = "O"')
        occupied_spots = cursor.fetchone()['occupied_spots']
        
        cursor.execute('SELECT COUNT(*) as total_users FROM users WHERE is_admin = 0')
        total_users = cursor.fetchone()['total_users']
        
        cursor.execute('SELECT COUNT(*) as active_reservations FROM reservations WHERE status = "active"')
        active_reservations = cursor.fetchone()['active_reservations']
        
        # Revenue calculation
        cursor.execute('SELECT SUM(parking_cost) as total_revenue FROM reservations WHERE parking_cost IS NOT NULL')
        revenue_result = cursor.fetchone()
        total_revenue = revenue_result['total_revenue'] if revenue_result['total_revenue'] else 0
        
        # Lot occupancy rates
        cursor.execute('''
            SELECT 
                pl.id,
                pl.prime_location_name,
                pl.maximum_number_of_spots,
                COUNT(ps.id) as total_spots,
                SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots,
                ROUND((SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) * 100.0 / COUNT(ps.id)), 2) as occupancy_rate
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            GROUP BY pl.id
        ''')
        lot_occupancy = cursor.fetchall()
        
        conn.close()
        
        analytics_data = {
            'summary': {
                'total_lots': total_lots,
                'total_spots': total_spots,
                'occupied_spots': occupied_spots,
                'available_spots': total_spots - occupied_spots,
                'total_users': total_users,
                'active_reservations': active_reservations,
                'total_revenue': total_revenue,
                'occupancy_rate': round((occupied_spots / total_spots * 100) if total_spots > 0 else 0, 2)
            },
            'lot_occupancy': lot_occupancy
        }
        
        logger.info(f"Analytics data: {analytics_data}")
        return jsonify(analytics_data), 200
        
    except Exception as e:
        logger.error(f"Error in admin_analytics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Matplotlib graph generation endpoints
def generate_graph_base64(fig):
    """Convert matplotlib figure to base64 string"""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close(fig)
    return base64.b64encode(image_png).decode('utf-8')

@app.route('/api/admin/graphs/occupancy', methods=['GET'])
def generate_occupancy_graph():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get lot occupancy data
        cursor.execute('''
            SELECT 
                pl.prime_location_name,
                COUNT(ps.id) as total_spots,
                SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            GROUP BY pl.id
        ''')
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            # Generate sample data for demo
            data = [
                {'prime_location_name': 'Main Campus', 'total_spots': 50, 'occupied_spots': 30},
                {'prime_location_name': 'Library', 'total_spots': 25, 'occupied_spots': 15},
                {'prime_location_name': 'Sports Center', 'total_spots': 40, 'occupied_spots': 20},
                {'prime_location_name': 'Student Center', 'total_spots': 35, 'occupied_spots': 25}
            ]
        
        # Create DataFrame
        df = pd.DataFrame(data)
        df['available_spots'] = df['total_spots'] - df['occupied_spots']
        df['occupancy_rate'] = (df['occupied_spots'] / df['total_spots'] * 100).round(2)
        
        # Create figure with subplots - smaller size for better container fit
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(8, 6))
        fig.suptitle('Parking Lot Analytics Dashboard', fontsize=12, fontweight='bold', y=0.96)
        
        # 1. Occupancy pie chart
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
        wedges, texts, autotexts = ax1.pie(df['occupied_spots'], labels=df['prime_location_name'], 
                                          autopct='%1.1f%%', colors=colors[:len(df)])
        ax1.set_title('Current Occupancy Distribution', fontweight='bold')
        
        # 2. Bar chart - occupied vs available
        x = range(len(df))
        width = 0.35
        ax2.bar([i - width/2 for i in x], df['occupied_spots'], width, 
                label='Occupied', color='#FF6B6B', alpha=0.8)
        ax2.bar([i + width/2 for i in x], df['available_spots'], width, 
                label='Available', color='#4ECDC4', alpha=0.8)
        ax2.set_xlabel('Parking Lots')
        ax2.set_ylabel('Number of Spots')
        ax2.set_title('Occupied vs Available Spots', fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(df['prime_location_name'], rotation=45, ha='right')
        ax2.legend()
        ax2.grid(True, alpha=0.3)


        # 3. Occupancy rate bar chart
        bars = ax3.bar(df['prime_location_name'], df['occupancy_rate'], 
                       color=['#FF6B6B' if x > 80 else '#FECA57' if x > 60 else '#4ECDC4' 
                              for x in df['occupancy_rate']])
        ax3.set_xlabel('Parking Lots')
        ax3.set_ylabel('Occupancy Rate (%)')
        ax3.set_title('Occupancy Rate by Location', fontweight='bold')
        ax3.set_xticklabels(df['prime_location_name'], rotation=45, ha='right')
        ax3.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, rate in zip(bars, df['occupancy_rate']):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate}%', ha='center', va='bottom', fontweight='bold')
        
        # 4. Total capacity overview
        total_spots = df['total_spots'].sum()
        total_occupied = df['occupied_spots'].sum()
        total_available = total_spots - total_occupied
        
        sizes = [total_occupied, total_available]
        colors_overview = ['#FF6B6B', '#4ECDC4']
        wedges, texts, autotexts = ax4.pie(sizes, labels=['Occupied', 'Available'], 
                                          autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*total_spots)} spots)',
                                          colors=colors_overview, startangle=90)
        ax4.set_title(f'Overall System Status\nTotal: {total_spots} spots', fontweight='bold')
        
        plt.tight_layout(h_pad=3.0, w_pad=2.5, rect=[0.08, 0.08, 0.92, 0.88])  # Optimized spacing for smaller figure
        graph_data = generate_graph_base64(fig)
        
        return jsonify({
            'graph': graph_data, 
            'data': data,
            'summary': {
                'total_spots': int(total_spots),
                'total_occupied': int(total_occupied),
                'total_available': int(total_available),
                'overall_occupancy': round(total_occupied / total_spots * 100, 2) if total_spots > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating occupancy graph: {e}")
        return jsonify({'error': 'Failed to generate graph'}), 500

@app.route('/api/admin/graphs/revenue', methods=['GET'])
def generate_revenue_graph():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get revenue data for last 30 days
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as reservations,
                SUM(CASE WHEN parking_cost IS NOT NULL THEN parking_cost ELSE 0 END) as revenue
            FROM reservations 
            WHERE created_at >= date('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''')
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            # Generate sample data for demo
            dates = pd.date_range(start=datetime.now() - timedelta(days=29), 
                                end=datetime.now(), freq='D')
            data = []
            for date in dates:
                reservations = np.random.randint(5, 25)
                revenue = np.random.uniform(50, 300)
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'reservations': reservations,
                    'revenue': round(revenue, 2)
                })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Create figure with subplots - smaller size for better container fit
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(8, 6))
        fig.suptitle('Revenue Analytics Dashboard', fontsize=14, fontweight='bold', y=0.98)
        
        # 1. Daily revenue trend
        ax1.plot(df['date'], df['revenue'], marker='o', linewidth=2, 
                color='#4ECDC4', markersize=4)
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Revenue ($)')
        ax1.set_title('Daily Revenue Trend (Last 30 Days)', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Reservations vs Revenue scatter
        ax2.scatter(df['reservations'], df['revenue'], alpha=0.6, 
                   color='#FF6B6B', s=50)
        ax2.set_xlabel('Number of Reservations')
        ax2.set_ylabel('Revenue ($)')
        ax2.set_title('Reservations vs Revenue Correlation', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add trend line
        z = np.polyfit(df['reservations'], df['revenue'], 1)
        p = np.poly1d(z)
        ax2.plot(df['reservations'], p(df['reservations']), "r--", alpha=0.8)
        
        # 3. Weekly revenue comparison
        df['week'] = df['date'].dt.isocalendar().week
        weekly_revenue = df.groupby('week')['revenue'].sum().reset_index()
        
        bars = ax3.bar(range(len(weekly_revenue)), weekly_revenue['revenue'], 
                      color='#45B7D1', alpha=0.8)
        ax3.set_xlabel('Week')
        ax3.set_ylabel('Total Revenue ($)')
        ax3.set_title('Weekly Revenue Comparison', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, revenue in zip(bars, weekly_revenue['revenue']):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'${revenue:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # 4. Revenue distribution histogram
        ax4.hist(df['revenue'], bins=10, color='#96CEB4', alpha=0.7, edgecolor='black')
        ax4.set_xlabel('Revenue ($)')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Daily Revenue Distribution', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout(h_pad=3.0, w_pad=2.5, rect=[0.08, 0.08, 0.92, 0.88])  # Optimized spacing for smaller figure
        graph_data = generate_graph_base64(fig)
        
        total_revenue = df['revenue'].sum()
        avg_daily_revenue = df['revenue'].mean()
        
        return jsonify({
            'graph': graph_data,
            'data': data,
            'summary': {
                'total_revenue': round(total_revenue, 2),
                'avg_daily_revenue': round(avg_daily_revenue, 2),
                'total_reservations': int(df['reservations'].sum()),
                'avg_daily_reservations': round(df['reservations'].mean(), 1)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating revenue graph: {e}")
        return jsonify({'error': 'Failed to generate graph'}), 500

@app.route('/api/admin/graphs/usage', methods=['GET'])
def generate_usage_graph():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get hourly usage data
        cursor.execute('''
            SELECT 
                strftime('%H', created_at) as hour,
                COUNT(*) as reservations
            FROM reservations 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY strftime('%H', created_at)
            ORDER BY hour
        ''')
        hourly_data = cursor.fetchall()
        
        # Get user activity data
        cursor.execute('''
            SELECT 
                u.username,
                COUNT(r.id) as total_reservations
            FROM users u
            LEFT JOIN reservations r ON u.id = r.user_id
            WHERE u.is_admin = 0 AND r.created_at >= date('now', '-30 days')
            GROUP BY u.id
            ORDER BY total_reservations DESC
            LIMIT 10
        ''')
        user_data = cursor.fetchall()
        conn.close()
        
        # Generate sample data if no real data exists
        if not hourly_data:
            hourly_data = [{'hour': f'{i:02d}', 'reservations': np.random.randint(0, 15)} 
                          for i in range(24)]
        
        if not user_data:
            user_data = [{'username': f'User{i}', 'total_reservations': np.random.randint(1, 20)} 
                        for i in range(1, 11)]
        
        # Create figure - smaller size for better container fit
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(8, 6))
        fig.suptitle('Usage Analytics Dashboard', fontsize=14, fontweight='bold', y=0.98)
        
        # 1. Hourly usage pattern
        hours = [int(d['hour']) for d in hourly_data]
        reservations = [d['reservations'] for d in hourly_data]
        
        # Fill missing hours with 0
        hourly_reservations = [0] * 24
        for h, r in zip(hours, reservations):
            hourly_reservations[h] = r
        
        ax1.bar(range(24), hourly_reservations, color='#FF6B6B', alpha=0.7)
        ax1.set_xlabel('Hour of Day')
        ax1.set_ylabel('Number of Reservations')
        ax1.set_title('Hourly Usage Pattern', fontweight='bold')
        ax1.set_xticks(range(0, 24, 2))
        ax1.grid(True, alpha=0.3)
        
        # 2. Top users bar chart
        usernames = [d['username'][:8] for d in user_data[:8]]  # Truncate long names
        user_reservations = [d['total_reservations'] for d in user_data[:8]]
        
        bars = ax2.barh(usernames, user_reservations, color='#4ECDC4', alpha=0.8)
        ax2.set_xlabel('Total Reservations')
        ax2.set_title('Top Active Users (Last 30 Days)', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, count in zip(bars, user_reservations):
            width = bar.get_width()
            ax2.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{count}', ha='left', va='center', fontweight='bold')
        
        # 3. Peak hours analysis
        peak_hours = sorted(range(24), key=lambda x: hourly_reservations[x], reverse=True)[:6]
        peak_values = [hourly_reservations[h] for h in peak_hours]
        
        colors = ['#FF6B6B', '#FF8E53', '#FF8E53', '#4ECDC4', '#4ECDC4', '#4ECDC4']
        bars = ax3.bar([f'{h:02d}:00' for h in peak_hours], peak_values, 
                      color=colors, alpha=0.8)
        ax3.set_xlabel('Peak Hours')
        ax3.set_ylabel('Reservations')
        ax3.set_title('Top 6 Peak Hours', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, value in zip(bars, peak_values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{value}', ha='center', va='bottom', fontweight='bold')
        
        # 4. Usage summary text instead of heatmap
        ax4.axis('off')  # Turn off axis for text display
        
        # Calculate some summary statistics
        total_reservations = sum(hourly_reservations)
        avg_hourly = total_reservations / 24 if total_reservations > 0 else 0
        peak_hour_value = max(hourly_reservations) if hourly_reservations else 0
        peak_hour_idx = hourly_reservations.index(peak_hour_value) if peak_hour_value > 0 else 0
        
        summary_text = f"""
📊 Usage Summary

🔥 Peak Hour: {peak_hour_idx:02d}:00
   ({peak_hour_value} reservations)

📈 Total Daily: {total_reservations}
   reservations

⏰ Hourly Average: {avg_hourly:.1f}
   reservations

👥 Active Users: {len(user_data)}
   in last 30 days
        """
        
        ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout(h_pad=3.0, w_pad=2.5, rect=[0.08, 0.08, 0.92, 0.88])  # Optimized spacing for smaller figure
        graph_data = generate_graph_base64(fig)
        
        return jsonify({
            'graph': graph_data,
            'hourly_data': hourly_data,
            'user_data': user_data,
            'summary': {
                'peak_hour': f'{peak_hours[0]:02d}:00' if peak_hours else '12:00',
                'total_active_users': len(user_data),
                'avg_hourly_reservations': round(sum(hourly_reservations) / 24, 1)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating usage graph: {e}")
        return jsonify({'error': 'Failed to generate graph'}), 500

@app.route('/api/admin/reports/weekly', methods=['GET'])
def get_weekly_report():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get data for the last 7 days
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as reservations,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN parking_cost IS NOT NULL THEN parking_cost ELSE 0 END) as revenue
            FROM reservations 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''')
        daily_data = cursor.fetchall()
        
        # Hourly distribution for today
        cursor.execute('''
            SELECT 
                strftime('%H', created_at) as hour,
                COUNT(*) as reservations
            FROM reservations 
            WHERE date(created_at) = date('now')
            GROUP BY strftime('%H', created_at)
            ORDER BY hour
        ''')
        hourly_data = cursor.fetchall()
        
        # User activity patterns
        cursor.execute('''
            SELECT 
                u.username,
                COUNT(r.id) as total_reservations,
                SUM(CASE WHEN r.parking_cost IS NOT NULL THEN r.parking_cost ELSE 0 END) as total_spent,
                MAX(r.created_at) as last_reservation
            FROM users u
            LEFT JOIN reservations r ON u.id = r.user_id
            WHERE u.is_admin = 0 AND r.created_at >= date('now', '-7 days')
            GROUP BY u.id
            ORDER BY total_reservations DESC
            LIMIT 10
        ''')
        top_users = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'daily_data': daily_data,
            'hourly_data': hourly_data,
            'top_users': top_users
        }), 200
        
    except Exception as e:
        logger.error(f"Error in weekly report: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/reports/monthly', methods=['GET'])
def get_monthly_report():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Monthly trends for last 6 months
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as reservations,
                SUM(CASE WHEN parking_cost IS NOT NULL THEN parking_cost ELSE 0 END) as revenue,
                COUNT(DISTINCT user_id) as unique_users
            FROM reservations 
            WHERE created_at >= date('now', '-6 months')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month
        ''')
        monthly_trends = cursor.fetchall()
        
        # Lot performance
        cursor.execute('''
            SELECT 
                pl.prime_location_name,
                COUNT(r.id) as total_reservations,
                SUM(CASE WHEN r.parking_cost IS NOT NULL THEN r.parking_cost ELSE 0 END) as total_revenue,
                AVG(CASE WHEN r.parking_cost IS NOT NULL THEN r.parking_cost ELSE 0 END) as avg_revenue_per_reservation
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            LEFT JOIN reservations r ON ps.id = r.spot_id
            WHERE r.created_at >= date('now', '-1 month')
            GROUP BY pl.id
            ORDER BY total_revenue DESC
        ''')
        lot_performance = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'monthly_trends': monthly_trends,
            'lot_performance': lot_performance
        }), 200
        
    except Exception as e:
        logger.error(f"Error in monthly report: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/reports/daily-simple', methods=['GET'])
def get_daily_simple_report():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get today's data
        today = datetime.now().date()
        
        # Today's reservations
        cursor.execute('''
            SELECT 
                COUNT(*) as total_reservations_today,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_today,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_today,
                SUM(CASE WHEN parking_cost IS NOT NULL THEN parking_cost ELSE 0 END) as revenue_today
            FROM reservations 
            WHERE date(created_at) = date('now')
        ''')
        today_stats = cursor.fetchone()
        
        # This week's simple data (last 7 days available)
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as reservations
            FROM reservations 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        ''')
        available_days = cursor.fetchall()
        
        # Current reservation status
        cursor.execute('''
            SELECT 
                COUNT(*) as total_active_reservations,
                COUNT(DISTINCT user_id) as unique_active_users
            FROM reservations 
            WHERE status = 'active'
        ''')
        current_status = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'today': today_stats,
            'available_days': available_days,
            'current_status': current_status,
            'has_data': len(available_days) > 0 or today_stats['total_reservations_today'] > 0
        }), 200
        
    except Exception as e:
        logger.error(f"Error in daily simple report: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Test endpoint to check database connectivity
@app.route('/api/admin/test', methods=['GET'])
def admin_test():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Test database connectivity
        cursor.execute('SELECT COUNT(*) as count FROM parking_lots')
        lots_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as count FROM parking_spots')
        spots_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as count FROM users')
        users_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as count FROM reservations')
        reservations_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'Database connection successful',
            'counts': {
                'parking_lots': lots_count,
                'parking_spots': spots_count,
                'users': users_count,
                'reservations': reservations_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in admin_test: {e}")
        return jsonify({'error': str(e)}), 500

# Batch Job Management APIs
@app.route('/api/admin/batch-jobs', methods=['GET', 'POST'])
def batch_jobs():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT * FROM batch_jobs 
            ORDER BY created_at DESC 
            LIMIT 50
        ''')
        jobs = cursor.fetchall()
        conn.close()
        return jsonify({'jobs': jobs}), 200
    
    elif request.method == 'POST':
        try:
            data = request.json
            job_type = data.get('job_type')
            parameters = data.get('parameters', {})
            
            if not job_type:
                return jsonify({'error': 'Job type is required'}), 400
            
            # Start appropriate Celery task
            task = None
            if job_type == 'cleanup_expired':
                task = cleanup_expired_reservations.delay()
            elif job_type == 'daily_report':
                task = generate_daily_report.delay(parameters.get('date'))
            elif job_type == 'optimize_allocation':
                task = optimize_parking_allocation.delay()
            else:
                return jsonify({'error': 'Invalid job type'}), 400
            
            # Record job in database
            cursor.execute('''
                INSERT INTO batch_jobs (job_type, status, task_id, parameters)
                VALUES (?, 'running', ?, ?)
            ''', (job_type, task.id, json.dumps(parameters)))
            
            job_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({
                'message': 'Batch job started successfully',
                'job_id': job_id,
                'task_id': task.id
            }), 201
            
        except Exception as e:
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/admin/batch-jobs/<int:job_id>/status', methods=['GET'])
def batch_job_status(job_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM batch_jobs WHERE id = ?', (job_id,))
    job = cursor.fetchone()
    
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    
    # Check Celery task status if task is running
    if job['task_id'] and job['status'] == 'running':
        try:
            task = celery.AsyncResult(job['task_id'])
            if task.ready():
                if task.successful():
                    # Update job status
                    cursor.execute('''
                        UPDATE batch_jobs 
                        SET status = 'completed', result = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (json.dumps(task.result, default=str), job_id))
                    job['status'] = 'completed'
                    job['result'] = json.dumps(task.result, default=str)
                else:
                    # Task failed
                    cursor.execute('''
                        UPDATE batch_jobs 
                        SET status = 'failed', error_message = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (str(task.info), job_id))
                    job['status'] = 'failed'
                    job['error_message'] = str(task.info)
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error checking task status: {e}")
    
    conn.close()
    return jsonify({'job': job}), 200

# New API Endpoints for the added features
@app.route('/api/user/preferences', methods=['GET', 'POST'])
def user_preferences():
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify({'error': 'User access required'}), 403
    
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    user_id = session['user_id']
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
        prefs = cursor.fetchone()
        
        if not prefs:
            # Create default preferences
            cursor.execute('''
                INSERT INTO user_preferences (user_id, reminder_enabled, reminder_time, notification_method)
                VALUES (?, 1, '18:00', 'email')
            ''', (user_id,))
            conn.commit()
            
            cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
            prefs = cursor.fetchone()
        
        conn.close()
        return jsonify({'preferences': prefs}), 200
    
    elif request.method == 'POST':
        try:
            data = request.json
            reminder_enabled = data.get('reminder_enabled', 1)
            reminder_time = data.get('reminder_time', '18:00')
            notification_method = data.get('notification_method', 'email')
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (user_id, reminder_enabled, reminder_time, notification_method, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, reminder_enabled, reminder_time, notification_method))
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Preferences updated successfully'}), 200
            
        except Exception as e:
            conn.close()
            return jsonify({'error': str(e)}), 500

@app.route('/api/user/export-csv', methods=['POST'])
def request_csv_export():
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify({'error': 'User access required'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        user_id = session['user_id']
        
        # Check if there's already a pending export
        cursor.execute('''
            SELECT * FROM csv_export_jobs 
            WHERE user_id = ? AND status IN ('pending', 'processing')
        ''', (user_id,))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Export already in progress'}), 400
        
        # Create new export job
        cursor.execute('''
            INSERT INTO csv_export_jobs (user_id, status)
            VALUES (?, 'processing')
        ''', (user_id,))
        
        export_job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Start CSV export task
        task = export_user_parking_data_csv.delay(user_id)
        
        return jsonify({
            'message': 'CSV export started',
            'export_job_id': export_job_id,
            'task_id': task.id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/export-status/<int:export_job_id>', methods=['GET'])
def csv_export_status(export_job_id):
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify({'error': 'User access required'}), 403
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM csv_export_jobs 
            WHERE id = ? AND user_id = ?
        ''', (export_job_id, session['user_id']))
        
        export_job = cursor.fetchone()
        
        if not export_job:
            conn.close()
            return jsonify({'error': 'Export job not found'}), 404
        
        conn.close()
        return jsonify({'export_job': export_job}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/trigger-daily-reminders', methods=['POST'])
def trigger_daily_reminders():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        task = send_daily_reminders.delay()
        return jsonify({
            'message': 'Daily reminders task started',
            'task_id': task.id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/trigger-monthly-report', methods=['POST'])
def trigger_monthly_report():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.json
        user_id = data.get('user_id')
        month = data.get('month')
        year = data.get('year')
        
        task = generate_monthly_activity_report.delay(user_id, month, year)
        return jsonify({
            'message': 'Monthly report generation started',
            'task_id': task.id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Enhanced User APIs with caching
@app.route('/api/user/parking-lots', methods=['GET'])
def user_parking_lots():
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify({'error': 'User access required'}), 403
    
    @cached(timeout=CACHE_TIMEOUT, key_prefix='user')
    def get_user_parking_lots():
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                pl.*,
                COUNT(ps.id) as total_spots,
                SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            GROUP BY pl.id
            HAVING available_spots > 0
            ORDER BY pl.prime_location_name
        ''')
        
        lots = cursor.fetchall()
        conn.close()
        return lots
    
    lots = get_user_parking_lots()
    return jsonify({'parking_lots': lots}), 200

@app.route('/api/user/reserve-spot', methods=['POST'])
def user_reserve_spot():
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify({'error': 'User access required'}), 403
    
    try:
        data = request.json
        lot_id = data.get('lot_id')
        
        if not lot_id:
            return jsonify({'error': 'Lot ID is required'}), 400
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Check if user already has an active reservation
        cursor.execute('''
            SELECT r.id FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            WHERE r.user_id = ? AND r.status = 'active'
        ''', (session['user_id'],))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'You already have an active reservation'}), 400
        
        # Find first available spot in the lot
        cursor.execute('''
            SELECT id FROM parking_spots 
            WHERE lot_id = ? AND status = 'A' 
            ORDER BY spot_number LIMIT 1
        ''', (lot_id,))
        
        spot = cursor.fetchone()
        if not spot:
            conn.close()
            return jsonify({'error': 'No available spots in this parking lot'}), 400
        
        # Create reservation
        cursor.execute('''
            INSERT INTO reservations (spot_id, user_id, status)
            VALUES (?, ?, 'active')
        ''', (spot['id'], session['user_id']))
        
        reservation_id = cursor.lastrowid
        
        # Update spot status to occupied
        cursor.execute('UPDATE parking_spots SET status = "O" WHERE id = ?', (spot['id'],))
        
        conn.commit()
        
        # Get reservation details
        cursor.execute('''
            SELECT 
                r.*,
                ps.spot_number,
                pl.prime_location_name,
                pl.address,
                pl.price
            FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE r.id = ?
        ''', (reservation_id,))
        
        reservation = cursor.fetchone()
        conn.close()
        
        # Invalidate relevant caches
        invalidate_cache_pattern('*parking_lots*')
        invalidate_cache_pattern('*analytics*')
        
        return jsonify({
            'message': 'Spot reserved successfully',
            'reservation': reservation
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get daily report
@app.route('/api/admin/reports/daily/<date>', methods=['GET'])
def get_daily_report(date):
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Check if report exists in cache
        report_key = f"daily_report:{date}"
        cached_report = redis_client.get(report_key)
        
        if cached_report:
            return jsonify(json.loads(cached_report)), 200
        
        # Generate report if not cached
        task = generate_daily_report.delay(date)
        
        return jsonify({
            'message': 'Report generation started',
            'task_id': task.id,
            'status': 'generating'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get optimization recommendations
@app.route('/api/admin/optimization', methods=['GET'])
def get_optimization_recommendations():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Check cache first
        cached_recommendations = redis_client.get('parking_optimization')
        
        if cached_recommendations:
            return jsonify({
                'recommendations': json.loads(cached_recommendations),
                'cached': True
            }), 200
        
        # Start optimization task
        task = optimize_parking_allocation.delay()
        
        return jsonify({
            'message': 'Optimization analysis started',
            'task_id': task.id,
            'status': 'analyzing'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/park-vehicle', methods=['POST'])
def user_park_vehicle():
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify({'error': 'User access required'}), 403
    
    try:
        data = request.json
        reservation_id = data.get('reservation_id')
        
        if not reservation_id:
            return jsonify({'error': 'Reservation ID is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Update reservation with parking timestamp
        parking_time = datetime.now()
        cursor.execute('''
            UPDATE reservations 
            SET parking_timestamp = ? 
            WHERE id = ? AND user_id = ? AND status = 'active'
        ''', (parking_time, reservation_id, session['user_id']))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Invalid reservation or already parked'}), 400
        
        conn.commit()
        conn.close()
        
        # Invalidate user-specific caches
        invalidate_cache_pattern(f'*user:{session["user_id"]}*')
        
        return jsonify({
            'message': 'Vehicle parked successfully',
            'parking_timestamp': parking_time.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/release-spot', methods=['POST'])
def user_release_spot():
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify({'error': 'User access required'}), 403
    
    try:
        data = request.json
        reservation_id = data.get('reservation_id')
        
        if not reservation_id:
            return jsonify({'error': 'Reservation ID is required'}), 400
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Get reservation details
        cursor.execute('''
            SELECT 
                r.*,
                ps.spot_number,
                pl.price
            FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE r.id = ? AND r.user_id = ? AND r.status = 'active'
        ''', (reservation_id, session['user_id']))
        
        reservation = cursor.fetchone()
        if not reservation:
            conn.close()
            return jsonify({'error': 'Invalid reservation'}), 400
        
        if not reservation['parking_timestamp']:
            conn.close()
            return jsonify({'error': 'Vehicle not yet parked'}), 400
        
        # Calculate parking cost
        leaving_time = datetime.now()
        parking_start = datetime.fromisoformat(reservation['parking_timestamp'])
        duration_hours = max(1, (leaving_time - parking_start).total_seconds() / 3600)  # Minimum 1 hour
        parking_cost = duration_hours * reservation['price']
        
        # Update reservation
        cursor.execute('''
            UPDATE reservations 
            SET leaving_timestamp = ?, parking_cost = ?, status = 'completed'
            WHERE id = ?
        ''', (leaving_time, parking_cost, reservation_id))
        
        # Update spot status to available
        cursor.execute('UPDATE parking_spots SET status = "A" WHERE id = ?', (reservation['spot_id'],))
        
        conn.commit()
        conn.close()
        
        # Invalidate relevant caches
        invalidate_cache_pattern('*parking_lots*')
        invalidate_cache_pattern('*analytics*')
        invalidate_cache_pattern(f'*user:{session["user_id"]}*')
        
        return jsonify({
            'message': 'Spot released successfully',
            'leaving_timestamp': leaving_time.isoformat(),
            'parking_cost': round(parking_cost, 2),
            'duration_hours': round(duration_hours, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/my-reservations', methods=['GET'])
def user_reservations():
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify({'error': 'User access required'}), 403
    
    @cached(timeout=CACHE_TIMEOUT, key_prefix=f'user:{session["user_id"]}')
    def get_user_reservations():
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                r.*,
                ps.spot_number,
                pl.prime_location_name,
                pl.address,
                pl.price
            FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
        ''', (session['user_id'],))
        
        reservations = cursor.fetchall()
        conn.close()
        return reservations
    
    reservations = get_user_reservations()
    return jsonify({'reservations': reservations}), 200

@app.route('/api/user/analytics', methods=['GET'])
def user_analytics():
    if not session.get('user_id') or session.get('is_admin'):
        return jsonify({'error': 'User access required'}), 403
    
    @cached(timeout=ANALYTICS_CACHE_TIMEOUT, key_prefix=f'user:{session["user_id"]}')
    def get_user_analytics():
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        user_id = session['user_id']
        
        # Total reservations
        cursor.execute('SELECT COUNT(*) as total_reservations FROM reservations WHERE user_id = ?', (user_id,))
        total_reservations = cursor.fetchone()['total_reservations']
        
        # Active reservations
        cursor.execute('SELECT COUNT(*) as active_reservations FROM reservations WHERE user_id = ? AND status = "active"', (user_id,))
        active_reservations = cursor.fetchone()['active_reservations']
        
        # Total cost
        cursor.execute('SELECT SUM(parking_cost) as total_spent FROM reservations WHERE user_id = ? AND parking_cost IS NOT NULL', (user_id,))
        total_spent = cursor.fetchone()['total_spent'] or 0
        
        # Average parking duration
        cursor.execute('''
            SELECT AVG(
                CASE 
                    WHEN parking_timestamp IS NOT NULL AND leaving_timestamp IS NOT NULL 
                    THEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24
                    ELSE NULL 
                END
            ) as avg_duration_hours
            FROM reservations 
            WHERE user_id = ? AND status = 'completed'
        ''', (user_id,))
        avg_duration = cursor.fetchone()['avg_duration_hours'] or 0
        
        # Recent reservations for chart
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM reservations 
            WHERE user_id = ? AND created_at >= date('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (user_id,))
        recent_activity = cursor.fetchall()
        
        conn.close()
        
        return {
            'summary': {
                'total_reservations': total_reservations,
                'active_reservations': active_reservations,
                'completed_reservations': total_reservations - active_reservations,
                'total_spent': round(total_spent, 2),
                'average_duration_hours': round(avg_duration, 2)
            },
            'recent_activity': recent_activity
        }
    
    analytics_data = get_user_analytics()
    return jsonify(analytics_data), 200

# Cache management endpoints
@app.route('/api/admin/cache/stats', methods=['GET'])
def cache_stats():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        info = redis_client.info()
        return jsonify({
            'redis_info': {
                'version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'hit_rate': round(info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)) * 100, 2)
            }
        }), 200
    except redis.RedisError as e:
        return jsonify({'error': f'Redis connection error: {e}'}), 500

@app.route('/api/admin/cache/clear', methods=['POST'])
def clear_cache():
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        data = request.json
        pattern = data.get('pattern', '*')
        
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            return jsonify({
                'message': f'Cleared {len(keys)} cache keys matching pattern: {pattern}'
            }), 200
        else:
            return jsonify({
                'message': 'No cache keys found matching pattern'
            }), 200
            
    except redis.RedisError as e:
        return jsonify({'error': f'Redis error: {e}'}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {}
    }
    
    # Check database
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {e}'
        health_status['status'] = 'degraded'
    
    # Check Redis
    try:
        redis_client.ping()
        health_status['services']['redis'] = 'healthy'
    except Exception as e:
        health_status['services']['redis'] = f'unhealthy: {e}'
        health_status['status'] = 'degraded'
    
    # Check Celery
    try:
        inspect = celery.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status['services']['celery'] = 'healthy'
        else:
            health_status['services']['celery'] = 'no workers available'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['services']['celery'] = f'unhealthy: {e}'
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

# Scheduled task setup
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run cleanup every hour
    sender.add_periodic_task(3600.0, cleanup_expired_reservations.s(), name='cleanup expired reservations')
    
    # Generate daily report at midnight
    sender.add_periodic_task(
        86400.0,  # 24 hours
        generate_daily_report.s(),
        name='generate daily report'
    )
    
    # Run optimization analysis every 6 hours
    sender.add_periodic_task(21600.0, optimize_parking_allocation.s(), name='optimize parking allocation')
    
    # Send daily reminders every evening at 6 PM
    sender.add_periodic_task(
        crontab(hour=18, minute=0),
        send_daily_reminders.s(),
        name='send daily reminders'
    )
    
    # Generate monthly reports on the 1st of every month at 9 AM
    sender.add_periodic_task(
        crontab(day_of_month=1, hour=9, minute=0),
        generate_monthly_activity_report.s(),
        name='generate monthly activity reports'
    )

# New Analytics API Endpoints for Chart.js Integration
@app.route('/api/admin/analytics/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Get comprehensive dashboard data for Chart.js charts"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
        
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Occupancy data
        cursor.execute('''
            SELECT 
                pl.prime_location_name,
                pl.price,
                COUNT(ps.id) as total_spots,
                SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots,
                SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            GROUP BY pl.id
        ''')
        occupancy_data = cursor.fetchall()
        
        # Revenue data (last 30 days)
        cursor.execute('''
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as reservations,
                SUM(CASE WHEN parking_cost IS NOT NULL THEN parking_cost ELSE 0 END) as revenue
            FROM reservations 
            WHERE created_at >= date('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''')
        revenue_data = cursor.fetchall()
        
        # Hourly usage patterns
        cursor.execute('''
            SELECT 
                strftime('%H', created_at) as hour,
                COUNT(*) as reservations
            FROM reservations 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY strftime('%H', created_at)
            ORDER BY hour
        ''')
        hourly_usage = cursor.fetchall()
        
        # Top users
        cursor.execute('''
            SELECT 
                u.username,
                COUNT(r.id) as total_reservations,
                SUM(CASE WHEN r.parking_cost IS NOT NULL THEN r.parking_cost ELSE 0 END) as total_spent
            FROM users u
            LEFT JOIN reservations r ON u.id = r.user_id
            WHERE u.is_admin = 0 AND r.created_at >= date('now', '-30 days')
            GROUP BY u.id
            HAVING COUNT(r.id) > 0
            ORDER BY total_reservations DESC
            LIMIT 10
        ''')
        top_users = cursor.fetchall()
        
        # Monthly trends (last 12 months)
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as reservations,
                SUM(CASE WHEN parking_cost IS NOT NULL THEN parking_cost ELSE 0 END) as revenue
            FROM reservations 
            WHERE created_at >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month
        ''')
        monthly_trends = cursor.fetchall()
        
        # Parking duration analysis
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24 < 1 THEN 'Under 1 hour'
                    WHEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24 < 3 THEN '1-3 hours'
                    WHEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24 < 6 THEN '3-6 hours'
                    WHEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24 < 12 THEN '6-12 hours'
                    ELSE 'Over 12 hours'
                END as duration_category,
                COUNT(*) as count
            FROM reservations 
            WHERE parking_timestamp IS NOT NULL AND leaving_timestamp IS NOT NULL
            AND created_at >= date('now', '-30 days')
            GROUP BY duration_category
        ''')
        duration_analysis = cursor.fetchall()
        
        conn.close()
        
        # Generate sample data if no real data exists
        if not occupancy_data:
            occupancy_data = [
                {'prime_location_name': 'Main Campus', 'price': 5.0, 'total_spots': 50, 'occupied_spots': 30, 'available_spots': 20},
                {'prime_location_name': 'Library', 'price': 3.0, 'total_spots': 25, 'occupied_spots': 15, 'available_spots': 10},
                {'prime_location_name': 'Sports Center', 'price': 4.0, 'total_spots': 40, 'occupied_spots': 20, 'available_spots': 20},
                {'prime_location_name': 'Student Center', 'price': 6.0, 'total_spots': 35, 'occupied_spots': 25, 'available_spots': 10}
            ]
            
        if not revenue_data:
            dates = pd.date_range(start=datetime.now() - timedelta(days=29), end=datetime.now(), freq='D')
            revenue_data = [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'reservations': np.random.randint(5, 25),
                    'revenue': round(np.random.uniform(50, 300), 2)
                }
                for date in dates
            ]
            
        if not hourly_usage:
            hourly_usage = [{'hour': f'{i:02d}', 'reservations': np.random.randint(0, 15)} for i in range(24)]
            
        if not top_users:
            top_users = [
                {'username': f'user{i}', 'total_reservations': np.random.randint(5, 20), 'total_spent': round(np.random.uniform(50, 200), 2)}
                for i in range(1, 11)
            ]
            
        if not monthly_trends:
            months = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='M')
            monthly_trends = [
                {
                    'month': month.strftime('%Y-%m'),
                    'reservations': np.random.randint(50, 200),
                    'revenue': round(np.random.uniform(500, 2000), 2)
                }
                for month in months
            ]
            
        if not duration_analysis:
            duration_analysis = [
                {'duration_category': 'Under 1 hour', 'count': 45},
                {'duration_category': '1-3 hours', 'count': 120},
                {'duration_category': '3-6 hours', 'count': 85},
                {'duration_category': '6-12 hours', 'count': 30},
                {'duration_category': 'Over 12 hours', 'count': 15}
            ]
        
        return jsonify({
            'occupancy': occupancy_data,
            'revenue': revenue_data,
            'hourly_usage': hourly_usage,
            'top_users': top_users,
            'monthly_trends': monthly_trends,
            'duration_analysis': duration_analysis,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500

@app.route('/api/admin/analytics/export-csv', methods=['POST'])
def export_analytics_csv():
    """Export analytics data as CSV file"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Admin access required'}), 403
        
    try:
        data = request.get_json()
        export_type = data.get('type', 'all')  # all, occupancy, revenue, users, reservations
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        output = io.StringIO()
        
        if export_type in ['all', 'reservations']:
            # Export reservations data
            cursor.execute('''
                SELECT 
                    r.id,
                    u.username,
                    pl.prime_location_name,
                    ps.spot_number,
                    r.parking_timestamp,
                    r.leaving_timestamp,
                    r.parking_cost,
                    r.status,
                    r.created_at
                FROM reservations r
                JOIN users u ON r.user_id = u.id
                JOIN parking_spots ps ON r.spot_id = ps.id
                JOIN parking_lots pl ON ps.lot_id = pl.id
                ORDER BY r.created_at DESC
            ''')
            reservations = cursor.fetchall()
            
            if reservations:
                output.write("RESERVATIONS DATA\n")
                writer = csv.DictWriter(output, fieldnames=reservations[0].keys())
                writer.writeheader()
                writer.writerows(reservations)
                output.write("\n\n")
        
        if export_type in ['all', 'occupancy']:
            # Export occupancy data
            cursor.execute('''
                SELECT 
                    pl.prime_location_name,
                    pl.address,
                    pl.pin_code,
                    pl.price,
                    pl.maximum_number_of_spots,
                    COUNT(ps.id) as total_spots,
                    SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots,
                    SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots
                FROM parking_lots pl
                LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
                GROUP BY pl.id
            ''')
            occupancy = cursor.fetchall()
            
            if occupancy:
                output.write("OCCUPANCY DATA\n")
                writer = csv.DictWriter(output, fieldnames=occupancy[0].keys())
                writer.writeheader()
                writer.writerows(occupancy)
                output.write("\n\n")
        
        if export_type in ['all', 'users']:
            # Export users data
            cursor.execute('''
                SELECT 
                    u.username,
                    u.email,
                    u.phone,
                    u.created_at,
                    COUNT(r.id) as total_reservations,
                    SUM(CASE WHEN r.parking_cost IS NOT NULL THEN r.parking_cost ELSE 0 END) as total_spent
                FROM users u
                LEFT JOIN reservations r ON u.id = r.user_id
                WHERE u.is_admin = 0
                GROUP BY u.id
                ORDER BY total_reservations DESC
            ''')
            users = cursor.fetchall()
            
            if users:
                output.write("USERS DATA\n")
                writer = csv.DictWriter(output, fieldnames=users[0].keys())
                writer.writeheader()
                writer.writerows(users)
                output.write("\n\n")
        
        if export_type in ['all', 'revenue']:
            # Export daily revenue data
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as reservations,
                    SUM(CASE WHEN parking_cost IS NOT NULL THEN parking_cost ELSE 0 END) as revenue
                FROM reservations 
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 90
            ''')
            revenue = cursor.fetchall()
            
            if revenue:
                output.write("DAILY REVENUE DATA\n")
                writer = csv.DictWriter(output, fieldnames=revenue[0].keys())
                writer.writeheader()
                writer.writerows(revenue)
        
        conn.close()
        
        # Create response with CSV data
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"parking_analytics_{export_type}_{timestamp}.csv"
        
        return jsonify({
            'csv_data': csv_content,
            'filename': filename,
            'export_type': export_type,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'error': 'Failed to export CSV data'}), 500

# Initialize database when app starts
if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
    print("Admin credentials: username='admin', password='admin123'")
    print("\nRedis & Celery Features Added:")
    print("- Redis caching for improved performance")
    print("- Background task processing with Celery")
    print("- Periodic cleanup of expired reservations")
    print("- Daily report generation")
    print("- Parking optimization analysis")
    print("- Cache management endpoints")
    print("- Health check endpoint")
    print("\nNew Backend Jobs Added:")
    print("- Daily reminders via email/Google Chat")
    print("- Monthly activity reports via email")
    print("- CSV export for user parking data")
    print("\nNew API Endpoints:")
    print("Batch Jobs:")
    print("  GET/POST /api/admin/batch-jobs - Manage batch jobs")
    print("  GET /api/admin/batch-jobs/<id>/status - Check job status")
    print("Reports:")
    print("  GET /api/admin/reports/daily/<date> - Get daily report")
    print("  GET /api/admin/optimization - Get optimization recommendations")
    print("Cache Management:")
    print("  GET /api/admin/cache/stats - Redis statistics")
    print("  POST /api/admin/cache/clear - Clear cache")
    print("User Features:")
    print("  GET/POST /api/user/preferences - Manage notification preferences")
    print("  POST /api/user/export-csv - Request CSV export")
    print("  GET /api/user/export-status/<id> - Check export status")
    print("Admin Triggers:")
    print("  POST /api/admin/trigger-daily-reminders - Manually trigger reminders")
    print("  POST /api/admin/trigger-monthly-report - Manually trigger monthly reports")
    print("Health:")
    print("  GET /api/health - System health check")
    print("\nEnvironment Variables to Set:")
    print("  EMAIL_USERNAME - Your Gmail address")
    print("  EMAIL_PASSWORD - Your Gmail app password")
    print("  GOOGLE_CHAT_WEBHOOK - Google Chat webhook URL (optional)")
    print("\nTo start Celery worker:")
    print("celery -A main.celery worker --loglevel=info")
    print("\nTo start Celery beat (scheduler):")
    print("celery -A main.celery beat --loglevel=info")
    
    app.run(debug=True, host='0.0.0.0', port=5001)

