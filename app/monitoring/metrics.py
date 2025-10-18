# app/monitoring/metrics.py
"""
Performance Metrics System for Lesotho Passport Notification System
Tracks API performance, error rates, Celery tasks, and system health
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import redis

from app.database import Base
from app.core.config import settings
from app.models.notification import Notification, NotificationStatus
from app.security.audit_logging import AuditLog, AuditEventType, AuditSeverity


class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self, db_session: Session, redis_client: redis.Redis = None):
        self.db = db_session
        self.redis_client = redis_client or redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            decode_responses=True
        )
    
    def get_api_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get API performance metrics for the last N hours
        Analyzes response times, request counts, and error rates
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query audit logs for API requests
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
        ).all()
        
        # Calculate statistics
        total_requests = len(api_requests)
        total_errors = len(api_errors)
        
        if total_requests == 0:
            return {
                "time_period_hours": hours,
                "message": "No API requests in this time period"
            }
        
        # Response time statistics
        response_times = [req.response_time_ms for req in api_requests if req.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # Slow requests (>1000ms)
        slow_requests = [req for req in api_requests if req.response_time_ms and req.response_time_ms > 1000]
        
        # Requests by endpoint
        endpoint_stats = defaultdict(lambda: {"count": 0, "errors": 0, "total_time": 0})
        for req in api_requests:
            endpoint = req.request_path or "unknown"
            endpoint_stats[endpoint]["count"] += 1
            endpoint_stats[endpoint]["total_time"] += req.response_time_ms or 0
        
        for err in api_errors:
            endpoint = err.request_path or "unknown"
            endpoint_stats[endpoint]["errors"] += 1
        
        # Calculate averages per endpoint
        endpoint_summary = {}
        for endpoint, stats in endpoint_stats.items():
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            error_rate = (stats["errors"] / stats["count"] * 100) if stats["count"] > 0 else 0
            endpoint_summary[endpoint] = {
                "request_count": stats["count"],
                "error_count": stats["errors"],
                "error_rate_percent": round(error_rate, 2),
                "avg_response_time_ms": round(avg_time, 2)
            }
        
        # Sort by request count
        top_endpoints = dict(sorted(
            endpoint_summary.items(),
            key=lambda x: x[1]["request_count"],
            reverse=True
        )[:10])
        
        return {
            "time_period_hours": hours,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate_percent": round((total_errors / total_requests * 100), 2),
            "response_times": {
                "average_ms": round(avg_response_time, 2),
                "minimum_ms": round(min_response_time, 2),
                "maximum_ms": round(max_response_time, 2)
            },
            "slow_requests": {
                "count": len(slow_requests),
                "threshold_ms": 1000,
                "percentage": round((len(slow_requests) / total_requests * 100), 2)
            },
            "top_endpoints": top_endpoints,
            "requests_per_hour": round(total_requests / hours, 2)
        }
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze error patterns and types
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get all errors
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
                "time_period_hours": hours,
                "total_errors": 0,
                "message": "No errors in this time period"
            }
        
        # Error by severity
        severity_counts = defaultdict(int)
        for error in errors:
            severity_counts[error.severity] += 1
        
        # Recent critical errors
        critical_errors = [
            {
                "timestamp": err.timestamp.isoformat(),
                "description": err.event_description,
                "endpoint": err.request_path,
                "user_id": str(err.user_id) if err.user_id else None
            }
            for err in errors
            if err.severity == AuditSeverity.CRITICAL.value
        ][:10]
        
        # Error by endpoint
        endpoint_errors = defaultdict(int)
        for error in errors:
            if error.request_path:
                endpoint_errors[error.request_path] += 1
        
        most_error_prone = dict(sorted(
            endpoint_errors.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5])
        
        return {
            "time_period_hours": hours,
            "total_errors": len(errors),
            "errors_per_hour": round(len(errors) / hours, 2),
            "by_severity": dict(severity_counts),
            "critical_errors": critical_errors,
            "most_error_prone_endpoints": most_error_prone
        }
    
    def get_notification_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get SMS notification performance metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Total notifications
        total = self.db.query(Notification).filter(
            Notification.created_at >= cutoff_time
        ).count()
        
        if total == 0:
            return {
                "time_period_days": days,
                "total_notifications": 0,
                "message": "No notifications in this time period"
            }
        
        # By status
        status_counts = {}
        for status in NotificationStatus:
            count = self.db.query(Notification).filter(
                and_(
                    Notification.status == status,
                    Notification.created_at >= cutoff_time
                )
            ).count()
            status_counts[status.value] = count
        
        # Success rate
        sent = status_counts.get('sent', 0) + status_counts.get('delivered', 0)
        success_rate = (sent / total * 100) if total > 0 else 0
        
        # Retry statistics
        retried = self.db.query(Notification).filter(
            and_(
                Notification.retry_count > 0,
                Notification.created_at >= cutoff_time
            )
        ).count()
        
        # Average delivery time (sent_at - created_at)
        notifications_with_times = self.db.query(Notification).filter(
            and_(
                Notification.sent_at.isnot(None),
                Notification.created_at >= cutoff_time
            )
        ).all()
        
        if notifications_with_times:
            delivery_times = [
                (n.sent_at - n.created_at).total_seconds()
                for n in notifications_with_times
            ]
            avg_delivery_time = sum(delivery_times) / len(delivery_times)
        else:
            avg_delivery_time = 0
        
        return {
            "time_period_days": days,
            "total_notifications": total,
            "by_status": status_counts,
            "success_rate_percent": round(success_rate, 2),
            "retry_statistics": {
                "notifications_retried": retried,
                "retry_rate_percent": round((retried / total * 100), 2)
            },
            "average_delivery_time_seconds": round(avg_delivery_time, 2),
            "notifications_per_day": round(total / days, 2)
        }
    
    def get_celery_task_metrics(self) -> Dict[str, Any]:
        """
        Get Celery worker and task performance metrics
        """
        from app.core.celery_app import celery_app
        
        try:
            inspect = celery_app.control.inspect()
            
            # Get worker stats
            stats = inspect.stats()
            active_tasks = inspect.active()
            reserved_tasks = inspect.reserved()
            
            if not stats:
                return {
                    "status": "no_workers",
                    "message": "No Celery workers are running"
                }
            
            # Aggregate worker information
            worker_info = []
            total_active = 0
            total_reserved = 0
            
            for worker_name, worker_stats in stats.items():
                active_count = len(active_tasks.get(worker_name, [])) if active_tasks else 0
                reserved_count = len(reserved_tasks.get(worker_name, [])) if reserved_tasks else 0
                
                total_active += active_count
                total_reserved += reserved_count
                
                worker_info.append({
                    "name": worker_name,
                    "status": "active",
                    "pool": worker_stats.get("pool", {}).get("implementation", "unknown"),
                    "active_tasks": active_count,
                    "reserved_tasks": reserved_count,
                    "total_processed": worker_stats.get("total", {})
                })
            
            return {
                "status": "operational",
                "worker_count": len(stats),
                "total_active_tasks": total_active,
                "total_reserved_tasks": total_reserved,
                "workers": worker_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get Celery metrics: {str(e)}"
            }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive system overview
        Combines all metrics for dashboard view
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "api_performance": self.get_api_performance_metrics(hours=24),
            "error_statistics": self.get_error_statistics(hours=24),
            "notifications": self.get_notification_metrics(days=7),
            "celery_workers": self.get_celery_task_metrics()
        }