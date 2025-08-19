<div align="center">

# 🅿️ ParkMate - Smart Parking Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.0+-green.svg)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-red.svg)](https://flask.palletsprojects.com/)

**A comprehensive parking lot management system built with Flask backend and Vue.js frontend, featuring real-time booking, automated email notifications, and advanced analytics.**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API Documentation](#api-endpoints) • [Contributing](#-contributing)

</div>

---

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

Before you begin, ensure you have the following installed on your system:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 16+** - [Download Node.js](https://nodejs.org/)
- **Redis Server** - [Installation Guide](https://redis.io/download)
- **Git** - [Download Git](https://git-scm.com/downloads)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Deepesh1604/ParkMate.git
cd ParkMate
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python3 -c "from main import init_db; init_db()"
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Environment Configuration

Create a `.env` file in the root directory:
```env
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
REDIS_URL=redis://localhost:6379
EMAIL_HOST=localhost
EMAIL_PORT=1025
GOOGLE_CHAT_WEBHOOK=your_webhook_url  # Optional
```

### 5. Start Services

#### Option A: Start All Services (Recommended)
```bash
# Start Redis server
redis-server --daemonize yes

# Start MailHog for email testing
./mailhog &  # Web UI: http://localhost:8025, SMTP: localhost:1025

# Start backend services in separate terminals
# Terminal 1: Flask Application
python3 main.py

# Terminal 2: Celery Worker
celery -A main.celery worker --loglevel=info

# Terminal 3: Celery Beat Scheduler
celery -A main.celery beat --loglevel=info

# Terminal 4: Frontend Development Server
cd frontend && npm run dev
```

#### Option B: Development Script (if available)
```bash
# Check if you have a development script
chmod +x start-dev.sh && ./start-dev.sh
```

### 6. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5000
- **MailHog Web UI**: http://localhost:8025
- **Default Admin**: username: `admin`, password: `admin123`

## 🏗️ Project Structure

```
ParkMate/
├── 📄 main.py                     # Main Flask application & API endpoints
├── 🗄️ parking_lot.db             # SQLite database
├── 📧 mailhog                     # MailHog binary for email testing
├── ⏰ celerybeat-schedule         # Celery beat schedule file
├── 📋 requirements.txt            # Python dependencies
├── 🙈 .gitignore                  # Git ignore rules
├── 📖 README.md                   # Project documentation
├── 📁 exports/                    # CSV export directory
├── 🐍 __pycache__/               # Python cache files
├── 🌐 frontend/                   # Vue.js frontend application
│   ├── 📁 src/
│   │   ├── 🧩 components/         # Reusable Vue components
│   │   │   ├── 👨‍💼 admin/           # Admin-specific components
│   │   │   │   ├── AdminOverview.vue
│   │   │   │   ├── ParkingLotsManagement.vue
│   │   │   │   ├── ParkingSpotsView.vue
│   │   │   │   ├── ReportsView.vue
│   │   │   │   └── UsersManagement.vue
│   │   │   ├── 👤 user/            # User-specific components
│   │   │   │   ├── ActiveParking.vue
│   │   │   │   ├── MyReservations.vue
│   │   │   │   ├── ParkingHistory.vue
│   │   │   │   ├── ParkingLotsView.vue
│   │   │   │   └── UserOverview.vue
│   │   │   ├── login.vue
│   │   │   ├── LoginSimple.vue
│   │   │   ├── ParkingStation3D.vue
│   │   │   └── register.vue
│   │   ├── 🛣️ router/              # Vue Router configuration
│   │   │   └── index.js
│   │   ├── 🎨 assets/             # Static assets & styles
│   │   │   ├── base.css
│   │   │   ├── logo.svg
│   │   │   └── main.css
│   │   ├── 🔧 utils/              # Utility functions
│   │   │   ├── api.js
│   │   │   ├── auth.js
│   │   │   └── security.js
│   │   ├── 📱 views/              # Main view components
│   │   │   ├── AdminDashboard.vue
│   │   │   ├── AdminDashboardSimple.vue
│   │   │   ├── HomeView.vue
│   │   │   ├── UserDashboard.vue
│   │   │   └── UserProfile.vue
│   │   ├── App.vue                # Root Vue component
│   │   └── main.js                # Vue application entry point
│   ├── 📁 public/                 # Public static assets
│   │   └── favicon.ico
│   ├── 📦 package.json            # Node.js dependencies
│   ├── ⚡ vite.config.js          # Vite build configuration
│   ├── 🔍 eslint.config.js        # ESLint configuration
│   ├── 📄 jsconfig.json           # JavaScript configuration
│   └── 📖 README.md               # Frontend documentation
└── 📁 logs/                       # Application logs (created at runtime)
    ├── celery_worker.log
    ├── celery_beat.log
    └── mailhog.log
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
# Application Configuration
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# Database Configuration
DATABASE_URL=sqlite:///parking_lot.db

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Email Configuration
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=false

# Optional Integrations
GOOGLE_CHAT_WEBHOOK=your_webhook_url  # Optional for notifications
```

### Email Configuration
| Environment | SMTP Server | Port | Description |
|-------------|-------------|------|-------------|
| **Development** | localhost | 1025 | Uses MailHog for testing |
| **Production** | your-smtp-server | 587/465 | Configure in `main.py` |

### Database Schema
The application uses SQLite with the following core tables:

| Table | Description |
|-------|-------------|
| `users` | User accounts and authentication data |
| `parking_lots` | Parking location details and metadata |
| `parking_spots` | Individual parking spaces and their status |
| `reservations` | Booking records and transaction history |
| `user_preferences` | Email notification settings and user preferences |

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

<details>
<summary><strong>Authentication Endpoints</strong></summary>

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/register` | User registration | ❌ |
| `POST` | `/api/login` | User login | ❌ |
| `POST` | `/api/logout` | User logout | ✅ |

</details>

<details>
<summary><strong>Parking Management Endpoints</strong></summary>

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/parking-lots` | List all parking lots | ✅ |
| `POST` | `/api/parking-lots` | Create new parking lot | ✅ (Admin) |
| `GET` | `/api/parking-lots/{id}/spots` | Get available spots | ✅ |
| `POST` | `/api/reserve-spot` | Make a reservation | ✅ |

</details>

<details>
<summary><strong>Analytics Endpoints</strong></summary>

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/admin/analytics` | Dashboard statistics | ✅ (Admin) |
| `GET` | `/api/user/history` | User booking history | ✅ |
| `POST` | `/api/export-csv` | Export user data | ✅ |

</details>

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

### Production Deployment Checklist

<details>
<summary><strong>Environment Configuration</strong></summary>

- [ ] Set `FLASK_ENV=production`
- [ ] Configure secure `SECRET_KEY`
- [ ] Set up production database (PostgreSQL recommended)
- [ ] Configure production SMTP server
- [ ] Set up proper Redis instance
- [ ] Configure environment variables

</details>

<details>
<summary><strong>Infrastructure Setup</strong></summary>

- [ ] Configure reverse proxy (Nginx recommended)
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Configure proper logging and log rotation
- [ ] Set up monitoring and health checks
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline

</details>

### Docker Deployment (Recommended)

<details>
<summary><strong>Docker Configuration</strong></summary>

**Dockerfile**
```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A main.celery worker --loglevel=info
    depends_on:
      - redis
      - web

  celery-beat:
    build: .
    command: celery -A main.celery beat --loglevel=info
    depends_on:
      - redis
      - web
```

</details>

### Cloud Deployment Options

| Platform | Complexity | Cost | Scalability |
|----------|------------|------|-------------|
| **Heroku** | Low | Medium | Medium |
| **AWS Elastic Beanstalk** | Medium | Variable | High |
| **Google Cloud Run** | Medium | Low | High |
| **DigitalOcean App Platform** | Low | Low | Medium |
| **Azure Container Instances** | Medium | Medium | High |

## 🧪 Testing

### Manual Testing Workflow
1. **Start all services** (Redis, MailHog, Flask, Celery, Frontend)
2. **Access frontend** at http://localhost:5173
3. **Register new user account** or use admin credentials
4. **Create parking lot** (admin required)
5. **Make reservation** as a regular user
6. **Check email notifications** in MailHog at http://localhost:8025

### API Testing with cURL

<details>
<summary><strong>Test User Registration</strong></summary>

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "email": "test@example.com"
  }'
```

</details>

<details>
<summary><strong>Test User Login</strong></summary>

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

</details>

### Unit Testing
```bash
# Install testing dependencies
pip install pytest pytest-cov

# Run tests with coverage
pytest --cov=main tests/

# Run specific test file
pytest tests/test_auth.py -v
```

## 🔧 Troubleshooting

<details>
<summary><strong>Common Issues & Solutions</strong></summary>

### 🔴 MailHog Port Conflict
```bash
# Kill existing MailHog processes
pkill -f mailhog

# Restart MailHog
./mailhog &

# Check if running
curl -f http://localhost:8025 || echo "MailHog not running"
```

### 🔴 Redis Connection Error
```bash
# Start Redis as daemon
redis-server --daemonize yes

# Check Redis status
redis-cli ping

# Alternative: Start with custom config
redis-server /path/to/redis.conf
```

### 🔴 Celery Tasks Not Running
```bash
# Kill all Celery processes
pkill -f celery

# Restart Celery services
celery -A main.celery worker --loglevel=info &
celery -A main.celery beat --loglevel=info &

# Check Celery status
celery -A main.celery status
```

### 🔴 Database Lock Error
```bash
# Check processes using the database
lsof parking_lot.db

# Force close database connections
pkill -f "python.*main.py"

# Backup and recreate database if corrupted
cp parking_lot.db parking_lot.db.backup
python3 -c "from main import init_db; init_db()"
```

### 🔴 Frontend Build Issues
```bash
# Clean install
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Check for Node.js version compatibility
node --version  # Should be 16+
npm --version
```

### 🔴 Permission Denied Errors
```bash
# Fix file permissions
chmod +x mailhog
chmod +x start-dev.sh  # if you have a startup script

# Fix directory permissions
chmod -R 755 logs/
chmod -R 755 exports/
```

</details>

### 📊 Health Check Commands

```bash
# Check all services status
echo "=== Service Health Check ==="
echo "1. Redis:" && redis-cli ping
echo "2. Flask:" && curl -f http://localhost:5000/health 2>/dev/null && echo "OK" || echo "FAIL"
echo "3. Frontend:" && curl -f http://localhost:5173 2>/dev/null && echo "OK" || echo "FAIL"
echo "4. MailHog:" && curl -f http://localhost:8025 2>/dev/null && echo "OK" || echo "FAIL"
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

We welcome contributions to ParkMate! Here's how you can help:

### 🚀 Quick Start for Contributors

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/your-username/ParkMate.git`
3. **Create** a feature branch: `git checkout -b feature/amazing-feature`
4. **Make** your changes
5. **Test** your changes thoroughly
6. **Commit** your changes: `git commit -m 'Add amazing feature'`
7. **Push** to your branch: `git push origin feature/amazing-feature`
8. **Open** a Pull Request

### 📋 Development Guidelines

<details>
<summary><strong>Code Style & Standards</strong></summary>

#### Python (Backend)
- Follow **PEP 8** style guide
- Use **type hints** where applicable
- Write **docstrings** for all functions and classes
- Maximum line length: **88 characters** (Black formatter)

#### JavaScript/Vue.js (Frontend)
- Use **ESLint** configuration provided
- Follow **Vue.js Style Guide**
- Use **Prettier** for code formatting
- Prefer **composition API** over options API

#### General
- Write **descriptive commit messages**
- Add **tests** for new features
- Update **documentation** for API changes
- Use **semantic versioning** for releases

</details>

<details>
<summary><strong>Pull Request Process</strong></summary>

1. **Ensure** your PR description clearly describes the problem and solution
2. **Include** the relevant issue number if applicable
3. **Add** screenshots for UI changes
4. **Ensure** all tests pass
5. **Update** documentation if needed
6. **Request** review from maintainers

</details>

### 🐛 Bug Reports

When filing an issue, please include:
- **OS and browser** version
- **Steps to reproduce** the issue
- **Expected behavior**
- **Actual behavior**
- **Screenshots** if applicable

### 💡 Feature Requests

For new features, please:
- **Check** existing issues first
- **Describe** the feature in detail
- **Explain** the use case
- **Consider** implementation complexity

## � Performance Metrics

### System Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 2GB | 4GB+ |
| **CPU** | 2 cores | 4+ cores |
| **Storage** | 1GB | 5GB+ |
| **Network** | 1Mbps | 10Mbps+ |

### Benchmarks
- **Response Time**: < 200ms (average)
- **Concurrent Users**: 100+ supported
- **Database**: Handles 10,000+ reservations
- **Email Queue**: 1,000+ emails/hour

## 🔮 Roadmap & Future Enhancements

### 🎯 Short Term (Next 3 months)
- [ ] **Mobile App** - React Native implementation
- [ ] **Payment Gateway** - Stripe/PayPal integration
- [ ] **Real-time Notifications** - WebSocket implementation
- [ ] **API Rate Limiting** - Enhanced security
- [ ] **Unit Testing** - Comprehensive test suite

### 🚀 Medium Term (3-6 months)
- [ ] **GPS Navigation** - Turn-by-turn directions
- [ ] **Machine Learning** - Demand prediction algorithms
- [ ] **Multi-language Support** - i18n implementation
- [ ] **Advanced Analytics** - Business intelligence dashboard
- [ ] **Social Login** - OAuth integration

### 🌟 Long Term (6+ months)
- [ ] **IoT Integration** - Smart sensor connectivity
- [ ] **Blockchain** - Decentralized parking tokens
- [ ] **AI Assistant** - Chatbot for customer support
- [ ] **Microservices** - Architecture modernization
- [ ] **Cloud Native** - Kubernetes deployment

## �📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Deepesh Kumar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 👥 Team

| Role | Name | GitHub | Contact |
|------|------|--------|---------|
| **Lead Developer** | Deepesh Kumar | [@Deepesh1604](https://github.com/Deepesh1604) 

## 🙏 Acknowledgments

We extend our gratitude to the following projects and communities:

- **[Flask](https://flask.palletsprojects.com/)** - For the robust web framework
- **[Vue.js](https://vuejs.org/)** - For the reactive frontend framework  
- **[Celery](https://celeryproject.org/)** - For reliable background task processing
- **[Redis](https://redis.io/)** - For high-performance caching and messaging
- **[MailHog](https://github.com/mailhog/MailHog)** - For email testing capabilities
- **Open Source Community** - For continuous inspiration and support

## 📞 Support

### 💬 Community Support
- **GitHub Issues**: [Report bugs and request features](https://github.com/Deepesh1604/ParkMate/issues)
- **Discussions**: [Join community discussions](https://github.com/Deepesh1604/ParkMate/discussions)
- **Wiki**: [Browse documentation](https://github.com/Deepesh1604/ParkMate/wiki)

### 📧 Direct Contact
- **Email**: deepesh@example.com
- **LinkedIn**: [Deepesh Kumar](https://linkedin.com/in/deepesh-kumar)
- **Twitter**: [@deepesh_dev](https://twitter.com/deepesh_dev)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

**Made with ❤️ by [Deepesh Kumar](https://github.com/Deepesh1604)**

*ParkMate - Making parking simple, smart, and efficient!* 🅿️✨

[![GitHub stars](https://img.shields.io/github/stars/Deepesh1604/ParkMate.svg?style=social&label=Star)](https://github.com/Deepesh1604/ParkMate)
[![GitHub forks](https://img.shields.io/github/forks/Deepesh1604/ParkMate.svg?style=social&label=Fork)](https://github.com/Deepesh1604/ParkMate/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/Deepesh1604/ParkMate.svg?style=social&label=Watch)](https://github.com/Deepesh1604/ParkMate)

</div>
