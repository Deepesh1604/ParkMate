# 🅿️ ParkMate - Smart Parking Management System

A comprehensive parking lot management system built with Flask backend and Vue.js frontend, featuring real-time booking, automated email notifications, and advanced analytics.

## 🚀 Features

### 🔐 User Management
- User registration and authentication
- Admin and regular user roles
- Secure password hashing with SHA256
- Session-based authentication

### 🅿️ Parking Management
- Multiple parking lot support
- Real-time spot availability tracking
- Automatic spot allocation and optimization
- Reservation system with time tracking
- Pricing management per location

### 📧 Email Notifications
- Daily parking reminders
- Monthly activity reports
- Booking confirmations
- HTML-styled email templates
- MailHog integration for development

### 📊 Analytics & Reporting
- Daily usage statistics
- Monthly user activity reports
- Parking lot utilization metrics
- Revenue tracking
- CSV export functionality

### 🔄 Background Processing
- Celery-based task queue system
- Automated cleanup of expired reservations
- Scheduled email campaigns
- Performance optimization routines
- Redis-backed caching system

## 🛠️ Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLite** - Database with raw SQL queries
- **Celery** - Background task processing
- **Redis** - Caching and message broker
- **MailHog** - Email testing server

### Frontend
- **Vue.js 3** - Progressive JavaScript framework
- **Vite** - Build tool and development server
- **Vue Router** - Client-side routing
- **CSS3** - Responsive styling

### DevOps & Tools
- **Git** - Version control
- **npm** - Package management
- **Python venv** - Virtual environment

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- Redis server
- Git

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Deepesh1604/Parkmate.git
cd Mad-2-project
```

### 2. Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install flask flask-cors celery redis matplotlib smtplib-ssl

# Initialize database
python3 -c "from main import init_db; init_db()"
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Start Services

#### Start Redis Server
```bash
redis-server
```

#### Start MailHog (for email testing)
```bash
./mailhog &  # Runs on localhost:8025 (web) and localhost:1025 (SMTP)
```

#### Start Backend Services
```bash
# Terminal 1: Flask Application
python3 main.py

# Terminal 2: Celery Worker
celery -A main.celery worker --loglevel=info

