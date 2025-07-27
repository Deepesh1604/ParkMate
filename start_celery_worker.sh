#!/bin/bash
# Celery Worker Start Script for ParkMate

echo "🚀 Starting ParkMate Email Service..."

# Load environment variables if .env file exists
if [ -f .env ]; then
    echo "📧 Loading email configuration from .env file..."
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
    echo "✅ Email Username: $EMAIL_USERNAME"
else
    echo "⚠️  No .env file found. Please create one with your email credentials."
    echo "📋 Copy .env.example to .env and update with your Gmail credentials"
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis server is not running. Starting Redis..."
    sudo systemctl start redis-server
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis server started successfully"
    else
        echo "❌ Failed to start Redis server. Please check your Redis installation."
        exit 1
    fi
else
    echo "✅ Redis server is already running"
fi

# Start Celery worker
echo "🔄 Starting Celery worker for background email tasks..."
echo "📧 Email service will handle: welcome emails, daily reminders, monthly reports, CSV exports"
echo ""
echo "Press Ctrl+C to stop the worker"
echo "==========================================="

# Use solo pool for single-threaded operation (good for development)
celery -A main.celery worker --loglevel=info --pool=solo --concurrency=1
