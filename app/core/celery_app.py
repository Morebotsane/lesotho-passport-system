# app/core/celery_app.py
"""
Celery application configuration for background task processing.
Uses Redis as both message broker and result backend.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "lesotho_passport_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.notification_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Maseru",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Rate limiting
    task_default_rate_limit="100/m",
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Periodic task schedule (for future use)
"""
celery_app.conf.beat_schedule = {
    "cleanup-expired-audit-logs": {
        "task": "app.tasks.audit_tasks.cleanup_old_audit_logs",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
    "generate-daily-report": {
        "task": "app.tasks.report_tasks.generate_daily_statistics",
        "schedule": crontab(hour=23, minute=0),  # Run at 11 PM daily
    },
}
"""

# Task routing (optional - for advanced queue management)
celery_app.conf.task_routes = {
    "app.tasks.notification_tasks.*": {"queue": "notifications"},
    "app.tasks.report_tasks.*": {"queue": "reports"},
    "app.tasks.audit_tasks.*": {"queue": "maintenance"},
}