# Terminal 3: Celery Beat Scheduler
celery -A main.celery beat --loglevel=info
```

#### Start Frontend
```bash
cd frontend
npm run dev  # Runs on http://localhost:5173
```

## 🏗️ Project Structure

```
Mad-2-project/
├── main.py                    # Main Flask application
├── parking_lot.db            # SQLite database
├── mailhog                   # MailHog binary
├── celerybeat-schedule       # Celery beat schedule
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # Project documentation
├── exports/                 # CSV export directory
├── __pycache__/            # Python cache files
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   │   ├── admin/     # Admin-specific components
│   │   │   └── user/      # User-specific components
│   │   ├── router/        # Vue Router configuration
│   │   ├── views/         # Main view components
│   │   └── assets/        # Static assets
│   ├── public/            # Public assets
│   ├── package.json       # Node.js dependencies
│   └── vite.config.js     # Vite configuration
└── logs/                  # Application logs
    ├── celery_worker.log
    ├── celery_beat.log
    └── mailhog.log
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
REDIS_URL=redis://localhost:6379
EMAIL_HOST=localhost
EMAIL_PORT=1025
GOOGLE_CHAT_WEBHOOK=your_webhook_url  # Optional
```

### Email Configuration
- **Development**: Uses MailHog on localhost:1025
- **Production**: Configure SMTP settings in `main.py`

### Database Schema
The application uses SQLite with the following main tables:
- `users` - User accounts and authentication
- `parking_lots` - Parking location details
- `parking_spots` - Individual parking spaces
- `reservations` - Booking records
- `user_preferences` - Email notification settings

## 🎯 Usage

### Admin Features
1. **Login**: Use default admin credentials (admin/admin123)
2. **Manage Parking Lots**: Add, edit, remove parking locations
3. **User Management**: View and manage user accounts
4. **Analytics**: Access comprehensive reports and statistics
5. **System Monitoring**: View background task status

### User Features
1. **Registration**: Create new user account
2. **Browse Locations**: View available parking lots
3. **Make Reservations**: Book parking spots in real-time
4. **Track History**: View past and active bookings
5. **Email Reports**: Receive automated activity summaries

### API Endpoints

#### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - User logout

#### Parking Management
- `GET /api/parking-lots` - List all parking lots
- `POST /api/parking-lots` - Create new parking lot (admin)
- `GET /api/parking-lots/{id}/spots` - Get available spots
- `POST /api/reserve-spot` - Make a reservation

#### Analytics
- `GET /api/admin/analytics` - Dashboard statistics
- `GET /api/user/history` - User booking history
- `POST /api/export-csv` - Export user data

## 📧 Email System

### Scheduled Tasks
- **Daily Reminders**: Sent every 20 seconds (configurable)
- **Monthly Reports**: Generated every 20 seconds (configurable)
- **Test Emails**: System health checks every 20 seconds

### Email Templates
- HTML-styled responsive emails
- Personalized content based on user activity
- Parking availability notifications
- Detailed monthly statistics

## 🔍 Monitoring & Debugging

### Log Files
- `celery_worker.log` - Background task execution
- `celery_beat.log` - Scheduled task logs  
- `mailhog.log` - Email server logs

### Development Tools
- **MailHog Web UI**: http://localhost:8025
- **Redis CLI**: Monitor cache and queues
- **Flask Debug Mode**: Detailed error information

## 🚀 Deployment

### Production Checklist
1. Set `FLASK_ENV=production`
2. Configure proper SMTP server
3. Use PostgreSQL instead of SQLite
4. Set up proper Redis instance
5. Configure reverse proxy (nginx)
6. Set up SSL certificates
7. Configure proper logging
8. Set up monitoring and alerts

### Docker Deployment (Recommended)
```dockerfile
# Example Dockerfile structure
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

## 🧪 Testing

### Manual Testing
1. Start all services
2. Access frontend at http://localhost:5173
3. Register new user account
4. Create parking lot (admin)
5. Make reservation
6. Check email notifications in MailHog

### API Testing
```bash
# Test user registration
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123","email":"test@example.com"}'

# Test login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **MailHog Port Conflict**
   ```bash
   pkill -f mailhog
   ./mailhog &
   ```

2. **Redis Connection Error**
   ```bash
   redis-server --daemonize yes
   ```

3. **Celery Tasks Not Running**
   ```bash
   pkill -f celery
   celery -A main.celery worker --loglevel=info &
   celery -A main.celery beat --loglevel=info &
   ```

4. **Database Lock Error**
   ```bash
   # Check for running processes using the database
   lsof parking_lot.db
   ```

5. **Frontend Build Issues**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

## 📈 Performance Optimization

### Caching Strategy
- Redis-based caching for frequent queries
- Cache invalidation on data updates
- Configurable cache timeouts

### Database Optimization
- Indexed columns for faster queries
- Connection pooling
- Regular cleanup of expired data

### Background Processing
- Async task processing with Celery
- Rate limiting for email sending
- Batch processing for large operations

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint for JavaScript code
- Write descriptive commit messages
- Add tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Deepesh Kumar** - *Initial work* - [Deepesh1604](https://github.com/Deepesh1604)

## 🙏 Acknowledgments

- Flask community for excellent documentation
- Vue.js team for the reactive framework
- Celery contributors for background task processing
- MailHog for email testing capabilities


## 🔮 Future Enhancements

- [ ] Mobile app development (React Native)
- [ ] Payment gateway integration
- [ ] GPS-based navigation
- [ ] Real-time notifications with WebSockets
- [ ] Machine learning for demand prediction
- [ ] IoT sensor integration
- [ ] Multi-language support
- [ ] API rate limiting and throttling
- [ ] Advanced analytics dashboard
- [ ] Social login integration

---

**Made with ❤️ by Deepesh Kumar**

*ParkMate - Making parking simple, smart, and efficient!* 🅿️✨
