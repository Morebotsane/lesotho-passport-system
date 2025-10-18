# app/api/metrics.py
"""
Performance Metrics API Endpoints
Provides access to system performance data and statistics
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.monitoring.metrics import MetricsCollector
from app.monitoring.alerting import AlertManager, ErrorTracker

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/overview")
def get_metrics_overview(db: Session = Depends(get_db)):
    """
    Comprehensive system metrics overview
    Includes API performance, errors, notifications, and Celery status
    """
    collector = MetricsCollector(db)
    return collector.get_system_overview()


@router.get("/api-performance")
def get_api_performance(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze (1-168)"),
    db: Session = Depends(get_db)
):
    """
    API performance metrics for the specified time period
    - Response times (avg, min, max)
    - Request counts
    - Error rates
    - Slow requests
    - Top endpoints
    """
    collector = MetricsCollector(db)
    return collector.get_api_performance_metrics(hours=hours)


@router.get("/errors")
def get_error_statistics(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze (1-168)"),
    db: Session = Depends(get_db)
):
    """
    Error statistics and patterns
    - Total errors
    - Errors by severity
    - Critical errors
    - Most error-prone endpoints
    """
    collector = MetricsCollector(db)
    return collector.get_error_statistics(hours=hours)


@router.get("/notifications")
def get_notification_metrics(
    days: int = Query(7, ge=1, le=30, description="Days to analyze (1-30)"),
    db: Session = Depends(get_db)
):
    """
    SMS notification performance metrics
    - Total sent
    - Success rate
    - Retry statistics
    - Delivery times
    """
    collector = MetricsCollector(db)
    return collector.get_notification_metrics(days=days)


@router.get("/celery")
def get_celery_metrics(db: Session = Depends(get_db)):
    """
    Celery worker and task metrics
    - Worker status
    - Active tasks
    - Task queue depth
    """
    collector = MetricsCollector(db)
    return collector.get_celery_task_metrics()


@router.get("/dashboard")
def metrics_dashboard(db: Session = Depends(get_db)):
    """
    Formatted metrics dashboard suitable for monitoring displays
    Provides key metrics in an easy-to-read format
    """
    collector = MetricsCollector(db)
    overview = collector.get_system_overview()
    
    # Format for display
    api = overview.get("api_performance", {})
    errors = overview.get("error_statistics", {})
    notifications = overview.get("notifications", {})
    celery = overview.get("celery_workers", {})
    
    return {
        "generated_at": overview["timestamp"],
        "summary": {
            "api_requests_24h": api.get("total_requests", 0),
            "api_error_rate": f"{api.get('error_rate_percent', 0)}%",
            "avg_response_time": f"{api.get('response_times', {}).get('average_ms', 0)}ms",
            "notifications_7d": notifications.get("total_notifications", 0),
            "notification_success_rate": f"{notifications.get('success_rate_percent', 0)}%",
            "celery_workers": celery.get("worker_count", 0),
            "active_tasks": celery.get("total_active_tasks", 0)
        },
        "alerts": _generate_alerts(api, errors, notifications, celery),
        "detailed_metrics": overview
    }


def _generate_alerts(api, errors, notifications, celery) -> list:
    """Generate alerts based on metric thresholds"""
    alerts = []
    
    # High error rate
    error_rate = api.get("error_rate_percent", 0)
    if error_rate > 5:
        alerts.append({
            "severity": "warning",
            "message": f"High API error rate: {error_rate}%",
            "threshold": "5%"
        })
    
    # Slow response times
    avg_response = api.get("response_times", {}).get("average_ms", 0)
    if avg_response > 500:
        alerts.append({
            "severity": "warning",
            "message": f"Slow API responses: {avg_response}ms average",
            "threshold": "500ms"
        })
    
    # No Celery workers
    if celery.get("worker_count", 0) == 0:
        alerts.append({
            "severity": "critical",
            "message": "No Celery workers running",
            "action": "Start Celery worker immediately"
        })
    
    # Low notification success rate
    success_rate = notifications.get("success_rate_percent", 100)
    if success_rate < 90:
        alerts.append({
            "severity": "warning",
            "message": f"Low notification success rate: {success_rate}%",
            "threshold": "90%"
        })
    
    if not alerts:
        alerts.append({
            "severity": "info",
            "message": "All systems operating within normal parameters"
        })
    
    return alerts

@router.get("/errors/patterns")
def get_error_patterns(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze (1-168)"),
    db: Session = Depends(get_db)
):
    """
    Analyze error patterns and identify recurring issues
    - Errors by endpoint
    - Errors by user
    - Error spikes (time-based)
    - Repeated error messages
    """
    tracker = ErrorTracker(db)
    return tracker.analyze_error_patterns(hours=hours)


@router.get("/errors/critical")
def get_critical_errors(
    limit: int = Query(10, ge=1, le=50, description="Number of errors to return"),
    db: Session = Depends(get_db)
):
    """
    Get recent critical errors requiring immediate attention
    """
    tracker = ErrorTracker(db)
    return {
        "critical_errors": tracker.get_recent_critical_errors(limit=limit),
        "message": "Review these errors immediately"
    }


@router.get("/alerts")
def get_active_alerts(db: Session = Depends(get_db)):
    """
    Get all active system alerts
    Checks thresholds and returns actionable alerts
    """
    manager = AlertManager(db)
    return manager.get_alert_summary()


@router.get("/alerts/check")
def check_alert_status(db: Session = Depends(get_db)):
    """
    Quick alert status check
    Returns simple status: healthy, warning, or critical
    """
    manager = AlertManager(db)
    summary = manager.get_alert_summary()
    
    return {
        "status": summary["status"],
        "has_critical_alerts": summary["critical_count"] > 0,
        "has_warnings": summary["warning_count"] > 0,
        "total_alerts": summary["alert_count"],
        "message": summary["message"] if "message" in summary else None
    }