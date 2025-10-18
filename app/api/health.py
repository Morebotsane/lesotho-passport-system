# app/api/health.py
"""
Health check endpoints for monitoring system status
Checks database, Redis, Celery worker, and overall system health
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any
import redis
from celery.result import AsyncResult

from app.core.database import get_db
from app.core.config import settings
from app.core.celery_app import celery_app

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", status_code=status.HTTP_200_OK)
def health_check_basic():
    """
    Basic health check - just confirms API is responding
    Use this for simple uptime monitoring
    """
    return {
        "status": "healthy",
        "service": "Lesotho Passport Notification System",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/detailed", status_code=status.HTTP_200_OK)
def health_check_detailed(db: Session = Depends(get_db)):
    """
    Detailed health check - checks all system components
    Returns status of database, Redis, Celery worker, and overall system health
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    overall_healthy = True
    
    # Check Database
    db_status = _check_database(db)
    health_status["components"]["database"] = db_status
    if not db_status["healthy"]:
        overall_healthy = False
    
    # Check Redis
    redis_status = _check_redis()
    health_status["components"]["redis"] = redis_status
    if not redis_status["healthy"]:
        overall_healthy = False
    
    # Check Celery Worker
    celery_status = _check_celery()
    health_status["components"]["celery"] = celery_status
    if not celery_status["healthy"]:
        overall_healthy = False
    
    # Set overall status
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    
    # Return appropriate HTTP status code
    http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return health_status


@router.get("/database")
def health_check_database(db: Session = Depends(get_db)):
    """Check database connectivity and responsiveness"""
    return _check_database(db)


@router.get("/redis")
def health_check_redis():
    """Check Redis connectivity and responsiveness"""
    return _check_redis()


@router.get("/celery")
def health_check_celery():
    """Check Celery worker status"""
    return _check_celery()


def _check_database(db: Session) -> Dict[str, Any]:
    """
    Check database health
    Tests: Connection, query execution, table existence
    """
    try:
        # Test basic query execution
        start_time = datetime.utcnow()
        result = db.execute(text("SELECT 1"))
        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Test table existence (check notifications table)
        table_check = db.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'notifications')"
        ))
        tables_exist = table_check.scalar()
        
        # Get connection pool stats
        pool_size = db.bind.pool.size()
        pool_checked_out = db.bind.pool.checkedout()
        
        return {
            "healthy": True,
            "status": "connected",
            "response_time_ms": round(query_time, 2),
            "tables_exist": tables_exist,
            "connection_pool": {
                "size": pool_size,
                "checked_out": pool_checked_out,
                "available": pool_size - pool_checked_out
            },
            "database_url": settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else "configured"
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "status": "disconnected",
            "error": str(e),
            "error_type": type(e).__name__
        }


def _check_redis() -> Dict[str, Any]:
    """
    Check Redis health
    Tests: Connection, ping, memory usage
    """
    try:
        # Connect to Redis
        redis_client = redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            decode_responses=True
        )
        
        # Test ping
        start_time = datetime.utcnow()
        redis_client.ping()
        ping_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Get Redis info
        info = redis_client.info()
        
        return {
            "healthy": True,
            "status": "connected",
            "response_time_ms": round(ping_time, 2),
            "version": info.get("redis_version", "unknown"),
            "memory_used": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "broker_url": settings.CELERY_BROKER_URL.replace(
                settings.CELERY_BROKER_URL.split('@')[0].split('//')[1] if '@' in settings.CELERY_BROKER_URL else '',
                '***'
            )
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "status": "disconnected",
            "error": str(e),
            "error_type": type(e).__name__
        }


def _check_celery() -> Dict[str, Any]:
    """
    Check Celery worker health
    Tests: Worker connectivity, active tasks, queue stats
    """
    try:
        # Check active workers
        inspect = celery_app.control.inspect()
        
        # Get active workers
        active_workers = inspect.active()
        stats = inspect.stats()
        
        if not active_workers:
            return {
                "healthy": False,
                "status": "no_workers",
                "message": "No Celery workers are running",
                "workers": []
            }
        
        # Count active tasks across all workers
        active_tasks_count = sum(len(tasks) for tasks in active_workers.values())
        
        # Get worker details
        worker_details = []
        for worker_name, worker_stats in (stats or {}).items():
            worker_details.append({
                "name": worker_name,
                "status": "active",
                "pool": worker_stats.get("pool", {}).get("implementation", "unknown"),
                "max_concurrency": worker_stats.get("pool", {}).get("max-concurrency", 0)
            })
        
        return {
            "healthy": True,
            "status": "running",
            "workers": worker_details,
            "worker_count": len(active_workers),
            "active_tasks": active_tasks_count,
            "queues": {
                "default": "operational"
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "status": "unreachable",
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Could not connect to Celery workers. Is the worker running?"
        }


@router.get("/startup-checklist")
def startup_checklist(db: Session = Depends(get_db)):
    """
    Comprehensive startup checklist for system administrators
    Verifies all required services and configurations
    """
    checklist = {
        "timestamp": datetime.utcnow().isoformat(),
        "checks": []
    }
    
    # Check 1: Database
    db_check = _check_database(db)
    checklist["checks"].append({
        "component": "PostgreSQL Database",
        "status": "PASS" if db_check["healthy"] else "FAIL",
        "details": db_check
    })
    
    # Check 2: Redis
    redis_check = _check_redis()
    checklist["checks"].append({
        "component": "Redis Message Broker",
        "status": "PASS" if redis_check["healthy"] else "FAIL",
        "details": redis_check
    })
    
    # Check 3: Celery
    celery_check = _check_celery()
    checklist["checks"].append({
        "component": "Celery Background Worker",
        "status": "PASS" if celery_check["healthy"] else "FAIL",
        "details": celery_check
    })
    
    # Check 4: Configuration
    config_check = {
        "twilio_configured": bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN),
        "database_url_set": bool(settings.DATABASE_URL),
        "redis_url_set": bool(settings.CELERY_BROKER_URL),
        "environment": settings.ENVIRONMENT
    }
    checklist["checks"].append({
        "component": "Configuration",
        "status": "PASS" if all(config_check.values()) else "FAIL",
        "details": config_check
    })
    
    # Overall status
    all_passed = all(check["status"] == "PASS" for check in checklist["checks"])
    checklist["overall_status"] = "ALL SYSTEMS OPERATIONAL" if all_passed else "ISSUES DETECTED"
    checklist["ready_for_production"] = all_passed
    
    return checklist