# app/monitoring/alerting.py
"""
Error Tracking and Alerting System
Detects error patterns and triggers alerts when thresholds are breached
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from app.security.audit_logging import AuditLog, AuditEventType, AuditSeverity
from app.models.notification import Notification, NotificationStatus


class AlertThresholds:
    """Configurable alert thresholds"""
    
    # API Performance thresholds
    ERROR_RATE_WARNING = 5.0  # 5% error rate triggers warning
    ERROR_RATE_CRITICAL = 10.0  # 10% error rate triggers critical alert
    AVG_RESPONSE_TIME_WARNING = 500  # 500ms average response time
    AVG_RESPONSE_TIME_CRITICAL = 1000  # 1000ms average response time
    
    # Error thresholds
    ERRORS_PER_HOUR_WARNING = 10
    ERRORS_PER_HOUR_CRITICAL = 50
    CRITICAL_ERRORS_THRESHOLD = 1  # Even 1 critical error triggers alert
    
    # Notification thresholds
    NOTIFICATION_SUCCESS_RATE_WARNING = 90.0  # Below 90% success
    NOTIFICATION_SUCCESS_RATE_CRITICAL = 75.0  # Below 75% success
    
    # Worker thresholds
    MIN_WORKERS_REQUIRED = 1
    MAX_TASK_QUEUE_DEPTH = 100


class AlertSeverityLevel:
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert:
    """Alert object"""
    def __init__(
        self,
        severity: str,
        category: str,
        message: str,
        details: Optional[Dict] = None,
        action_required: Optional[str] = None
    ):
        self.severity = severity
        self.category = category
        self.message = message
        self.details = details or {}
        self.action_required = action_required
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "details": self.details,
            "action_required": self.action_required,
            "timestamp": self.timestamp.isoformat()
        }


class ErrorTracker:
    """Tracks and analyzes error patterns"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger("error_tracker")
    
    def analyze_error_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze error patterns and identify recurring issues
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get all errors in time window
        errors = self.db.query(AuditLog).filter(
            and_(
                AuditLog.event_type.in_([
                    AuditEventType.API_ERROR.value,
                    AuditEventType.SYSTEM_ERROR.value
                ]),
                AuditLog.timestamp >= cutoff_time
            )
        ).all()
        
        if not errors:
            return {
                "patterns_found": 0,
                "message": "No error patterns detected"
            }
        
        # Pattern 1: Errors by endpoint
        endpoint_errors = defaultdict(list)
        for error in errors:
            if error.request_path:
                endpoint_errors[error.request_path].append({
                    "timestamp": error.timestamp,
                    "description": error.event_description,
                    "user_id": str(error.user_id) if error.user_id else None
                })
        
        # Pattern 2: Errors by user
        user_errors = defaultdict(int)
        for error in errors:
            if error.user_id:
                user_errors[str(error.user_id)] += 1
        
        # Pattern 3: Error spikes (time-based clustering)
        hourly_errors = defaultdict(int)
        for error in errors:
            hour_key = error.timestamp.strftime("%Y-%m-%d %H:00")
            hourly_errors[hour_key] += 1
        
        # Identify spike hours (>2x average)
        if hourly_errors:
            avg_errors = sum(hourly_errors.values()) / len(hourly_errors)
            spike_hours = {
                hour: count 
                for hour, count in hourly_errors.items() 
                if count > avg_errors * 2
            }
        else:
            spike_hours = {}
        
        # Pattern 4: Repeated error messages
        error_messages = defaultdict(int)
        for error in errors:
            # Extract first 100 chars of error description as pattern
            pattern = error.event_description[:100] if error.event_description else "unknown"
            error_messages[pattern] += 1
        
        # Find most common errors
        top_repeated_errors = dict(sorted(
            error_messages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5])
        
        return {
            "time_period_hours": hours,
            "total_errors": len(errors),
            "patterns_found": 4,
            "endpoint_errors": {
                endpoint: len(error_list)
                for endpoint, error_list in endpoint_errors.items()
            },
            "top_error_prone_users": dict(sorted(
                user_errors.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            "error_spike_hours": spike_hours,
            "repeated_errors": top_repeated_errors
        }
    
    def get_recent_critical_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent critical errors for immediate attention"""
        critical_errors = self.db.query(AuditLog).filter(
            and_(
                AuditLog.severity == AuditSeverity.CRITICAL.value,
                AuditLog.event_type.in_([
                    AuditEventType.API_ERROR.value,
                    AuditEventType.SYSTEM_ERROR.value,
                    AuditEventType.SECURITY_VIOLATION.value
                ])
            )
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "id": str(error.id),
                "timestamp": error.timestamp.isoformat(),
                "type": error.event_type,
                "description": error.event_description,
                "endpoint": error.request_path,
                "user_id": str(error.user_id) if error.user_id else None,
                "client_ip": error.client_ip
            }
            for error in critical_errors
        ]


class AlertManager:
    """Manages alert generation and threshold checking"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.error_tracker = ErrorTracker(db_session)
        self.thresholds = AlertThresholds()
        self.logger = logging.getLogger("alert_manager")
    
    def check_all_alerts(self) -> List[Alert]:
        """
        Check all alert conditions and return active alerts
        """
        alerts = []
        
        # Check API performance
        alerts.extend(self._check_api_performance())
        
        # Check error rates
        alerts.extend(self._check_error_rates())
        
        # Check notification system
        alerts.extend(self._check_notification_health())
        
        # Check Celery workers
        alerts.extend(self._check_celery_workers())
        
        # Check for critical errors
        alerts.extend(self._check_critical_errors())
        
        # Log alerts
        for alert in alerts:
            if alert.severity == AlertSeverityLevel.CRITICAL:
                self.logger.critical(f"ALERT: {alert.message}")
            elif alert.severity == AlertSeverityLevel.WARNING:
                self.logger.warning(f"ALERT: {alert.message}")
        
        return alerts
    
    def _check_api_performance(self) -> List[Alert]:
        """Check API performance metrics"""
        alerts = []
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        # Get recent API requests
        api_requests = self.db.query(AuditLog).filter(
            and_(
                AuditLog.event_type == AuditEventType.API_REQUEST.value,
                AuditLog.timestamp >= cutoff_time
            )
        ).all()
        
        api_errors = self.db.query(AuditLog).filter(
            and_(
                AuditLog.event_type == AuditEventType.API_ERROR.value,
                AuditLog.timestamp >= cutoff_time
            )
        ).count()
        
        if not api_requests:
            return alerts
        
        total_requests = len(api_requests)
        error_rate = (api_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Check error rate
        if error_rate >= self.thresholds.ERROR_RATE_CRITICAL:
            alerts.append(Alert(
                severity=AlertSeverityLevel.CRITICAL,
                category="api_performance",
                message=f"Critical: API error rate is {error_rate:.1f}%",
                details={"error_rate": error_rate, "threshold": self.thresholds.ERROR_RATE_CRITICAL},
                action_required="Investigate API errors immediately"
            ))
        elif error_rate >= self.thresholds.ERROR_RATE_WARNING:
            alerts.append(Alert(
                severity=AlertSeverityLevel.WARNING,
                category="api_performance",
                message=f"Warning: API error rate is {error_rate:.1f}%",
                details={"error_rate": error_rate, "threshold": self.thresholds.ERROR_RATE_WARNING},
                action_required="Monitor API errors"
            ))
        
        # Check response times
        response_times = [req.response_time_ms for req in api_requests if req.response_time_ms]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            
            if avg_response >= self.thresholds.AVG_RESPONSE_TIME_CRITICAL:
                alerts.append(Alert(
                    severity=AlertSeverityLevel.CRITICAL,
                    category="api_performance",
                    message=f"Critical: Average response time is {avg_response:.0f}ms",
                    details={"avg_response_time": avg_response, "threshold": self.thresholds.AVG_RESPONSE_TIME_CRITICAL},
                    action_required="Investigate performance bottleneck"
                ))
            elif avg_response >= self.thresholds.AVG_RESPONSE_TIME_WARNING:
                alerts.append(Alert(
                    severity=AlertSeverityLevel.WARNING,
                    category="api_performance",
                    message=f"Warning: Average response time is {avg_response:.0f}ms",
                    details={"avg_response_time": avg_response, "threshold": self.thresholds.AVG_RESPONSE_TIME_WARNING}
                ))
        
        return alerts
    
    def _check_error_rates(self) -> List[Alert]:
        """Check error rates and patterns"""
        alerts = []
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        errors_last_hour = self.db.query(AuditLog).filter(
            and_(
                AuditLog.event_type.in_([
                    AuditEventType.API_ERROR.value,
                    AuditEventType.SYSTEM_ERROR.value
                ]),
                AuditLog.timestamp >= cutoff_time
            )
        ).count()
        
        if errors_last_hour >= self.thresholds.ERRORS_PER_HOUR_CRITICAL:
            alerts.append(Alert(
                severity=AlertSeverityLevel.CRITICAL,
                category="error_rate",
                message=f"Critical: {errors_last_hour} errors in the last hour",
                details={"errors": errors_last_hour, "threshold": self.thresholds.ERRORS_PER_HOUR_CRITICAL},
                action_required="Investigate error spike immediately"
            ))
        elif errors_last_hour >= self.thresholds.ERRORS_PER_HOUR_WARNING:
            alerts.append(Alert(
                severity=AlertSeverityLevel.WARNING,
                category="error_rate",
                message=f"Warning: {errors_last_hour} errors in the last hour",
                details={"errors": errors_last_hour, "threshold": self.thresholds.ERRORS_PER_HOUR_WARNING}
            ))
        
        return alerts
    
    def _check_notification_health(self) -> List[Alert]:
        """Check notification system health"""
        alerts = []
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        total_notifications = self.db.query(Notification).filter(
            Notification.created_at >= cutoff_time
        ).count()
        
        if total_notifications == 0:
            return alerts
        
        successful = self.db.query(Notification).filter(
            and_(
                Notification.created_at >= cutoff_time,
                Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED])
            )
        ).count()
        
        success_rate = (successful / total_notifications * 100) if total_notifications > 0 else 0
        
        if success_rate < self.thresholds.NOTIFICATION_SUCCESS_RATE_CRITICAL:
            alerts.append(Alert(
                severity=AlertSeverityLevel.CRITICAL,
                category="notifications",
                message=f"Critical: Notification success rate is {success_rate:.1f}%",
                details={"success_rate": success_rate, "threshold": self.thresholds.NOTIFICATION_SUCCESS_RATE_CRITICAL},
                action_required="Check Twilio credentials and Celery worker"
            ))
        elif success_rate < self.thresholds.NOTIFICATION_SUCCESS_RATE_WARNING:
            alerts.append(Alert(
                severity=AlertSeverityLevel.WARNING,
                category="notifications",
                message=f"Warning: Notification success rate is {success_rate:.1f}%",
                details={"success_rate": success_rate, "threshold": self.thresholds.NOTIFICATION_SUCCESS_RATE_WARNING}
            ))
        
        return alerts
    
    def _check_celery_workers(self) -> List[Alert]:
        """Check Celery worker health"""
        alerts = []
        
        try:
            from app.core.celery_app import celery_app
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            
            if not stats or len(stats) < self.thresholds.MIN_WORKERS_REQUIRED:
                alerts.append(Alert(
                    severity=AlertSeverityLevel.CRITICAL,
                    category="celery",
                    message="Critical: No Celery workers are running",
                    details={"workers_running": len(stats) if stats else 0, "required": self.thresholds.MIN_WORKERS_REQUIRED},
                    action_required="Start Celery worker: .\\scripts\\start_celery_worker.bat"
                ))
        except Exception as e:
            alerts.append(Alert(
                severity=AlertSeverityLevel.CRITICAL,
                category="celery",
                message=f"Critical: Cannot connect to Celery: {str(e)}",
                action_required="Check Redis and Celery configuration"
            ))
        
        return alerts
    
    def _check_critical_errors(self) -> List[Alert]:
        """Check for any critical errors"""
        alerts = []
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        critical_errors = self.db.query(AuditLog).filter(
            and_(
                AuditLog.severity == AuditSeverity.CRITICAL.value,
                AuditLog.timestamp >= cutoff_time
            )
        ).count()
        
        if critical_errors > 0:
            alerts.append(Alert(
                severity=AlertSeverityLevel.CRITICAL,
                category="critical_errors",
                message=f"Critical: {critical_errors} critical error(s) in the last hour",
                details={"count": critical_errors},
                action_required="Review critical errors immediately"
            ))
        
        return alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all active alerts"""
        alerts = self.check_all_alerts()
        
        if not alerts:
            return {
                "status": "healthy",
                "message": "No alerts - all systems operating normally",
                "alerts": []
            }
        
        # Group by severity
        critical = [a for a in alerts if a.severity == AlertSeverityLevel.CRITICAL]
        warning = [a for a in alerts if a.severity == AlertSeverityLevel.WARNING]
        
        status = "critical" if critical else "warning"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "alert_count": len(alerts),
            "critical_count": len(critical),
            "warning_count": len(warning),
            "alerts": [alert.to_dict() for alert in alerts],
            "recommended_actions": [
                alert.action_required 
                for alert in alerts 
                if alert.action_required
            ]
        }