# IMPORTS AND DEPENDENCIES
import sqlite3
import hashlib
import json
import socket
import time
import subprocess
import csv
import io
import os
import base64
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps

# Third-party Library Imports
import redis
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Flask and Extensions
from flask import Flask, request, jsonify, session
from flask_cors import CORS

# Celery for Background Tasks
from celery import Celery
from celery.schedules import crontab

# Data Visualization and Analysis
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from io import BytesIO


# LOGGING CONFIGURATION
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# FLASK APPLICATION SETUP
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'http://localhost:3000'])
app.secret_key = 'parking_lot_secret_key_2024'

# Security Headers Middleware
@app.after_request
def after_request(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:;"
    
    # Remove server header for security
    response.headers.pop('Server', None)
    
    return response

#JWT Configuration
JWT_SECRET_KEY = 'parkmate_jwt_secret_key_2024_very_secure_key_change_in_production'
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

#JWT Blacklist for logout functionality
JWT_BLACKLIST = set()

def add_token_to_blacklist(jti):
    """Add token JTI to blacklist"""
    JWT_BLACKLIST.add(jti)

def is_token_blacklisted(jti):
    """Check if token is blacklisted"""
    return jti in JWT_BLACKLIST

#CONFIGURATION SETTINGS,  Email Configuration for MailHog
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_USERNAME = 'admin@parkmate.com'
EMAIL_PASSWORD = ''
EMAIL_FROM = 'admin@parkmate.com'

# Google Chat Webhook Configuration
GOOGLE_CHAT_WEBHOOK = os.environ.get('GOOGLE_CHAT_WEBHOOK')

# Cache Configuration
CACHE_TIMEOUT = 300 
ANALYTICS_CACHE_TIMEOUT = 900

#Rate Limiting Configuration
LOGIN_RATE_LIMIT = 5  # Max 5 attempts per minute
REGISTER_RATE_LIMIT = 3  # Max 3 registrations per minute

def rate_limit_key(endpoint, identifier):
    """Generate rate limit key"""
    return f"rate_limit:{endpoint}:{identifier}"

def check_rate_limit(endpoint, identifier, limit_per_minute):
    """Check if request is within rate limit"""
    try:
        key = rate_limit_key(endpoint, identifier)
        current_count = redis_client.get(key)
        
        if current_count is None:

            redis_client.setex(key, 60, 1) 
            return True
        
        if int(current_count) >= limit_per_minute:
            return False
        
        redis_client.incr(key)
        return True
        
    except redis.RedisError as e:
        logger.warning(f"Rate limiting error: {e}")
        return True 

def rate_limited(limit_per_minute):
    """Decorator for rate limiting endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr or 'unknown'
            endpoint = f.__name__
            
            if not check_rate_limit(endpoint, identifier, limit_per_minute):
                return jsonify({
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': 60
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# REDIS CONFIGURATION
redis_client = redis.Redis(
    host='localhost', 
    port=6379, 
    db=0, 
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)
# CELERY CONFIGURATION
def make_celery(app):
    """Create and configure Celery instance"""
    celery = Celery(
        app.import_name,
        backend='redis://localhost:6379/1',
        broker='redis://localhost:6379/2'
    )
    celery.conf.update(app.config)
    
    celery.conf.beat_schedule = {
        'cleanup-expired-reservations': {
            'task': 'main.cleanup_expired_reservations',
            'schedule': 20.0,  
        },
        'generate-daily-report': {
            'task': 'main.generate_daily_report',
            'schedule': 20.0,  
        },
        'optimize-parking-allocation': {
            'task': 'main.optimize_parking_allocation',
            'schedule': 20.0,  
        },
        'send-parking-reminders': {
            'task': 'main.send_parking_reminders',
            'schedule': 20.0,  
        },
        'daily-mail-reminder-test': {
            'task': 'main.send_daily_reminders',
            'schedule': 20.0, 
        },
        'daily-mail-reminder': {
            'task': 'main.send_daily_reminders',
            'schedule': crontab(minute=0, hour=18)  
        },
        'monthly-mail-report-test': {
            'task': 'main.generate_monthly_activity_report',
            'schedule': 20.0, 
        },
        'monthly-mail-report': {
            'task': 'main.generate_monthly_activity_report',
            'schedule': crontab(minute=0, hour=0, day_of_month=1)  
        },
        'daily-test-reminder': {
            'task': 'main.send_test_daily_reminders',
            'schedule': 20.0,  
        }
    }
    celery.conf.timezone = 'Asia/Kolkata'    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)    
    celery.Task = ContextTask
    return celery
celery = make_celery(app)

# CACHE MANAGEMENT UTILITIES
def cache_key(*args):
    """Generate cache key from arguments"""
    return ':'.join(str(arg) for arg in args)

def cached(timeout=CACHE_TIMEOUT, key_prefix=''):
    """Decorator for caching function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key_name = f"{key_prefix}:{f.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            try:
                cached_result = redis_client.get(cache_key_name)
                if cached_result:
                    logger.info(f"Cache hit for {cache_key_name}")
                    return json.loads(cached_result)
            except redis.RedisError as e:
                logger.warning(f"Redis cache read error: {e}")
            
            result = f(*args, **kwargs)
            
            try:
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

def robust_cache_invalidation():
    """More comprehensive cache invalidation"""
    try:
        patterns_to_clear = [
            '*parking_lots*',
            '*user*',
            '*admin*',
            '*analytics*',
            '*reservations*'
        ]       
        total_cleared = 0
        for pattern in patterns_to_clear:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                total_cleared += len(keys)
                logger.info(f"Cleared {len(keys)} keys matching {pattern}")
        
        logger.info(f"Total cache keys cleared: {total_cleared}")
        return total_cleared
    except redis.RedisError as e:
        logger.warning(f"Cache invalidation error: {e}")
        return 0

# DATABASE INITIALIZATION AND UTILITIES
def init_db():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect('parking_lot.db')
    cursor = conn.cursor()
    # Users table
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
    # Parking Lots table
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
    # Parking Spots table
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
    # Reservations table
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
    # Batch Jobs table for tracking background tasks
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
    # User Preferences table for reminder settings
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
    # CSV Export Jobs table
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
    # Parking Reminders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reservation_id) REFERENCES reservations (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Payment Transactions table for payment gateway
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            payment_details TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_id TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (reservation_id) REFERENCES reservations (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create default admin user
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, email, is_admin) 
        VALUES (?, ?, ?, ?)
    ''', ('admin', admin_password, 'admin@parkinglot.com', 1))
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    return sqlite3.connect('parking_lot.db')

def hash_password(password):
    """Hash password using bcrypt (more secure than SHA256)"""
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except:
        return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password

def generate_tokens(user_data):
    """Generate JWT access and refresh tokens"""
    try:
        import uuid
        
        #generates unique JTI (JWT ID) for tken blacklisting
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())
  
        access_payload = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'is_admin': user_data['is_admin'],
            'exp': datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES,
            'iat': datetime.utcnow(),
            'jti': access_jti,
            'type': 'access'
        }
        
        # refreshess token payload
        refresh_payload = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'exp': datetime.utcnow() + JWT_REFRESH_TOKEN_EXPIRES,
            'iat': datetime.utcnow(),
            'jti': refresh_jti,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': int(JWT_ACCESS_TOKEN_EXPIRES.total_seconds()),
            'token_type': 'Bearer'
        }
    except Exception as e:
        logger.error(f"Error generating tokens: {e}")
        return None

def verify_token(token, token_type='access'):
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Check if token type matches
        if payload.get('type') != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None
        
        #Check if token is blacklisted
        jti = payload.get('jti')
        if jti and is_token_blacklisted(jti):
            logger.warning(f"Blacklisted token attempt: {jti}")
            return None
        
        # Checks expiration manually for better error handling
        exp = payload.get('exp')
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token has expired")
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None

# Authentication Decorators
def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1] 
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        # Fallback to session-based auth if no token
        if not token:
            if not session.get('user_id'):
                return jsonify({'error': 'Authentication required'}), 401
            #Creates user data from session
            request.current_user = {
                'user_id': session.get('user_id'),
                'is_admin': session.get('is_admin', False)
            }
            return f(*args, **kwargs)
        
        # Verifiess token
        user_data = verify_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            # Session-based check
            if not session.get('user_id'):
                return jsonify({'error': 'Authentication required'}), 401
            if not session.get('is_admin'):
                return jsonify({'error': 'Admin access required'}), 403
            request.current_user = {
                'user_id': session.get('user_id'),
                'is_admin': True
            }
            return f(*args, **kwargs)
        
        # Token-based check
        user_data = verify_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        if not user_data.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated

def user_required(f):
    """Decorator to require regular user privileges (non-admin)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
           
            if not session.get('user_id'):
                return jsonify({'error': 'Authentication required'}), 401
            if session.get('is_admin'):
                return jsonify({'error': 'User access only'}), 403
            request.current_user = {
                'user_id': session.get('user_id'),
                'is_admin': False
            }
            return f(*args, **kwargs)
        
        user_data = verify_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        if user_data.get('is_admin'):
            return jsonify({'error': 'User access only'}), 403
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated

def login_required(f):
    """Decorator to require authentication (allows both users and admins)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
           
            if not session.get('user_id'):
                return jsonify({'error': 'Authentication required'}), 401
            request.current_user = {
                'user_id': session.get('user_id'),
                'is_admin': session.get('is_admin', False)
            }

            return f(*args, **kwargs)
        
        user_data = verify_token(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated

def dict_factory(cursor, row):
    """Convert sqlite row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def ensure_database_consistency():
    """Ensure database consistency after operations"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM reservations 
            WHERE user_id NOT IN (SELECT id FROM users)
        """)
        orphaned_count = cursor.rowcount
        
        cursor.execute("""
            UPDATE parking_spots 
            SET status = 'A' 
            WHERE status = 'O' 
            AND id NOT IN (
                SELECT spot_id FROM reservations WHERE status = 'active'
            )
        """)
        freed_spots = cursor.rowcount
        
        cursor.execute("""
            UPDATE parking_spots 
            SET status = 'O' 
            WHERE status = 'A' 
            AND id IN (
                SELECT spot_id FROM reservations WHERE status = 'active'
            )
        """)
        occupied_spots = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if orphaned_count > 0 or freed_spots > 0 or occupied_spots > 0:
            logger.info(f"Database consistency check: {orphaned_count} orphaned reservations, {freed_spots} spots freed, {occupied_spots} spots marked occupied")
        
        return True
    except Exception as e:
        logger.error(f"Database consistency check failed: {e}")
        return False

# EMAIL AND NOTIFICATION UTILITIES
def check_mailhog_status():
    """Check if MailHog is running and accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((EMAIL_HOST, EMAIL_PORT))
        sock.close()
        return result == 0
    except Exception:
        return False

def ensure_mailhog_running():
    """Ensure MailHog is running, attempt to start it if not"""
    if check_mailhog_status():
        logger.info("MailHog is already running")
        return True
    logger.warning("MailHog not running, attempting to start...")
    try:
        mailhog_path = os.path.join(os.getcwd(), 'mailhog')
        if not os.path.exists(mailhog_path):
            logger.error(f"MailHog executable not found at: {mailhog_path}")
            return False
        logger.info(f"Starting MailHog from: {mailhog_path}")
        
        cmd = [
            mailhog_path,
            '-smtp-bind-addr', f'127.0.0.1:{EMAIL_PORT}',
            '-ui-bind-addr', '127.0.0.1:8025',
            '-api-bind-addr', '127.0.0.1:8025'
        ]
        
        logger.info(f"MailHog command: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.getcwd()
        )
        logger.info(f"MailHog process started with PID: {process.pid}")
        
        max_wait = 10
        for i in range(max_wait):
            time.sleep(1)
            if check_mailhog_status():
                logger.info(f"MailHog started successfully after {i+1} seconds")
                return True
            logger.info(f"Waiting for MailHog to start... ({i+1}/{max_wait})")
        
        logger.error(f"MailHog failed to start within {max_wait} seconds")
        return False
            
    except Exception as e:
        logger.error(f"Error starting MailHog: {e}")
        return False

def send_email(to_email, subject, body, attachment=None, retry_count=3):
    """Enhanced email sending function with auto-start capability and retry logic"""
    if not ensure_mailhog_running():
        logger.error("Cannot send email - MailHog is not running and could not be started")
        return False
    
    for attempt in range(retry_count):
        try:
            if not check_mailhog_status():
                logger.warning(f"MailHog not accessible on attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    ensure_mailhog_running()
                    time.sleep(2)
                    continue
                else:
                    logger.error("MailHog server is not accessible after all attempts")
                    return False
            
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
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
            
        except ConnectionRefusedError as e:
            logger.warning(f"Connection refused on attempt {attempt + 1}/{retry_count}: {e}")
            if attempt < retry_count - 1:
                ensure_mailhog_running()
                time.sleep(3)
                continue
            else:
                logger.error(f"Failed to send email after {retry_count} attempts - Connection refused")
                return False
                
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error on attempt {attempt + 1}: {e}")
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
            else:
                logger.error(f"Failed to send email after {retry_count} attempts - SMTP error")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
            else:
                logger.error(f"Failed to send email after {retry_count} attempts - Unexpected error")
                return False
    
    return False

def send_google_chat_message(message):
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

# GRAPH GENERATION UTILITIES
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

# CELERY BACKGROUND TASKS
@celery.task(bind=True)
def cleanup_expired_reservations(self):
    try:
        conn = get_db()
        cursor = conn.cursor()
        expiry_time = datetime.now() - timedelta(hours=24)
        cursor.execute('''
            SELECT r.id, r.spot_id FROM reservations r
            WHERE r.status = 'active' 
            AND r.parking_timestamp IS NULL 
            AND r.created_at < ?
        ''', (expiry_time,))
        
        expired_reservations = cursor.fetchall()
        
        if expired_reservations:
            reservation_ids = [r[0] for r in expired_reservations]
            spot_ids = [r[1] for r in expired_reservations]
            cursor.executemany(
                'UPDATE reservations SET status = "expired" WHERE id = ?',
                [(rid,) for rid in reservation_ids]
            )
            cursor.executemany(
                'UPDATE parking_spots SET status = "A" WHERE id = ?',
                [(sid,) for sid in spot_ids]
            )
            
            conn.commit()
            
            invalidate_cache_pattern('*parking_lots*')
            invalidate_cache_pattern('*analytics*')
            logger.info(f"Cleaned up {len(expired_reservations)} expired reservations")            
        conn.close()
        return f"Cleaned up {len(expired_reservations)} expired reservations"
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_reservations: {e}")
        raise

@celery.task(bind=True)
def generate_daily_report(self, date_str=None): #parking
    try:
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
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
        report_key = f"daily_report:{date_str}"
        redis_client.setex(report_key, 86400, json.dumps(report, default=str))
        
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
        
        redis_client.setex('parking_optimization', 3600, json.dumps(recommendations, default=str))
        
        conn.close()
        logger.info(f"Generated {len(recommendations)} optimization recommendations")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error in parking optimization: {e}")
        raise

@celery.task(bind=True)
def send_daily_reminders(self):
    try:
        logger.info("🔄 Starting daily reminder job...")
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        # Fetch users who have opted in for reminders
        cursor.execute('''
            SELECT 
                u.id, u.username, u.email, u.phone,
                up.reminder_enabled, up.notification_method,
                up.reminder_time
            FROM users u
            LEFT JOIN user_preferences up ON u.id = up.user_id
            WHERE u.is_admin = 0 AND u.email IS NOT NULL AND u.email != ''
            AND (up.reminder_enabled = 1 OR up.reminder_enabled IS NULL)
        ''')
        users = cursor.fetchall()
        seven_days_ago = datetime.now() - timedelta(days=7)
        inactive_users = []
        sent_count = 0
        
        # Find users who haven'ot made reservations in the last 7 days
        for user in users:
            cursor.execute('''
                SELECT COUNT(*) as recent_count
                FROM reservations 
                WHERE user_id = ? AND created_at >= ?
            ''', (user['id'], seven_days_ago))
            
            recent_reservations = cursor.fetchone()['recent_count']
            
            if recent_reservations == 0:
                inactive_users.append(user)
        
        # Ftesting: if no inactive users
        if len(inactive_users) == 0 and len(users) > 0:
            inactive_users = users[:3]  # Take first 3 users for testing
            logger.info(f"No inactive users found, using first {len(inactive_users)} users for testing")
        
        # gets available parking lots
        cursor.execute('''
            SELECT 
                pl.id, pl.prime_location_name as location_name, 
                pl.address, pl.price, pl.maximum_number_of_spots,
                COUNT(CASE WHEN ps.status = 'A' THEN 1 END) as available_slots
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            GROUP BY pl.id, pl.prime_location_name, pl.address, pl.price, pl.maximum_number_of_spots
            HAVING available_slots > 0
            ORDER BY available_slots DESC
            LIMIT 5
        ''')
        
        available_lots = cursor.fetchall()
        
        # Send reminders to inactive users
        for user in inactive_users:
            subject = "Parking Reminder - Book Your Spot Today! 🚗"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🚗 Parking Reminder</h1>
                    </div>
                    
                    <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                        <h2 style="color: #667eea; margin-top: 0;">Hello {user['username']}!</h2>
                        
                        <p>We noticed you haven't booked a parking spot recently. Don't miss out on securing your parking space!</p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #495057; margin-top: 0;">🅿️ Available Parking Lots</h3>
            """
            
            for i, lot in enumerate(available_lots[:3]):  # Show top 3 lots
                body += f"""
                            <div style="border-left: 4px solid #667eea; padding-left: 15px; margin: 15px 0;">
                                <h4 style="margin: 0; color: #333;">{lot['location_name']}</h4>
                                <p style="margin: 5px 0; color: #666;"><strong>📍 Address:</strong> {lot['address']}</p>
                                <p style="margin: 5px 0; color: #666;"><strong>💰 Price:</strong> ${lot['price']}/hour</p>
                                <p style="margin: 5px 0; color: #666;"><strong>🚗 Available Spots:</strong> {lot['available_slots']}/{lot['maximum_number_of_spots']}</p>
                            </div>
                """
            
            body += """
                        </div>
                        
                        <div style="background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #0c5460; margin-top: 0;">📅 Quick Booking Tips</h3>
                            <ul style="color: #0c5460;">
                                <li>Book in advance to guarantee your spot</li>
                                <li>Check availability during peak hours</li>
                                <li>Save time with our quick booking feature</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <p style="font-size: 16px; color: #667eea; font-weight: bold;">Book your parking spot now to secure your place!</p>
                            <p style="color: #6c757d; font-size: 14px;">
                                Best regards,<br>
                                <strong>Parking Management Team</strong>
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            if send_email(user['email'], subject, body):
                sent_count += 1
                logger.info(f"Sent reminder email to {user['username']} ({user['email']})")
        
        active_users = [user for user in users if user not in inactive_users]
        
        # For testing: if we have fewer than 2 active users
        if len(active_users) < 2 and len(users) > len(inactive_users):
            active_users = users[len(inactive_users):len(inactive_users)+2]  # Take next 2 users
            logger.info(f"Using {len(active_users)} users for active user notifications")
        
        for user in active_users[:5]:  # Limit to 5 active users to avoid spam
            # Check if they have active reservations today
            cursor.execute('''
                SELECT COUNT(*) as today_count
                FROM reservations 
                WHERE user_id = ? AND DATE(created_at) = DATE('now')
            ''', (user['id'],))
            
            today_bookings = cursor.fetchone()['today_count']
            
            # only to users who haven't booked today, if today_bookings == 0 and available_lots:
            if available_lots:  # for testing
                subject = "New Parking Opportunities Available! 🅿️"
                
                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 28px;">🅿️ Great Parking Options</h1>
                        </div>
                        
                        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                            <h2 style="color: #56ab2f; margin-top: 0;">Hello {user['username']}!</h2>
                            
                            <p>Great news! We have excellent parking lots available with plenty of spots:</p>
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                <h3 style="color: #495057; margin-top: 0;">🏢 Available Locations</h3>
                """
                
                for lot in available_lots[:2]:
                    body += f"""
                                <div style="border-left: 4px solid #56ab2f; padding-left: 15px; margin: 15px 0;">
                                    <h4 style="margin: 0; color: #333;">{lot['location_name']}</h4>
                                    <p style="margin: 5px 0; color: #666;"><strong>📍 Address:</strong> {lot['address']}</p>
                                    <p style="margin: 5px 0; color: #666;"><strong>💰 Price:</strong> ${lot['price']}/hour</p>
                                    <p style="margin: 5px 0; color: #666;"><strong>🚗 Available Now:</strong> {lot['available_slots']} spots</p>
                                </div>
                    """
                
                body += """
                            </div>
                            
                            <div style="text-align: center; margin-top: 30px;">
                                <p style="font-size: 16px; color: #56ab2f; font-weight: bold;">Check out these locations and book your spot today!</p>
                                <p style="color: #6c757d; font-size: 14px;">
                                    Best regards,<br>
                                    <strong>Parking Management Team</strong>
                                </p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                if send_email(user['email'], subject, body):
                    sent_count += 1
                    logger.info(f"Sent availability notification to {user['username']} ({user['email']})")
        
        conn.close()
        logger.info(f"✅ Daily reminder job completed. Sent {sent_count} emails.")
        return f"Sent {sent_count} reminder emails successfully"
        
    except Exception as e:
        logger.error(f"❌ Daily reminder job failed: {str(e)}")
        raise

@celery.task(bind=True)
def send_test_daily_reminders(self):
    """Test version - sends daily reminders to first 3 users regardless of conditions"""
    try:
        logger.info("🔄 Starting TEST daily reminder job...")
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        #first 3 users with email addresses
        cursor.execute('''
            SELECT id, username, email
            FROM users u
            WHERE u.is_admin = 0 AND u.email IS NOT NULL AND u.email != ''
            LIMIT 3
        ''')
        
        users = cursor.fetchall()
        sent_count = 0
        
        logger.info(f"Found {len(users)} users for testing")
        
        for user in users:
            subject = "🔔 TEST Daily Parking Reminder!"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">🔔 TEST Reminder</h1>
                    </div>
                    
                    <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                        <h2 style="color: #ff6b35; margin-top: 0;">Hello {user['username']}! 👋</h2>
                        
                        <p><strong>This is a TEST email to verify the scheduled email system is working!</strong></p>
                        
                        <div style="background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #0c5460; margin-top: 0;">✅ System Status</h3>
                            <ul style="color: #0c5460;">
                                <li>Celery Beat Scheduler: ✅ Running</li>
                                <li>Email System: ✅ Working</li>
                                <li>Database: ✅ Connected</li>
                                <li>MailHog: ✅ Receiving</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <p style="font-size: 14px; color: #666;">
                                Test sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                                <strong>Parking Management System</strong>
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            if send_email(user['email'], subject, body):
                sent_count += 1
                logger.info(f"✅ Sent TEST email to {user['username']} ({user['email']})")
            else:
                logger.error(f"❌ Failed to send TEST email to {user['username']} ({user['email']})")
        
        conn.close()
        logger.info(f"🎉 TEST daily reminder completed. Sent {sent_count} emails.")
        return f"TEST: Sent {sent_count} reminder emails successfully"
        
    except Exception as e:
        logger.error(f"❌ TEST daily reminder failed: {str(e)}")
        raise

@celery.task(bind=True)
def generate_monthly_activity_report(self, user_id=None, month=None, year=None):
    """Generate monthly activity report for user(s)"""
    try:
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
        
        logger.info(f"🔄 Starting monthly report generation for {month}/{year}")
            
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        #getting users with email addresses
        if user_id:
            cursor.execute('SELECT * FROM users WHERE id = ? AND is_admin = 0 AND email IS NOT NULL AND email != ""', (user_id,))
            users = cursor.fetchall()
        else:
            cursor.execute('SELECT * FROM users WHERE is_admin = 0 AND email IS NOT NULL AND email != ""')
            users = cursor.fetchall()
        
        reports_generated = 0
        
        logger.info(f"Found {len(users)} users to generate reports for")
        
        for user in users:
            try:
                #genrating monthly statistics
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
                
                #skips users with no activity this month
                if not monthly_stats or monthly_stats['total_bookings'] == 0:
                    logger.info(f"Skipping {user['username']} - no activity this month")
                    continue
                
                #show most used parking lot
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
                
                #shows daily usage pattern
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
                
                #create enhanced HTML report
                html_report = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Monthly Parking Activity Report</title>
                    <style>
                        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
                        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                        .header h1 {{ margin: 0; font-size: 28px; }}
                        .content {{ padding: 30px; }}
                        .stat-box {{ background: linear-gradient(135deg, #e8f4f8 0%, #f0f8ff 100%); padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
                        .stat-box h2 {{ color: #333; margin-top: 0; font-size: 20px; }}
                        .stat-item {{ display: inline-block; margin: 10px 20px 10px 0; }}
                        .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; display: block; }}
                        .stat-label {{ color: #666; font-size: 14px; }}
                        .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                        .table th {{ background-color: #667eea; color: white; font-weight: bold; }}
                        .table tr:nth-child(even) {{ background-color: #f9f9f9; }}
                        .highlight {{ background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); padding: 15px; border-radius: 8px; margin: 20px 0; }}
                        .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>📊 Monthly Parking Report</h1>
                            <p style="margin: 10px 0 0 0; font-size: 18px;">ParkMate Activity Summary</p>
                        </div>
                        
                        <div class="content">
                            <div style="text-align: center; margin-bottom: 30px;">
                                <h2 style="color: #333; margin: 0;">Hello {user['username']}! 👋</h2>
                                <p style="color: #666; margin: 5px 0;"><strong>Report Period:</strong> {month}/{year}</p>
                                <p style="color: #666; margin: 5px 0;"><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            </div>
                            
                            <div class="stat-box">
                                <h2>📈 Monthly Summary</h2>
                                <div style="display: flex; flex-wrap: wrap;">
                                    <div class="stat-item">
                                        <span class="stat-value">{monthly_stats['total_bookings'] if monthly_stats else 0}</span>
                                        <span class="stat-label">Total Bookings</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-value">{monthly_stats['completed_bookings'] if monthly_stats else 0}</span>
                                        <span class="stat-label">Completed Sessions</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-value">${"{:.2f}".format(monthly_stats['total_spent']) if monthly_stats and monthly_stats.get('total_spent') else '0.00'}</span>
                                        <span class="stat-label">Total Spent</span>
                                    </div>
                                    <div class="stat-item">
                                        <span class="stat-value">{f"{monthly_stats['avg_duration_hours']:.1f}h" if monthly_stats and monthly_stats.get('avg_duration_hours') is not None else 'N/A'}</span>
                                        <span class="stat-label">Avg. Duration</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="stat-box">
                                <h2>🏢 Favorite Location</h2>
                                <p style="font-size: 18px; margin: 10px 0;"><strong>{most_used_lot['prime_location_name'] if most_used_lot else 'No specific preference'}</strong></p>
                                <p style="color: #666;">Usage: {most_used_lot['usage_count'] if most_used_lot else 0} times this month</p>
                            </div>
                            
                            <div class="stat-box">
                                <h2>📅 Daily Activity Pattern</h2>
                                <table class="table">
                                    <thead>
                                        <tr><th>Date</th><th>Bookings Made</th></tr>
                                    </thead>
                                    <tbody>
                """
                
                for day in daily_usage:
                    html_report += f"<tr><td>{day['date']}</td><td>{day['bookings']}</td></tr>"
                
                html_report += """
                                    </tbody>
                                </table>
                            </div>
                            
                            <div class="highlight">
                                <h2 style="margin-top: 0;">💡 Tips for Next Month</h2>
                                <ul style="margin: 10px 0;">
                                    <li>📅 <strong>Plan ahead:</strong> Book parking spots in advance to ensure availability</li>
                                    <li>⏰ <strong>Off-peak savings:</strong> Consider booking during off-peak hours for better rates</li>
                                    <li>🎫 <strong>Monthly passes:</strong> Ask about monthly parking passes for regular users</li>
                                    <li>📱 <strong>Mobile app:</strong> Use our app for quick and easy booking</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="footer">
                            <p><strong>Thank you for using ParkMate!</strong></p>
                            <p>Questions? Contact us at admin@parkmate.com</p>
                            <p style="font-size: 12px; margin-top: 15px;">This is an automated report from ParkMate Parking Management System</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # Send the email
                if send_email(
                    user['email'], 
                    f"📊 Your Monthly Parking Report - {month}/{year}",
                    html_report
                ):
                    reports_generated += 1
                    logger.info(f"Successfully sent monthly report to {user['username']} ({user['email']})")
                else:
                    logger.warning(f"Failed to send monthly report to {user['username']} ({user['email']})")
                    
            except Exception as e:
                logger.error(f"Error generating report for user {user['username']}: {e}")
                continue
        
        conn.close()
        logger.info(f"✅ Monthly report generation completed. Generated {reports_generated} reports for {month}/{year}")
        return f"Generated {reports_generated} monthly reports for {month}/{year}"
        
    except Exception as e:
        logger.error(f"❌ Error generating monthly reports: {e}")
        raise

@celery.task(bind=True)
def export_user_parking_data_csv(self, user_id):
    """Export user's parking data to CSV format"""
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
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
        
        filename = f"parking_data_{user['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join('exports', filename)
        
        os.makedirs('exports', exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            f.write(csv_content)
        
        cursor.execute('''
            UPDATE csv_export_jobs 
            SET status = 'completed', file_path = ?, completed_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'processing'
        ''', (filepath, user_id))
        
        conn.commit()
        
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

@celery.task(bind=True)
def send_parking_reminders(self):
    """Send reminders to users who have reserved but not parked"""
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        #finds reservationms that are active but user hasn't parked yet, send reminder after 30 minutes of boking
        reminder_time = datetime.now() - timedelta(minutes=30)
        
        cursor.execute('''
            SELECT 
                r.id as reservation_id,
                r.created_at,
                r.user_id,
                u.username,
                u.email,
                ps.spot_number,
                pl.prime_location_name,
                pl.address,
                pl.price
            FROM reservations r
            JOIN users u ON r.user_id = u.id
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE r.status = 'active' 
                AND r.parking_timestamp IS NULL 
                AND r.created_at < ?
                AND r.created_at > ?
        ''', (reminder_time, datetime.now() - timedelta(hours=2)))
        
        pending_reservations = cursor.fetchall()
        
        reminders_sent = 0
        
        for reservation in pending_reservations:
            try:
                cursor.execute('''
                    SELECT id FROM parking_reminders 
                    WHERE reservation_id = ? AND reminder_type = 'parking_pending'
                ''', (reservation['reservation_id'],))
                
                if cursor.fetchone():
                    continue
                #calculate time since booking
                booking_time = datetime.fromisoformat(reservation['created_at'])
                time_elapsed = datetime.now() - booking_time
                hours_elapsed = time_elapsed.total_seconds() / 3600
                
                reminder_email_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #ff9a56 0%, #ff6b35 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 28px;">⏰ Parking Reminder</h1>
                        </div>
                        
                        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                            <h2 style="color: #ff6b35; margin-top: 0;">Hello {reservation['username']}!</h2>
                            
                            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                <h3 style="color: #856404; margin-top: 0;">⚠️ Your Vehicle is Not Parked Yet!</h3>
                                <p style="color: #856404; margin-bottom: 0;">You have a reserved parking spot that's waiting for you.</p>
                            </div>
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                <h3 style="color: #495057; margin-top: 0;">Reservation Details</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Reservation ID:</td>
                                        <td style="padding: 8px 0;">#{reservation['reservation_id']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Location:</td>
                                        <td style="padding: 8px 0;">{reservation['prime_location_name']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Address:</td>
                                        <td style="padding: 8px 0;">{reservation['address']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Spot Number:</td>
                                        <td style="padding: 8px 0;">#{reservation['spot_number']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Reserved At:</td>
                                        <td style="padding: 8px 0;">{booking_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Time Elapsed:</td>
                                        <td style="padding: 8px 0; color: #dc3545; font-weight: bold;">{round(hours_elapsed, 1)} hours</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-weight: bold;">Rate:</td>
                                        <td style="padding: 8px 0;">${reservation['price']}/hour</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                <h3 style="color: #0c5460; margin-top: 0;">📍 What You Need to Do:</h3>
                                <ol style="color: #0c5460;">
                                    <li><strong>Arrive at the location:</strong> {reservation['address']}</li>
                                    <li><strong>Find your spot:</strong> Look for spot number #{reservation['spot_number']}</li>
                                    <li><strong>Park your vehicle</strong> in the reserved spot</li>
                                    <li><strong>Check-in:</strong> Use your ParkMate app to confirm parking</li>
                                </ol>
                            </div>
                            
                            <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                <p style="color: #721c24; margin: 0; font-weight: bold;">
                                    ⚠️ Important: Your reservation may expire if you don't arrive soon. Please park your vehicle to secure your spot!
                                </p>
                            </div>
                            
                            <div style="text-align: center; margin-top: 30px;">
                                <p style="color: #6c757d; font-size: 14px;">
                                    Need help? Contact us at admin@parkmate.com or call support.
                                </p>
                                <p style="color: #6c757d; font-size: 12px;">
                                    This is an automated reminder from ParkMate.
                                </p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # sends the reminder email
                if send_email(
                    reservation['email'], 
                    f"🚗 Parking Reminder - Spot #{reservation['spot_number']} Reserved", 
                    reminder_email_body
                ):
                    # Record that i sent this reminder
                    cursor.execute('''
                        INSERT INTO parking_reminders 
                        (reservation_id, user_id, reminder_type, sent_at) 
                        VALUES (?, ?, 'parking_pending', ?)
                    ''', (reservation['reservation_id'], reservation['user_id'], datetime.now()))
                    
                    reminders_sent += 1
                    logger.info(f"Parking reminder sent to {reservation['email']} for reservation #{reservation['reservation_id']}")
                
            except Exception as e:
                logger.error(f"Error sending parking reminder for reservation {reservation['reservation_id']}: {e}")
                continue
        
        if reminders_sent > 0:
            conn.commit()
        
        conn.close()
        
        logger.info(f"Parking reminders task completed: {reminders_sent} reminders sent")
        return f"Sent {reminders_sent} parking reminders"
        
    except Exception as e:
        logger.error(f"Error in send_parking_reminders: {e}")
        raise

# HEALTH CHECK AND SECURITY STATUS ENDPOINTS
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with security status"""
    try:
        # Check database connection
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        db_status = "OK"
        conn.close()
    except Exception:
        db_status = "ERROR"
    
    # Check Redis connection
    try:
        redis_client.ping()
        redis_status = "OK"
    except Exception:
        redis_status = "ERROR"
    
    # Check MailHog status
    mailhog_status = "OK" if check_mailhog_status() else "ERROR"
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'database': db_status,
            'redis': redis_status,
            'mailhog': mailhog_status
        },
        'security': {
            'jwt_enabled': True,
            'rate_limiting_enabled': True,
            'bcrypt_enabled': True,
            'cors_enabled': True,
            'security_headers': True,
            'blacklisted_tokens': len(JWT_BLACKLIST)
        },
        'version': '1.0.0'
    }), 200

@app.route('/api/security/token-info', methods=['GET'])
@token_required
def token_info():
    """Get information about the current JWT token"""
    try:
        user_data = request.current_user

        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if 'Bearer ' in auth_header else None
        
        if not token:
            return jsonify({'error': 'No JWT token provided'}), 400
        
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        return jsonify({
            'token_info': {
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'email': payload.get('email'),
                'is_admin': payload.get('is_admin'),
                'token_type': payload.get('type'),
                'issued_at': datetime.utcfromtimestamp(payload.get('iat')).isoformat() if payload.get('iat') else None,
                'expires_at': datetime.utcfromtimestamp(payload.get('exp')).isoformat() if payload.get('exp') else None,
                'jti': payload.get('jti'),
                'algorithm': JWT_ALGORITHM
            },
            'security': {
                'is_blacklisted': is_token_blacklisted(payload.get('jti', '')),
                'time_to_expiry': int((datetime.utcfromtimestamp(payload.get('exp')) - datetime.utcnow()).total_seconds()) if payload.get('exp') else None
            }
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# AUTHENTICATION API ENDPOINTS
@app.route('/api/register', methods=['POST'])
@rate_limited(REGISTER_RATE_LIMIT)
def register():
    """User registration endpoint"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone = data.get('phone', '')
        
        if not username or not password or not email:
            return jsonify({'error': 'Username, password, and email are required'}), 400
        
        if len(username) != 5:
            return jsonify({'error': 'Username must be exactly 5 characters long'}), 400
        
        if not username.isalnum():
            return jsonify({'error': 'Username must contain only alphanumeric characters (letters and numbers)'}), 400
        
        import re
        email_pattern = r'^[a-zA-Z]+@gmail\.com$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Email must be in format: alphabets@gmail.com (only Gmail addresses allowed)'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        if not password.isalnum():
            return jsonify({'error': 'Password must contain only alphanumeric characters (letters and numbers)'}), 400
        
        if phone:  
            if not phone.isdigit():
                return jsonify({'error': 'Phone number must contain only numeric digits'}), 400
            
            if len(phone) != 10:
                return jsonify({'error': 'Phone number must be exactly 10 digits long'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            return jsonify({'error': 'Username already exists'}), 400
        
        hashed_password = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password, email, phone, is_admin) 
            VALUES (?, ?, ?, ?, 0)
        ''', (username, hashed_password, email, phone))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        welcome_email_body = f"""
        <html>
        <body>
            <h2>Welcome to ParkMate! 🚗</h2>
            <p>Dear {username},</p>
            <p>Thank you for registering with ParkMate! Your account has been successfully created.</p>
            
            <div style="background-color: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>Account Details:</h3>
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Phone:</strong> {phone}</p>
                <p><strong>Registration Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h3>What's Next?</h3>
            <ul>
                <li>🚗 Browse available parking lots</li>
                <li>📅 Make your first parking reservation</li>
                <li>💰 View pricing and payment options</li>
                <li>📊 Track your parking history</li>
            </ul>
            <p>If you need any assistance, feel free to contact our support team.</p>
            <p>Happy Parking!<br>
            <strong>The ParkMate Team</strong></p>
        </body>
        </html>
        """
        if email:
            send_email(email, "Welcome to ParkMate! 🚗", welcome_email_body)
        
        invalidate_cache_pattern('*users*')
        invalidate_cache_pattern('*admin*')
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
@rate_limited(LOGIN_RATE_LIMIT)
def login():
    """User login endpoint"""
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
            SELECT id, username, email, phone, is_admin, password 
            FROM users WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user or not verify_password(password, user['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Remove password from user data before generatin tokens
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'phone': user['phone'],
            'is_admin': user['is_admin']
        }
        
        # Generate JWT tokens (JT-only authentication)
        tokens = generate_tokens(user_data)
        
        if not tokens:
            return jsonify({'error': 'Failed to generate authentication tokens'}), 500
        
        # Set session variables for backward compatibility with frontend
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = bool(user['is_admin'])
        session.permanent = True
        
        response_data = {
            'message': 'Login successful',
            'user': user_data,
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in']
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout endpoint - supports both session and JWT logout"""
    try:
        # Check for JWT token in header
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                pass
        
        if token:
            # JWT-based logout - add token to blacklist
            user_data = verify_token(token)
            if user_data and user_data.get('jti'):
                add_token_to_blacklist(user_data['jti'])
                logger.info(f"JWT token blacklisted for user: {user_data.get('username')}")
            
            data = request.get_json() or {}
            refresh_token = data.get('refresh_token')
            if refresh_token:
                refresh_data = verify_token(refresh_token, 'refresh')
                if refresh_data and refresh_data.get('jti'):
                    add_token_to_blacklist(refresh_data['jti'])
                    logger.info(f"Refresh token blacklisted for user: {refresh_data.get('username')}")
        
        # Session-based logout
        if session.get('user_id'):
            logger.info(f"Session logout for user ID: {session.get('user_id')}")
        
        session.clear()
        
        return jsonify({
            'message': 'Logged out successfully',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        
        session.clear()
        return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/refresh-token', methods=['POST'])
@rate_limited(LOGIN_RATE_LIMIT)  # Same rate limit as login
def refresh_token():
    """Refresh JWT token endpoint"""
    try:
        data = request.json
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400
        
        # Verify refresh token
        user_data = verify_token(refresh_token, 'refresh')
        if not user_data:
            return jsonify({'error': 'Invalid or expired refresh token'}), 401
        
        # Check if refresh token is blacklisted
        if user_data.get('jti') and is_token_blacklisted(user_data.get('jti')):
            return jsonify({'error': 'Refresh token has been revoked'}), 401
        
        # Getupdated user data from database
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, phone, is_admin 
            FROM users WHERE id = ?
        ''', (user_data['user_id'],))
        
        current_user = cursor.fetchone()
        conn.close()
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Blacklist the old refresh token
        if user_data.get('jti'):
            add_token_to_blacklist(user_data.get('jti'))
            logger.info(f"Old refresh token blacklisted for user: {current_user['username']}")
        
        # Generate new tokens
        tokens = generate_tokens(current_user)
        if not tokens:
            return jsonify({'error': 'Failed to generate tokens'}), 500
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'token_type': tokens['token_type'],
            'user': {
                'id': current_user['id'],
                'username': current_user['username'],
                'email': current_user['email'],
                'is_admin': current_user['is_admin']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/verify-token', methods=['POST'])
def verify_token_endpoint():
    """Verify JWT token endpoint"""
    try:
        data = request.json
        token = data.get('access_token')
        
        if not token:
            return jsonify({'error': 'Access token required'}), 400
        
        user_data = verify_token(token, 'access')
        if not user_data:
            return jsonify({'error': 'Invalid or expired token', 'valid': False}), 401
        
        return jsonify({
            'message': 'Token is valid',
            'valid': True,
            'user': {
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'is_admin': user_data['is_admin']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ADMIN API ENDPOINTS
@app.route('/api/admin/parking-lots', methods=['GET', 'POST'])
@admin_required
def admin_parking_lots():
    """Admin parking lots management endpoint"""
    
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
            
            cursor.execute('''
                INSERT INTO parking_lots (prime_location_name, price, address, pin_code, maximum_number_of_spots)
                VALUES (?, ?, ?, ?, ?)
            ''', (location_name, price, address, pin_code, max_spots))
            
            lot_id = cursor.lastrowid
            for spot_num in range(1, max_spots + 1):
                cursor.execute('''
                    INSERT INTO parking_spots (lot_id, spot_number, status)
                    VALUES (?, ?, 'A')
                ''', (lot_id, spot_num))
            
            conn.commit()
            
            cursor.execute('SELECT username, email FROM users WHERE id = ? AND is_admin = 1', (request.current_user['user_id'],))
            admin_details = cursor.fetchone()
            
            conn.close()
            
            if admin_details and admin_details['email']:
                lot_creation_email = f"""
                <html>
                <body>
                    <h2>New Parking Lot Created Successfully! 🅿️</h2>
                    <p>Dear {admin_details['username']},</p>
                    <p>A new parking lot has been successfully added to the ParkMate system.</p>
                    
                    <div style="background-color: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4CAF50;">
                        <h3>Parking Lot Details:</h3>
                        <p><strong>Lot ID:</strong> #{lot_id}</p>
                        <p><strong>Name:</strong> {location_name}</p>
                        <p><strong>Address:</strong> {address}</p>
                        <p><strong>PIN Code:</strong> {pin_code}</p>
                        <p><strong>Price:</strong> ${price}/hour</p>
                        <p><strong>Total Spots:</strong> {max_spots}</p>
                        <p><strong>Created At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Status:</strong> All spots available</p>
                    </div>
                    
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>System Updates:</h3>
                        <ul>
                            <li>✅ {max_spots} parking spots have been automatically created</li>
                            <li>🔄 All spots are marked as available</li>
                            <li>📊 The new lot is now visible to users</li>
                            <li>📈 Analytics data has been updated</li>
                        </ul>
                    </div>
                    <p>The parking lot is now live and ready for reservations!</p>
                    <p>Best regards,<br>
                    <strong>ParkMate System</strong></p>
                </body>
                </html>
                """
                
                send_email(admin_details['email'], f"New Parking Lot Created - {location_name}", lot_creation_email)
            
            cursor = get_db().cursor()
            cursor.execute('SELECT email, username FROM users WHERE is_admin = 0 AND email IS NOT NULL')
            users = cursor.fetchall()
            cursor.connection.close()
            
            for user in users:
                new_lot_notification = f"""
                <html>
                <body>
                    <h2>New Parking Location Available! 🆕</h2>
                    <p>Dear {user[1]},</p>
                    <p>Great news! A new parking location has been added to ParkMate.</p>
                    
                    <div style="background-color: #cce5ff; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007bff;">
                        <h3>New Location:</h3>
                        <p><strong>📍 {location_name}</strong></p>
                        <p><strong>Address:</strong> {address}</p>
                        <p><strong>Price:</strong> ${price}/hour</p>
                        <p><strong>Available Spots:</strong> {max_spots}</p>
                    </div>
                    
                    <p>🚗 Ready to book? Log in to your ParkMate account and reserve your spot now!</p>
                    
                    <p>Happy Parking!<br>
                    <strong>The ParkMate Team</strong></p>
                </body>
                </html>
                """
                
                send_email(user[0], f"New Parking Location: {location_name}", new_lot_notification)
            
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
@admin_required
def update_parking_lot(lot_id):
    """Update parking lot endpoint"""
    
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
        
        cursor.execute('SELECT * FROM parking_lots WHERE id = ?', (lot_id,))
        existing_lot = cursor.fetchone()
        if not existing_lot:
            conn.close()
            return jsonify({'error': 'Parking lot not found'}), 404
        
        cursor.execute('''
            UPDATE parking_lots 
            SET prime_location_name = ?, price = ?, address = ?, pin_code = ?, maximum_number_of_spots = ?
            WHERE id = ?
        ''', (location_name, price, address, pin_code, max_spots, lot_id))
        
        cursor.execute('SELECT COUNT(*) as count FROM parking_spots WHERE lot_id = ?', (lot_id,))
        current_spots_count = cursor.fetchone()[0]
        
        if max_spots > current_spots_count:
            for spot_num in range(current_spots_count + 1, max_spots + 1):
                cursor.execute('''
                    INSERT INTO parking_spots (lot_id, spot_number, status)
                    VALUES (?, ?, 'A')
                ''', (lot_id, spot_num))
        elif max_spots < current_spots_count:
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
        
        invalidate_cache_pattern('*parking_lots*')
        invalidate_cache_pattern('*admin*')
        
        return jsonify({'message': 'Parking lot updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/parking-lots/<int:lot_id>', methods=['DELETE'])
@admin_required
def delete_parking_lot(lot_id):
    """Delete parking lot endpoint"""
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM parking_lots WHERE id = ?', (lot_id,))
        existing_lot = cursor.fetchone()
        if not existing_lot:
            conn.close()
            return jsonify({'error': 'Parking lot not found'}), 404
        
        cursor.execute('SELECT COUNT(*) as occupied FROM parking_spots WHERE lot_id = ? AND status = "O"', (lot_id,))
        occupied_spots = cursor.fetchone()[0]
        
        if occupied_spots > 0:
            conn.close()
            return jsonify({'error': 'Cannot delete lot: it has occupied spots'}), 400
        
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
        
        cursor.execute('DELETE FROM parking_spots WHERE lot_id = ?', (lot_id,))
        cursor.execute('DELETE FROM parking_lots WHERE id = ?', (lot_id,))
        
        conn.commit()
        conn.close()
        
        invalidate_cache_pattern('*parking_lots*')
        invalidate_cache_pattern('*admin*')
        
        return jsonify({'message': 'Parking lot deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/parking-spots', methods=['GET'])
@admin_required
def admin_parking_spots():
    """Admin parking spots endpoint"""
    
    try:
        lot_id = request.args.get('lot_id')
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        if lot_id:
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
@admin_required
def free_parking_spot(spot_id):
    """Free parking spot endpoint"""
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM parking_spots WHERE id = ?', (spot_id,))
        spot = cursor.fetchone()
        if not spot:
            conn.close()
            return jsonify({'error': 'Parking spot not found'}), 404
        
        cursor.execute('UPDATE parking_spots SET status = ? WHERE id = ?', ('A', spot_id))
        
        cursor.execute('''
            UPDATE reservations 
            SET status = 'completed', end_timestamp = CURRENT_TIMESTAMP 
            WHERE spot_id = ? AND status = 'active'
        ''', (spot_id,))
        
        conn.commit()
        conn.close()
        
        invalidate_cache_pattern('*admin*')
        
        return jsonify({'message': 'Parking spot freed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error freeing parking spot: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_users():
    """Admin users management endpoint"""
    
    @cached(timeout=CACHE_TIMEOUT, key_prefix='admin:users')
    def get_users_with_stats():
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
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
@admin_required
def delete_user(user_id):
    """Delete user endpoint"""
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, is_admin FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user[2]:
            return jsonify({'error': 'Cannot delete admin users'}), 400
        
        cursor.execute('''
            SELECT spot_id FROM reservations 
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        spots_to_free = [row[0] for row in cursor.fetchall()]
        
        cursor.execute('DELETE FROM reservations WHERE user_id = ?', (user_id,))
        
        if spots_to_free:
            cursor.executemany(
                'UPDATE parking_spots SET status = "A" WHERE id = ?',
                [(spot_id,) for spot_id in spots_to_free]
            )
        
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        ensure_database_consistency()
        robust_cache_invalidation()
        
        logger.info(f"Admin deleted user: {user[1]} (ID: {user_id}), freed {len(spots_to_free)} spots")
        return jsonify({
            'message': 'User deleted successfully',
            'freed_spots': len(spots_to_free)
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500

@app.route('/api/admin/analytics', methods=['GET'])
@admin_required
def admin_analytics():
    """Admin analytics endpoint"""
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
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
        
        cursor.execute('SELECT SUM(parking_cost) as total_revenue FROM reservations WHERE parking_cost IS NOT NULL')
        revenue_result = cursor.fetchone()
        total_revenue = revenue_result['total_revenue'] if revenue_result['total_revenue'] else 0
        
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

@app.route('/api/admin/analytics/dashboard-data', methods=['GET'])
@admin_required
def admin_analytics_dashboard_data():
    """Admin analytics dashboard data endpoint - provides data structure expected by frontend"""
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        #occupancy data
        cursor.execute('''
            SELECT 
                pl.id,
                pl.prime_location_name,
                pl.maximum_number_of_spots,
                COUNT(ps.id) as total_spots,
                SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots,
                (COUNT(ps.id) - SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END)) as available_spots,
                ROUND((SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) * 100.0 / COUNT(ps.id)), 2) as occupancy_rate
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            GROUP BY pl.id
        ''')
        occupancy_data = cursor.fetchall()
        
        #revenue data (last 30 days)
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
        
        #monthly trends (last 12 months)
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as reservations,
                SUM(CASE WHEN parking_cost IS NOT NULL THEN parking_cost ELSE 0 END) as revenue
            FROM reservations 
            WHERE created_at >= date('now', '-12 month')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month
        ''')
        monthly_trends = cursor.fetchall()
        
        #hourly usage pattern
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
        
        #duration analysis
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24 <= 1 THEN '0-1 hours'
                    WHEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24 <= 2 THEN '1-2 hours'
                    WHEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24 <= 4 THEN '2-4 hours'
                    WHEN (julianday(leaving_timestamp) - julianday(parking_timestamp)) * 24 <= 8 THEN '4-8 hours'
                    ELSE '8+ hours'
                END as duration_category,
                COUNT(*) as count
            FROM reservations 
            WHERE parking_timestamp IS NOT NULL AND leaving_timestamp IS NOT NULL
                AND created_at >= date('now', '-30 days')
            GROUP BY duration_category
            ORDER BY count DESC
        ''')
        duration_analysis = cursor.fetchall()
        
        #top users (last 30 days)
        cursor.execute('''
            SELECT 
                u.username,
                COUNT(r.id) as total_reservations,
                SUM(CASE WHEN r.parking_cost IS NOT NULL THEN r.parking_cost ELSE 0 END) as total_spent
            FROM users u
            JOIN reservations r ON u.id = r.user_id
            WHERE u.is_admin = 0 AND r.created_at >= date('now', '-30 days')
            GROUP BY u.id
            ORDER BY total_reservations DESC
            LIMIT 10
        ''')
        top_users = cursor.fetchall()
        
        conn.close()
        
        #gives default data if no data exists
        if not occupancy_data:
            occupancy_data = [
                {
                    'id': 1,
                    'prime_location_name': 'Main Campus',
                    'maximum_number_of_spots': 50,
                    'total_spots': 50,
                    'occupied_spots': 30,
                    'available_spots': 20,
                    'occupancy_rate': 60.0
                },
                {
                    'id': 2,
                    'prime_location_name': 'Library',
                    'maximum_number_of_spots': 25,
                    'total_spots': 25,
                    'occupied_spots': 15,
                    'available_spots': 10,
                    'occupancy_rate': 60.0
                },
                {
                    'id': 3,
                    'prime_location_name': 'Sports Center',
                    'maximum_number_of_spots': 40,
                    'total_spots': 40,
                    'occupied_spots': 20,
                    'available_spots': 20,
                    'occupancy_rate': 50.0
                }
            ]
        
        if not revenue_data:
            import random
            from datetime import datetime, timedelta
            
            revenue_data = []
            for i in range(30):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                reservations = random.randint(5, 25)
                revenue = random.uniform(50, 300)
                revenue_data.append({
                    'date': date,
                    'reservations': reservations,
                    'revenue': round(revenue, 2)
                })
            revenue_data.sort(key=lambda x: x['date'])
        
        if not monthly_trends:
            import random
            monthly_trends = []
            for i in range(12):
                date = datetime.now() - timedelta(days=30*i)
                month = date.strftime('%Y-%m')
                reservations = random.randint(100, 500)
                revenue = random.uniform(1000, 5000)
                monthly_trends.append({
                    'month': month,
                    'reservations': reservations,
                    'revenue': round(revenue, 2)
                })
            monthly_trends.sort(key=lambda x: x['month'])
        
        if not hourly_usage:
            import random
            hourly_usage = []
            for hour in range(24):
                #simulates realistic parking patterns
                if 6 <= hour <= 9 or 17 <= hour <= 19:  # Peak hours
                    reservations = random.randint(10, 30)
                elif 10 <= hour <= 16:  # Day time
                    reservations = random.randint(5, 15)
                else:  # Night time
                    reservations = random.randint(1, 5)
                
                hourly_usage.append({
                    'hour': f"{hour:02d}",
                    'reservations': reservations
                })
        
        if not duration_analysis:
            duration_analysis = [
                {'duration_category': '0-1 hours', 'count': 45},
                {'duration_category': '1-2 hours', 'count': 32},
                {'duration_category': '2-4 hours', 'count': 28},
                {'duration_category': '4-8 hours', 'count': 15},
                {'duration_category': '8+ hours', 'count': 8}
            ]
        
        if not top_users:
            top_users = [
                {'username': 'user1', 'total_reservations': 25, 'total_spent': 375.50},
                {'username': 'user2', 'total_reservations': 22, 'total_spent': 330.75},
                {'username': 'user3', 'total_reservations': 18, 'total_spent': 270.00},
                {'username': 'user4', 'total_reservations': 15, 'total_spent': 225.25},
                {'username': 'user5', 'total_reservations': 12, 'total_spent': 180.00}
            ]
        
        dashboard_data = {
            'occupancy': occupancy_data,
            'revenue': revenue_data,
            'monthly_trends': monthly_trends,
            'hourly_usage': hourly_usage,
            'duration_analysis': duration_analysis,
            'top_users': top_users
        }
        
        logger.info(f"Dashboard data prepared with {len(occupancy_data)} lots, {len(revenue_data)} revenue records")
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Error in admin_analytics_dashboard_data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/admin/analytics/export-csv', methods=['POST'])
@admin_required
def admin_analytics_export_csv():
    """Export analytics data as CSV"""
    
    try:
        data = request.json
        export_type = data.get('type', 'all')
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        csv_data = ""
        filename = f"parkmate_analytics_{export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if export_type == 'all' or export_type == 'reservations':
            cursor.execute('''
                SELECT 
                    r.id,
                    u.username,
                    u.email,
                    pl.prime_location_name,
                    ps.spot_number,
                    r.created_at,
                    r.parking_timestamp,
                    r.leaving_timestamp,
                    r.parking_cost,
                    r.status
                FROM reservations r
                JOIN users u ON r.user_id = u.id
                JOIN parking_spots ps ON r.spot_id = ps.id
                JOIN parking_lots pl ON ps.lot_id = pl.id
                ORDER BY r.created_at DESC
            ''')
            reservations = cursor.fetchall()
            
            if reservations:
                csv_data += "Reservation ID,Username,Email,Location,Spot Number,Created At,Parking Time,Leaving Time,Cost,Status\n"
                for res in reservations:
                    csv_data += f"{res['id']},{res['username']},{res['email']},{res['prime_location_name']},{res['spot_number']},{res['created_at']},{res['parking_timestamp'] or ''},{res['leaving_timestamp'] or ''},{res['parking_cost'] or 0},{res['status']}\n"
        
        elif export_type == 'occupancy':
            cursor.execute('''
                SELECT 
                    pl.prime_location_name,
                    pl.address,
                    pl.maximum_number_of_spots,
                    COUNT(ps.id) as total_spots,
                    SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots,
                    (COUNT(ps.id) - SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END)) as available_spots,
                    ROUND((SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) * 100.0 / COUNT(ps.id)), 2) as occupancy_rate
                FROM parking_lots pl
                LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
                GROUP BY pl.id
            ''')
            occupancy = cursor.fetchall()
            
            if occupancy:
                csv_data += "Location,Address,Max Spots,Total Spots,Occupied,Available,Occupancy Rate %\n"
                for occ in occupancy:
                    csv_data += f"{occ['prime_location_name']},{occ['address']},{occ['maximum_number_of_spots']},{occ['total_spots']},{occ['occupied_spots']},{occ['available_spots']},{occ['occupancy_rate']}\n"
        
        elif export_type == 'revenue':
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as reservations,
                    SUM(CASE WHEN parking_cost IS NOT NULL THEN parking_cost ELSE 0 END) as revenue
                FROM reservations 
                WHERE parking_cost IS NOT NULL
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''')
            revenue = cursor.fetchall()
            
            if revenue:
                csv_data += "Date,Reservations,Revenue\n"
                for rev in revenue:
                    csv_data += f"{rev['date']},{rev['reservations']},{rev['revenue']}\n"
        
        elif export_type == 'users':
            cursor.execute('''
                SELECT 
                    u.id,
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
                csv_data += "User ID,Username,Email,Phone,Registered,Total Reservations,Total Spent\n"
                for user in users:
                    csv_data += f"{user['id']},{user['username']},{user['email']},{user['phone'] or ''},{user['created_at']},{user['total_reservations']},{user['total_spent']}\n"
        
        conn.close()
        
        if not csv_data:
            csv_data = "No data available for export\n"
        
        return jsonify({
            'csv_data': csv_data,
            'filename': filename
        }), 200
        
    except Exception as e:
        logger.error(f"Error in admin_analytics_export_csv: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# GRAPH GENERATION API ENDPOINTS
@app.route('/api/admin/graphs/occupancy', methods=['GET'])
@admin_required
def generate_occupancy_graph():
    """Generate occupancy analytics graph"""
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
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
            data = [
                {'prime_location_name': 'Main Campus', 'total_spots': 50, 'occupied_spots': 30},
                {'prime_location_name': 'Library', 'total_spots': 25, 'occupied_spots': 15},
                {'prime_location_name': 'Sports Center', 'total_spots': 40, 'occupied_spots': 20},
                {'prime_location_name': 'Student Center', 'total_spots': 35, 'occupied_spots': 25}
            ]
        
        df = pd.DataFrame(data)
        df['available_spots'] = df['total_spots'] - df['occupied_spots']
        df['occupancy_rate'] = (df['occupied_spots'] / df['total_spots'] * 100).round(2)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(8, 6))
        fig.suptitle('Parking Lot Analytics Dashboard', fontsize=12, fontweight='bold', y=0.96)
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
        wedges, texts, autotexts = ax1.pie(df['occupied_spots'], labels=df['prime_location_name'], 
                                          autopct='%1.1f%%', colors=colors[:len(df)])
        ax1.set_title('Current Occupancy Distribution', fontweight='bold')
        
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

        bars = ax3.bar(df['prime_location_name'], df['occupancy_rate'], 
                       color=['#FF6B6B' if x > 80 else '#FECA57' if x > 60 else '#4ECDC4' 
                              for x in df['occupancy_rate']])
        ax3.set_xlabel('Parking Lots')
        ax3.set_ylabel('Occupancy Rate (%)')
        ax3.set_title('Occupancy Rate by Location', fontweight='bold')
        ax3.set_xticklabels(df['prime_location_name'], rotation=45, ha='right')
        ax3.grid(True, alpha=0.3)
        
        for bar, rate in zip(bars, df['occupancy_rate']):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate}%', ha='center', va='bottom', fontweight='bold')
        
        total_spots = df['total_spots'].sum()
        total_occupied = df['occupied_spots'].sum()
        total_available = total_spots - total_occupied
        
        sizes = [total_occupied, total_available]
        colors_overview = ['#FF6B6B', '#4ECDC4']
        wedges, texts, autotexts = ax4.pie(sizes, labels=['Occupied', 'Available'], 
                                          autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*total_spots)} spots)',
                                          colors=colors_overview, startangle=90)
        ax4.set_title(f'Overall System Status\nTotal: {total_spots} spots', fontweight='bold')
        
        plt.tight_layout(h_pad=3.0, w_pad=2.5, rect=[0.08, 0.08, 0.92, 0.88])
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
@admin_required
def generate_revenue_graph():
    """Generate revenue analytics graph"""
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
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
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(8, 6))
        fig.suptitle('Revenue Analytics Dashboard', fontsize=14, fontweight='bold', y=0.98)
        
        ax1.plot(df['date'], df['revenue'], marker='o', linewidth=2, 
                color='#4ECDC4', markersize=4)
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Revenue ($)')
        ax1.set_title('Daily Revenue Trend (Last 30 Days)', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        ax2.scatter(df['reservations'], df['revenue'], alpha=0.6, 
                   color='#FF6B6B', s=50)
        ax2.set_xlabel('Number of Reservations')
        ax2.set_ylabel('Revenue ($)')
        ax2.set_title('Reservations vs Revenue Correlation', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        z = np.polyfit(df['reservations'], df['revenue'], 1)
        p = np.poly1d(z)
        ax2.plot(df['reservations'], p(df['reservations']), "r--", alpha=0.8)
        
        df['week'] = df['date'].dt.isocalendar().week
        weekly_revenue = df.groupby('week')['revenue'].sum().reset_index()
        
        bars = ax3.bar(range(len(weekly_revenue)), weekly_revenue['revenue'], 
                      color='#45B7D1', alpha=0.8)
        ax3.set_xlabel('Week')
        ax3.set_ylabel('Total Revenue ($)')
        ax3.set_title('Weekly Revenue Comparison', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        for bar, revenue in zip(bars, weekly_revenue['revenue']):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'${revenue:.0f}', ha='center', va='bottom', fontweight='bold')
        
        ax4.hist(df['revenue'], bins=10, color='#96CEB4', alpha=0.7, edgecolor='black')
        ax4.set_xlabel('Revenue ($)')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Daily Revenue Distribution', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout(h_pad=3.0, w_pad=2.5, rect=[0.08, 0.08, 0.92, 0.88])
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

# USER API ENDPOINTS
@app.route('/api/user/parking-lots', methods=['GET'])
@login_required
def user_parking_lots():
    """Get available parking lots for users"""
    
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
@login_required
def user_reserve_spot():
    """Reserve a parking spot"""
    
    try:
        data = request.json
        lot_id = data.get('lot_id')
        
        if not lot_id:
            return jsonify({'error': 'Lot ID is required'}), 400
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('BEGIN IMMEDIATE')
        
        try:
            cursor.execute('''
                SELECT r.id FROM reservations r
                JOIN parking_spots ps ON r.spot_id = ps.id
                WHERE r.user_id = ? AND r.status = 'active'
            ''', (request.current_user['user_id'],))
            
            if cursor.fetchone():
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'You already have an active reservation'}), 400
            
            cursor.execute('''
                SELECT id FROM parking_spots 
                WHERE lot_id = ? AND status = 'A' 
                ORDER BY spot_number LIMIT 1
            ''', (lot_id,))
            
            spot = cursor.fetchone()
            if not spot:
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'No available spots in this parking lot'}), 400
            
            cursor.execute('''
                INSERT INTO reservations (spot_id, user_id, status)
                VALUES (?, ?, 'active')
            ''', (spot['id'], request.current_user['user_id']))
            
            reservation_id = cursor.lastrowid
            
            cursor.execute('UPDATE parking_spots SET status = "O" WHERE id = ?', (spot['id'],))
            cursor.execute('COMMIT')
            
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
            
            cursor.execute('SELECT username, email FROM users WHERE id = ?', (request.current_user['user_id'],))
            user_details = cursor.fetchone()
            
            conn.close()
            
            if user_details and user_details['email']:
                reservation_email_body = f"""
                <html>
                <body>
                    <h2>Parking Spot Reserved Successfully! 🅿️</h2>
                    <p>Dear {user_details['username']},</p>
                    <p>Your parking spot has been successfully reserved. Here are the details:</p>
                    
                    <div style="background-color: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4CAF50;">
                        <h3>Reservation Details:</h3>
                        <p><strong>Reservation ID:</strong> #{reservation_id}</p>
                        <p><strong>Parking Lot:</strong> {reservation['prime_location_name']}</p>
                        <p><strong>Spot Number:</strong> {reservation['spot_number']}</p>
                        <p><strong>Address:</strong> {reservation['address']}</p>
                        <p><strong>Price:</strong> ${reservation['price']}/hour</p>
                        <p><strong>Reserved At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Status:</strong> Active</p>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <h3>Important Notes:</h3>
                        <ul>
                            <li>Your parking spot is now reserved and secured</li>
                            <li>Please arrive at the location to start your parking session</li>
                            <li>Don't forget to check in when you arrive</li>
                            <li>You can view your reservation details in your dashboard</li>
                        </ul>
                    </div>
                    
                    <p>Thank you for using ParkMate!</p>
                    <p>Safe travels! 🚗</p>
                    
                    <p>Best regards,<br>
                    <strong>The ParkMate Team</strong></p>
                </body>
                </html>
                """
                
                send_email(user_details['email'], f"Parking Reserved - {reservation['prime_location_name']}", reservation_email_body)
            
            robust_cache_invalidation()
            
            logger.info(f"User {request.current_user['user_id']} reserved spot {reservation['spot_number']} at {reservation['prime_location_name']}")
            
            return jsonify({
                'message': 'Spot reserved successfully',
                'reservation': reservation
            }), 201
            
        except Exception as e:
            cursor.execute('ROLLBACK')
            raise e
            
    except Exception as e:
        logger.error(f"Error in user_reserve_spot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/park-vehicle', methods=['POST'])
@login_required
def user_park_vehicle():
    """Start parking session"""
    
    try:
        data = request.json
        reservation_id = data.get('reservation_id')
        
        if not reservation_id:
            return jsonify({'error': 'Reservation ID is required'}), 400
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        parking_time =datetime.now()
        cursor.execute('''
            UPDATE reservations 
            SET parking_timestamp = ? 
            WHERE id = ? AND user_id = ? AND status = 'active'
        ''', (parking_time, reservation_id, request.current_user['user_id']))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Invalid reservation or already parked'}), 400
        
        conn.commit()
        conn.close()
        
        invalidate_cache_pattern(f'*user:{request.current_user["user_id"]}*')
        
        return jsonify({
            'message': 'Vehicle parked successfully',
            'parking_timestamp': parking_time.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/release-spot', methods=['POST'])
@login_required
def user_release_spot():
    """Release parking spot and complete session with payment"""
    
    try:
        data = request.json
        reservation_id = data.get('reservation_id')
        payment_method = data.get('payment_method')  # 'upi' or 'card'
        payment_details = data.get('payment_details')  # UPI ID or card details
        
        if not reservation_id:
            return jsonify({'error': 'Reservation ID is required'}), 400
            
        if not payment_method or payment_method not in ['upi', 'card']:
            return jsonify({'error': 'Valid payment method (upi/card) is required'}), 400
            
        if not payment_details:
            return jsonify({'error': 'Payment details are required'}), 400
        
        # Validate payment details based on method
        if payment_method == 'upi':
            upi_id = payment_details.get('upi_id')
            if not upi_id or '@' not in upi_id:
                return jsonify({'error': 'Valid UPI ID is required'}), 400
        elif payment_method == 'card':
            card_details = payment_details
            required_fields = ['card_number', 'expiry_month', 'expiry_year', 'cvv', 'cardholder_name']
            for field in required_fields:
                if not card_details.get(field):
                    return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
            
            # Basic card validation
            card_number = card_details['card_number'].replace(' ', '').replace('-', '')
            if not card_number.isdigit() or len(card_number) != 16:
                return jsonify({'error': 'Card number must be 16 digits'}), 400
                
            if not card_details['cvv'].isdigit() or len(card_details['cvv']) != 3:
                return jsonify({'error': 'CVV must be 3 digits'}), 400
                
            try:
                expiry_month = int(card_details['expiry_month'])
                expiry_year = int(card_details['expiry_year'])
                if expiry_month < 1 or expiry_month > 12:
                    return jsonify({'error': 'Invalid expiry month'}), 400
                if expiry_year < datetime.now().year:
                    return jsonify({'error': 'Card has expired'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid expiry date'}), 400
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('BEGIN IMMEDIATE')
        
        try:
            cursor.execute('''
                SELECT 
                    r.*,
                    ps.spot_number,
                    pl.price,
                    pl.prime_location_name,
                    pl.address
                FROM reservations r
                JOIN parking_spots ps ON r.spot_id = ps.id
                JOIN parking_lots pl ON ps.lot_id = pl.id
                WHERE r.id = ? AND r.user_id = ? AND r.status = 'active'
            ''', (reservation_id, request.current_user['user_id']))
            
            reservation = cursor.fetchone()
            if not reservation:
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'Invalid reservation'}), 400
            
            if not reservation['parking_timestamp']:
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'Vehicle not yet parked'}), 400
            
            leaving_time = datetime.now()
            parking_start = datetime.fromisoformat(reservation['parking_timestamp'])
            duration_hours = max(1, (leaving_time - parking_start).total_seconds() / 3600)
            parking_cost = duration_hours * reservation['price']
            
            # Create payment transaction
            import uuid
            transaction_id = f"PAY_{uuid.uuid4().hex[:12].upper()}"
            
            # Store payment details securely (in real world, encrypt sensitive data)
            if payment_method == 'upi':
                payment_details_json = json.dumps({
                    'upi_id': payment_details['upi_id'],
                    'method': 'upi'
                })
            else:  # card
                # In production, never store full card details
                payment_details_json = json.dumps({
                    'method': 'card',
                    'last_4_digits': card_number[-4:],
                    'cardholder_name': card_details['cardholder_name'],
                    'expiry': f"{card_details['expiry_month']}/{card_details['expiry_year']}"
                })
            
            # Simulate payment processing
            import random
            time.sleep(1)  # Simulate processing time
            
            # 95% success rate for demo
            payment_success = random.random() < 0.95
            
            cursor.execute('''
                INSERT INTO payment_transactions 
                (reservation_id, user_id, payment_method, payment_details, amount, transaction_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                reservation_id,
                request.current_user['user_id'], 
                payment_method, 
                payment_details_json, 
                parking_cost, 
                transaction_id,
                'completed' if payment_success else 'failed'
            ))
            
            if not payment_success:
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({
                    'error': 'Payment failed. Please try again.',
                    'transaction_id': transaction_id,
                    'amount': round(parking_cost, 2)
                }), 400
            
            cursor.execute('''
                UPDATE reservations 
                SET leaving_timestamp = ?, parking_cost = ?, status = 'completed'
                WHERE id = ?
            ''', (leaving_time, parking_cost, reservation_id))
            
            cursor.execute('UPDATE parking_spots SET status = "A" WHERE id = ?', (reservation['spot_id'],))
            
            # Update payment transaction with processed timestamp
            cursor.execute('''
                UPDATE payment_transactions 
                SET processed_at = CURRENT_TIMESTAMP
                WHERE transaction_id = ?
            ''', (transaction_id,))
            
            #gets user details for email notification before committing
            cursor.execute('SELECT email, username FROM users WHERE id = ?', (request.current_user['user_id'],))
            user_details = cursor.fetchone()
            
            cursor.execute('COMMIT')
            
            conn.close()
            
            robust_cache_invalidation()
            
            #sends release confirmation email with payment details
            if user_details:
                payment_method_display = "UPI Payment" if payment_method == 'upi' else "Card Payment"
                payment_info = payment_details['upi_id'] if payment_method == 'upi' else f"**** **** **** {card_number[-4:]}"
                
                release_email_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 28px;">✅ Payment Successful!</h1>
                        </div>
                        
                        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                            <h2 style="color: #4CAF50; margin-top: 0;">Hello {user_details['username']}!</h2>
                            
                            <p>Thank you! Your payment has been processed successfully and your parking session is now complete.</p>
                            
                            <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4CAF50;">
                                <h3 style="color: #2e7d32; margin-top: 0;">💳 Payment Details</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr style="border-bottom: 1px solid #c8e6c9;">
                                        <td style="padding: 8px 0; font-weight: bold;">Transaction ID:</td>
                                        <td style="padding: 8px 0; color: #2e7d32; font-weight: bold;">{transaction_id}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #c8e6c9;">
                                        <td style="padding: 8px 0; font-weight: bold;">Payment Method:</td>
                                        <td style="padding: 8px 0;">{payment_method_display}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #c8e6c9;">
                                        <td style="padding: 8px 0; font-weight: bold;">Payment Info:</td>
                                        <td style="padding: 8px 0;">{payment_info}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-weight: bold;">Amount Paid:</td>
                                        <td style="padding: 8px 0; color: #2e7d32; font-weight: bold; font-size: 18px;">${round(parking_cost, 2)}</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                <h3 style="color: #495057; margin-top: 0;">🅿️ Parking Session Summary</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Parking Spot:</td>
                                        <td style="padding: 8px 0;">#{reservation['spot_number']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Location:</td>
                                        <td style="padding: 8px 0;">{reservation.get('prime_location_name', 'N/A')}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Parked At:</td>
                                        <td style="padding: 8px 0;">{parking_start.strftime('%Y-%m-%d %H:%M:%S')}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Left At:</td>
                                        <td style="padding: 8px 0;">{leaving_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td style="padding: 8px 0; font-weight: bold;">Duration:</td>
                                        <td style="padding: 8px 0;">{round(duration_hours, 2)} hours</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-weight: bold;">Rate:</td>
                                        <td style="padding: 8px 0;">${reservation['price']}/hour</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <div style="text-align: center; margin-top: 30px;">
                                <p style="color: #4CAF50; font-weight: bold; font-size: 16px;">
                                    Payment completed successfully! Thank you for using ParkMate! 🚗
                                </p>
                                <p style="color: #6c757d; font-size: 14px;">
                                    Keep this email as your receipt.<br>
                                    <strong>The ParkMate Team</strong>
                                </p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                #send the email asynchronously
                try:
                    send_email(user_details['email'], f"Payment Receipt - Spot #{reservation['spot_number']} (${round(parking_cost, 2)})", release_email_body)
                    logger.info(f"Payment receipt email sent to {user_details['email']}")
                except Exception as email_error:
                    logger.error(f"Failed to send payment receipt email: {email_error}")
            
            logger.info(f"User {request.current_user['user_id']} released spot {reservation['spot_number']}, paid: ${round(parking_cost, 2)} - Transaction: {transaction_id}")
            
            return jsonify({
                'message': 'Payment successful! Spot released.',
                'leaving_timestamp': leaving_time.isoformat(),
                'parking_cost': round(parking_cost, 2),
                'duration_hours': round(duration_hours, 2),
                'payment': {
                    'transaction_id': transaction_id,
                    'amount': round(parking_cost, 2),
                    'method': payment_method,
                    'status': 'completed'
                }
            }), 200
            
        except Exception as e:
            cursor.execute('ROLLBACK')
            conn.close()
            raise e
            
    except Exception as e:
        logger.error(f"Error in user_release_spot with payment: {e}")
        return jsonify({'error': str(e)}), 500

# Legacy release endpoint without payment (for backward compatibility)
@app.route('/api/user/release-spot-legacy', methods=['POST'])
@login_required
def user_release_spot_legacy():
    """Release parking spot and complete session (Legacy - No Payment)"""
    
    try:
        data = request.json
        reservation_id = data.get('reservation_id')
        
        if not reservation_id:
            return jsonify({'error': 'Reservation ID is required'}), 400
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('BEGIN IMMEDIATE')
        
        try:
            cursor.execute('''
                SELECT 
                    r.*,
                    ps.spot_number,
                    pl.price,
                    pl.prime_location_name,
                    pl.address
                FROM reservations r
                JOIN parking_spots ps ON r.spot_id = ps.id
                JOIN parking_lots pl ON ps.lot_id = pl.id
                WHERE r.id = ? AND r.user_id = ? AND r.status = 'active'
            ''', (reservation_id, request.current_user['user_id']))
            
            reservation = cursor.fetchone()
            if not reservation:
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'Invalid reservation'}), 400
            
            if not reservation['parking_timestamp']:
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'Vehicle not yet parked'}), 400
            
            leaving_time = datetime.now()
            parking_start = datetime.fromisoformat(reservation['parking_timestamp'])
            duration_hours = max(1, (leaving_time - parking_start).total_seconds() / 3600)
            parking_cost = duration_hours * reservation['price']
            
            cursor.execute('''
                UPDATE reservations 
                SET leaving_timestamp = ?, parking_cost = ?, status = 'completed'
                WHERE id = ?
            ''', (leaving_time, parking_cost, reservation_id))
            
            cursor.execute('UPDATE parking_spots SET status = "A" WHERE id = ?', (reservation['spot_id'],))
            
            cursor.execute('COMMIT')
            
            conn.close()
            
            robust_cache_invalidation()
            
            logger.info(f"User {request.current_user['user_id']} released spot {reservation['spot_number']} (legacy), cost: ${round(parking_cost, 2)}")
            
            return jsonify({
                'message': 'Spot released successfully (Legacy)',
                'leaving_timestamp': leaving_time.isoformat(),
                'parking_cost': round(parking_cost, 2),
                'duration_hours': round(duration_hours, 2)
            }), 200
            
        except Exception as e:
            cursor.execute('ROLLBACK')
            raise e
            
    except Exception as e:
        logger.error(f"Error in user_release_spot_legacy: {e}")
        return jsonify({'error': str(e)}), 500
        logger.error(f"Error releasing spot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/parking-lots/<int:lot_id>/slots', methods=['GET'])
@login_required
def user_get_available_slots(lot_id):
    """Get available parking slots for a specific lot"""
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Verify the parking lot exists
        cursor.execute('SELECT id, prime_location_name FROM parking_lots WHERE id = ?', (lot_id,))
        lot = cursor.fetchone()
        
        if not lot:
            conn.close()
            return jsonify({'error': 'Parking lot not found'}), 404
        
        # Get all available slots for this lot
        cursor.execute('''
            SELECT 
                id,
                spot_number,
                status
            FROM parking_spots 
            WHERE lot_id = ? AND status = 'A'
            ORDER BY spot_number
        ''', (lot_id,))
        
        available_slots = cursor.fetchall()
        conn.close()
        
        logger.info(f"Retrieved {len(available_slots)} available slots for lot {lot_id}")
        
        return jsonify({
            'lot_id': lot_id,
            'lot_name': lot['prime_location_name'],
            'available_slots': available_slots
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching available slots for lot {lot_id}: {e}")
        return jsonify({'error': 'Failed to fetch available slots'}), 500

@app.route('/api/user/reserve-specific-spot', methods=['POST'])
@login_required
def user_reserve_specific_spot():
    """Reserve a specific parking spot by spot ID (Free booking)"""
    
    try:
        data = request.json
        spot_id = data.get('spot_id')
        
        if not spot_id:
            return jsonify({'error': 'Spot ID is required'}), 400
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('BEGIN IMMEDIATE')
        
        try:
            # Check if user already has an active reservation
            cursor.execute('''
                SELECT r.id FROM reservations r
                JOIN parking_spots ps ON r.spot_id = ps.id
                WHERE r.user_id = ? AND r.status = 'active'
            ''', (request.current_user['user_id'],))
            
            if cursor.fetchone():
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'You already have an active reservation'}), 400
            
            # Check if the specific spot is available
            cursor.execute('''
                SELECT 
                    ps.id,
                    ps.spot_number,
                    ps.status,
                    pl.id as lot_id,
                    pl.prime_location_name,
                    pl.address,
                    pl.price
                FROM parking_spots ps
                JOIN parking_lots pl ON ps.lot_id = pl.id
                WHERE ps.id = ?
            ''', (spot_id,))
            
            spot = cursor.fetchone()
            
            if not spot:
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'Parking spot not found'}), 404
            
            if spot['status'] != 'A':
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'This parking spot is no longer available'}), 400
            
            # Create the reservation (no payment required)
            cursor.execute('''
                INSERT INTO reservations (spot_id, user_id, status)
                VALUES (?, ?, 'active')
            ''', (spot_id, request.current_user['user_id']))
            
            reservation_id = cursor.lastrowid
            
            # Mark the spot as occupied
            cursor.execute('UPDATE parking_spots SET status = "O" WHERE id = ?', (spot_id,))
            
            cursor.execute('COMMIT')
            
            # Get the complete reservation details
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
            
            # Get user details for email notification
            cursor.execute('SELECT username, email FROM users WHERE id = ?', (request.current_user['user_id'],))
            user_details = cursor.fetchone()
            
            conn.close()
            
            # Send confirmation email
            if user_details and user_details['email']:
                reservation_email_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #64b5f6 0%, #1976d2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 28px;">🅿️ Parking Spot Reserved!</h1>
                        </div>
                        
                        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                            <h2 style="color: #1976d2; margin-top: 0;">Hello {user_details['username']}!</h2>
                            
                            <p>Great! Your specific parking spot has been successfully reserved.</p>
                            
                            <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #1976d2;">
                                <h3 style="color: #0d47a1; margin-top: 0;">Reservation Details</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr style="border-bottom: 1px solid #bbdefb;">
                                        <td style="padding: 8px 0; font-weight: bold;">Reservation ID:</td>
                                        <td style="padding: 8px 0;">#{reservation_id}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #bbdefb;">
                                        <td style="padding: 8px 0; font-weight: bold;">Parking Lot:</td>
                                        <td style="padding: 8px 0;">{reservation['prime_location_name']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #bbdefb;">
                                        <td style="padding: 8px 0; font-weight: bold;">Your Spot Number:</td>
                                        <td style="padding: 8px 0; color: #1976d2; font-weight: bold; font-size: 18px;">#{reservation['spot_number']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #bbdefb;">
                                        <td style="padding: 8px 0; font-weight: bold;">Address:</td>
                                        <td style="padding: 8px 0;">{reservation['address']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #bbdefb;">
                                        <td style="padding: 8px 0; font-weight: bold;">Rate:</td>
                                        <td style="padding: 8px 0;">${reservation['price']}/hour</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-weight: bold;">Reserved At:</td>
                                        <td style="padding: 8px 0;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <div style="background: #f3e5f5; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #9c27b0;">
                                <h3 style="color: #4a148c; margin-top: 0;">📍 What's Next?</h3>
                                <ol style="color: #4a148c; margin: 0;">
                                    <li><strong>Navigate to:</strong> {reservation['address']}</li>
                                    <li><strong>Look for spot:</strong> #{reservation['spot_number']}</li>
                                    <li><strong>Park your vehicle</strong> in your reserved spot</li>
                                    <li><strong>Payment:</strong> You'll pay when you leave the parking</li>
                                </ol>
                            </div>
                            
                            <div style="text-align: center; margin-top: 30px;">
                                <p style="color: #1976d2; font-weight: bold; font-size: 16px;">
                                    Your spot is secured! Pay when you leave! 🚗
                                </p>
                                <p style="color: #6c757d; font-size: 14px;">
                                    Best regards,<br>
                                    <strong>The ParkMate Team</strong>
                                </p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                send_email(
                    user_details['email'], 
                    f"Spot #{reservation['spot_number']} Reserved - {reservation['prime_location_name']}", 
                    reservation_email_body
                )
            
            robust_cache_invalidation()
            
            logger.info(f"User {request.current_user['user_id']} reserved specific spot {reservation['spot_number']} (ID: {spot_id}) at {reservation['prime_location_name']}")
            
            return jsonify({
                'message': f'Spot #{spot["spot_number"]} reserved successfully! Pay when you leave.',
                'reservation': reservation
            }), 201
            
        except Exception as e:
            cursor.execute('ROLLBACK')
            raise e
            
    except Exception as e:
        logger.error(f"Error in user_reserve_specific_spot: {e}")
        return jsonify({'error': str(e)}), 500

# Payment Gateway Endpoints
@app.route('/api/payment/validate', methods=['POST'])
@login_required
def validate_payment_details():
    """Validate payment details before processing"""
    try:
        data = request.json
        payment_method = data.get('payment_method')
        payment_details = data.get('payment_details')
        
        if not payment_method or payment_method not in ['upi', 'card']:
            return jsonify({'error': 'Valid payment method (upi/card) is required', 'valid': False}), 400
            
        if not payment_details:
            return jsonify({'error': 'Payment details are required', 'valid': False}), 400
        
        errors = []
        
        if payment_method == 'upi':
            upi_id = payment_details.get('upi_id', '').strip()
            if not upi_id:
                errors.append('UPI ID is required')
            elif '@' not in upi_id:
                errors.append('Invalid UPI ID format')
            elif len(upi_id) < 5:
                errors.append('UPI ID too short')
                
        elif payment_method == 'card':
            card_details = payment_details
            required_fields = {
                'card_number': 'Card number',
                'expiry_month': 'Expiry month',
                'expiry_year': 'Expiry year',
                'cvv': 'CVV',
                'cardholder_name': 'Cardholder name'
            }
            
            for field, display_name in required_fields.items():
                if not card_details.get(field, '').strip():
                    errors.append(f'{display_name} is required')
            
            if card_details.get('card_number'):
                card_number = card_details['card_number'].replace(' ', '').replace('-', '')
                if not card_number.isdigit():
                    errors.append('Card number must contain only digits')
                elif len(card_number) != 16:
                    errors.append('Card number must be 16 digits')
                    
            if card_details.get('cvv'):
                if not card_details['cvv'].isdigit():
                    errors.append('CVV must contain only digits')
                elif len(card_details['cvv']) != 3:
                    errors.append('CVV must be 3 digits')
                    
            if card_details.get('expiry_month') and card_details.get('expiry_year'):
                try:
                    expiry_month = int(card_details['expiry_month'])
                    expiry_year = int(card_details['expiry_year'])
                    
                    if expiry_month < 1 or expiry_month > 12:
                        errors.append('Invalid expiry month')
                    if expiry_year < datetime.now().year:
                        errors.append('Card has expired')
                    elif expiry_year == datetime.now().year and expiry_month < datetime.now().month:
                        errors.append('Card has expired')
                except ValueError:
                    errors.append('Invalid expiry date')
                    
            if card_details.get('cardholder_name'):
                if len(card_details['cardholder_name'].strip()) < 2:
                    errors.append('Cardholder name too short')
        
        if errors:
            return jsonify({'valid': False, 'errors': errors}), 400
            
        return jsonify({'valid': True, 'message': 'Payment details are valid'}), 200
        
    except Exception as e:
        logger.error(f"Error validating payment details: {e}")
        return jsonify({'error': 'Internal server error', 'valid': False}), 500

@app.route('/api/payment/transactions', methods=['GET'])
@login_required
def get_user_transactions():
    """Get user's payment transaction history"""
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                pt.id,
                pt.transaction_id,
                pt.payment_method,
                pt.amount,
                pt.status,
                pt.created_at,
                pt.processed_at,
                r.id as reservation_id,
                ps.spot_number,
                pl.prime_location_name,
                pl.address
            FROM payment_transactions pt
            LEFT JOIN reservations r ON pt.reservation_id = r.id
            LEFT JOIN parking_spots ps ON r.spot_id = ps.id
            LEFT JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE pt.user_id = ?
            ORDER BY pt.created_at DESC
        ''', (request.current_user['user_id'],))
        
        transactions = cursor.fetchall()
        conn.close()
        
        return jsonify({'transactions': transactions}), 200
        
    except Exception as e:
        logger.error(f"Error fetching user transactions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Keep the original reservation endpoint without payment for backward compatibility
@app.route('/api/user/reserve-specific-spot-legacy', methods=['POST'])
@login_required
def user_reserve_specific_spot_legacy():
    """Reserve a specific parking spot by spot ID (Legacy - No Payment)"""
    
    try:
        data = request.json
        spot_id = data.get('spot_id')
        
        if not spot_id:
            return jsonify({'error': 'Spot ID is required'}), 400
        
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('BEGIN IMMEDIATE')
        
        try:
            # Check if user already has an active reservation
            cursor.execute('''
                SELECT r.id FROM reservations r
                JOIN parking_spots ps ON r.spot_id = ps.id
                WHERE r.user_id = ? AND r.status = 'active'
            ''', (request.current_user['user_id'],))
            
            if cursor.fetchone():
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'You already have an active reservation'}), 400
            
            # Check if the specific spot is available
            cursor.execute('''
                SELECT 
                    ps.id,
                    ps.spot_number,
                    ps.status,
                    pl.id as lot_id,
                    pl.prime_location_name,
                    pl.address,
                    pl.price
                FROM parking_spots ps
                JOIN parking_lots pl ON ps.lot_id = pl.id
                WHERE ps.id = ?
            ''', (spot_id,))
            
            spot = cursor.fetchone()
            
            if not spot:
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'Parking spot not found'}), 404
            
            if spot['status'] != 'A':
                cursor.execute('ROLLBACK')
                conn.close()
                return jsonify({'error': 'This parking spot is no longer available'}), 400
            
            # Create the reservation
            cursor.execute('''
                INSERT INTO reservations (spot_id, user_id, status)
                VALUES (?, ?, 'active')
            ''', (spot_id, request.current_user['user_id']))
            
            reservation_id = cursor.lastrowid
            
            # Mark the spot as occupied
            cursor.execute('UPDATE parking_spots SET status = "O" WHERE id = ?', (spot_id,))
            
            cursor.execute('COMMIT')
            
            # Get the complete reservation details
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
            robust_cache_invalidation()
            
            return jsonify({
                'message': f'Spot #{spot["spot_number"]} reserved successfully (Legacy)',
                'reservation': reservation
            }), 201
            
        except Exception as e:
            cursor.execute('ROLLBACK')
            raise e
            
    except Exception as e:
        logger.error(f"Error in user_reserve_specific_spot_legacy: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/my-reservations', methods=['GET'])
@login_required
def user_reservations():
    """Get user's reservations"""
    
    try:
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
        ''', (request.current_user['user_id'],))
        
        reservations = cursor.fetchall()
        conn.close()
        
        return jsonify({'reservations': reservations}), 200
        
    except Exception as e:
        logger.error(f"Error fetching user reservations: {e}")
        return jsonify({'error': 'Failed to fetch reservations'}), 500

@app.route('/api/user/analytics', methods=['GET'])
@login_required
def user_analytics():
    """Get user analytics data"""
    
    @cached(timeout=ANALYTICS_CACHE_TIMEOUT, key_prefix=f'user:{request.current_user["user_id"]}')
    def get_user_analytics():
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        user_id = request.current_user['user_id']
        
        cursor.execute('SELECT COUNT(*) as total_reservations FROM reservations WHERE user_id = ?', (user_id,))
        total_reservations = cursor.fetchone()['total_reservations']
        
        cursor.execute('SELECT COUNT(*) as active_reservations FROM reservations WHERE user_id = ? AND status = "active"', (user_id,))
        active_reservations = cursor.fetchone()['active_reservations']
        
        cursor.execute('SELECT SUM(parking_cost) as total_spent FROM reservations WHERE user_id = ? AND parking_cost IS NOT NULL', (user_id,))
        total_spent = cursor.fetchone()['total_spent'] or 0
        
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

# UTILITY AND MANAGEMENT API ENDPOINTS
@app.route('/api/user/preferences', methods=['GET', 'POST'])
@login_required
def user_preferences():
    """Manage user notification preferences"""
    
    conn = get_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    user_id = request.current_user['user_id']
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
        prefs = cursor.fetchone()
        
        if not prefs:
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
@login_required
def request_csv_export():
    """Request CSV export of user data"""
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        user_id = request.current_user['user_id']
        
        cursor.execute('''
            SELECT * FROM csv_export_jobs 
            WHERE user_id = ? AND status IN ('pending', 'processing')
        ''', (user_id,))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Export already in progress'}), 400
        
        cursor.execute('''
            INSERT INTO csv_export_jobs (user_id, status)
            VALUES (?, 'processing')
        ''', (user_id,))
        
        export_job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        task = export_user_parking_data_csv.delay(user_id)
        
        return jsonify({
            'message': 'CSV export started',
            'export_job_id': export_job_id,
            'task_id': task.id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/export-status/<int:export_job_id>', methods=['GET'])
@login_required
def csv_export_status(export_job_id):
    """Check CSV export status"""
    
    try:
        conn = get_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM csv_export_jobs 
            WHERE id = ? AND user_id = ?
        ''', (export_job_id, request.current_user['user_id']))
        
        export_job = cursor.fetchone()
        
        if not export_job:
            conn.close()
            return jsonify({'error': 'Export job not found'}), 404
        
        conn.close()
        return jsonify({'export_job': export_job}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/cache/stats', methods=['GET'])
@admin_required
def cache_stats():
    """Get Redis cache statistics"""
    
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
@admin_required
def clear_cache():
    """Clear Redis cache"""
    
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

@app.route('/api/admin/trigger-parking-reminders', methods=['POST'])
@admin_required
def trigger_parking_reminders():
    """Manually trigger parking reminders (Admin only)"""
    
    try:
        #triggers th Celery task
        task = send_parking_reminders.delay()
        return jsonify({
            'message': 'Parking reminders task triggered successfully',
            'task_id': task.id
        }), 200
    except Exception as e:
        logger.error(f"Error triggering parking reminders: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/trigger-monthly-reports', methods=['POST'])
@admin_required
def trigger_monthly_reports():
    """Manually trigger monthly reports generation (Admin only)"""
    
    try:
        data = request.json if request.json else {}
        user_id = data.get('user_id') 
        month = data.get('month')     
        year = data.get('year')        
        
        #triggers Celery task
        if user_id:
            task = generate_monthly_activity_report.delay(user_id, month, year)
            message = f'Monthly report task triggered for user ID {user_id}'
        else:
            task = generate_monthly_activity_report.delay(None, month, year)
            message = 'Monthly reports task triggered for all users'
            
        return jsonify({
            'message': message,
            'task_id': task.id,
            'parameters': {
                'user_id': user_id,
                'month': month or 'current',
                'year': year or 'current'
            }
        }), 200
    except Exception as e:
        logger.error(f"Error triggering monthly reports: {e}")
        return jsonify({'error': str(e)}), 500

# APPLICATION ENTRY POINT
if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print("PARKMATE - PARKING MANAGEMENT SYSTEM")
    print("=" * 60)
    print("Database initialized successfully!")
    print("Admin credentials: username='admin', password='admin123'")
    print("\n🚀 SYSTEM FEATURES ENABLED:")
    print("✓ Redis caching for improved performance")
    print("✓ Background task processing with Celery")
    print("✓ Periodic cleanup of expired reservations")
    print("✓ Daily report generation")
    print("✓ Parking optimization analysis")
    print("✓ Cache management endpoints")
    print("✓ Health check endpoint")
    print("✓ Email notifications via MailHog")
    print("✓ CSV data export functionality")
    print("✓ User preferences management")
    print("✓ Real-time analytics dashboards")
    
    print("\n📧 EMAIL & NOTIFICATION JOBS:")
    print("• Daily reminders via email/Google Chat")
    print("• Monthly activity reports via email")
    print("• Registration welcome emails")
    print("• Reservation confirmation emails")
    print("• Parking completion receipts")
    
    print("\n🔧 ADMIN MANAGEMENT TOOLS:")
    print("• Comprehensive parking lot management")
    print("• User management and analytics")
    print("• Real-time system monitoring")
    print("• Cache management and optimization")
    print("• Batch job processing and monitoring")
    
    print("\n🌐 API ENDPOINTS AVAILABLE:")
    print("Authentication:")
    print("  POST /api/register - User registration")
    print("  POST /api/login - User login")
    print("  POST /api/logout - User logout")
    
    print("\nUser Operations:")
    print("  GET /api/user/parking-lots - View available lots")
    print("  POST /api/user/reserve-spot - Reserve parking spot")
    print("  POST /api/user/park-vehicle - Start parking session")
    print("  POST /api/user/release-spot - End parking session")
    print("  GET /api/user/my-reservations - View reservations")
    print("  GET /api/user/analytics - User analytics")
    
    print("\nAdmin Operations:")
    print("  GET/POST /api/admin/parking-lots - Manage parking lots")
    print("  GET /api/admin/parking-spots - View parking spots")
    print("  GET /api/admin/users - Manage users")
    print("  GET /api/admin/analytics - System analytics")
    print("  GET /api/admin/graphs/* - Generate charts")
    
    print("\nSystem Management:")
    print("  GET /api/health - System health check")
    print("  GET /api/admin/cache/stats - Cache statistics")
    print("  POST /api/admin/cache/clear - Clear cache")
    
    print("\n⚙️ ENVIRONMENT SETUP:")
    print("Required environment variables:")
    print("  GOOGLE_CHAT_WEBHOOK - Google Chat webhook URL (optional)")
    
    print("\n🔄 BACKGROUND SERVICES:")
    print("To start Celery worker:")
    print("  celery -A main.celery worker --loglevel=info")
    print("\nTo start Celery beat scheduler:")
    print("  celery -A main.celery beat --loglevel=info")
    
    print("\n📧 SCHEDULED TASKS (Beat Schedule):")
    print("• Daily reminders: Every day at 6:00 PM")
    print("• Monthly reports: 1st of every month at midnight")
    print("• Parking reminders: Every 15 minutes")
    print("• Cleanup expired reservations: Every hour")
    print("• Daily reports: Every 24 hours")
    print("• Parking optimization: Every 6 hours")
    
    print("\n📊 MONITORING:")
    print("MailHog Web UI: http://localhost:8025")
    print("Application: http://localhost:5000")
    
    print("=" * 60)
    print("🚗 PARKMATE IS READY TO SERVE!")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
