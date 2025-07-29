#!/usr/bin/env python3

from celery import Celery
from celery.schedules import crontab

# Create the Celery app
celery_app = Celery('parkmate')

# Configure Celery
celery_app.conf.update(
    broker_url='redis://localhost:6379/2',
    result_backend='redis://localhost:6379/1',
    timezone='Asia/Kolkata',
    beat_schedule={
        'cleanup-expired-reservations': {
            'task': 'main.cleanup_expired_reservations',
            'schedule': 3600.0,  # Every hour
        },
        'generate-daily-report': {
            'task': 'main.generate_daily_report',
            'schedule': 86400.0,  # Every 24 hours
        },
        'optimize-parking-allocation': {
            'task': 'main.optimize_parking_allocation',
            'schedule': 21600.0,  # Every 6 hours
        },
        'send-parking-reminders': {
            'task': 'main.send_parking_reminders',
            'schedule': 900.0,  # Every 15 minutes
        },
        'daily-mail-reminder': {
            'task': 'main.send_daily_reminders',
            'schedule': crontab(minute=0, hour=18)  # Daily at 6 PM
        },
        'monthly-mail-report': {
            'task': 'main.generate_monthly_activity_report',
            'schedule': crontab(minute=0, hour=0, day_of_month=1)  # Monthly on 1st at midnight
        }
    }
)

if __name__ == '__main__':
    celery_app.start()
