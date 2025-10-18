# app/api/officer_dashboard.py
"""
Officer Dashboard API endpoints
Provides administrative interface for passport officers
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.api.deps import get_current_officer, get_current_admin, get_db
from app.models.user import User
from app.models.notification import AlertSeverity
from app.services.officer_service import OfficerService
from app.models.passport_application import PassportApplication
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/overview")
def get_dashboard_overview(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer)
) -> Any:
    """
    Get comprehensive dashboard overview (Officers/Admins only)
    
    Returns key metrics, status breakdowns, and recent activity
    for the officer dashboard home page.
    """
    service = OfficerService(db)
    overview = service.get_dashboard_overview(current_user.id)
    
    return {
        "message": "Dashboard overview retrieved successfully",
        "officer_name": current_user.full_name,
        "officer_role": current_user.role.value,
        "data": overview
    }

@router.get("/workload")
def get_workload_assignment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer)
) -> Any:
    """
    Get officer workload and task assignments (Officers/Admins only)
    
    Returns prioritized queues of applications that need attention,
    organized by urgency and task type.
    """
    service = OfficerService(db)
    workload = service.get_workload_assignment(current_user.id)
    
    return {
        "message": "Workload assignment retrieved successfully",
        "officer_id": str(current_user.id),
        "assigned_work": workload
    }

@router.get("/alerts")
def get_system_alerts(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by alert severity")
) -> Any:
    """
    Get system alerts for officer attention (Officers/Admins only)
    
    Returns unresolved alerts about overdue applications, suspicious activity,
    and other system issues requiring officer intervention.
    """
    service = OfficerService(db)
    alerts = service.get_system_alerts(severity)
    
    return {
        "message": "System alerts retrieved successfully",
        "total_alerts": len(alerts),
        "severity_filter": severity.value if severity else None,
        "alerts": alerts
    }

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_system_alert(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    alert_id: uuid.UUID,
    notes: Optional[str] = None
) -> Any:
    """
    Acknowledge a system alert (Officers/Admins only)
    
    Marks an alert as resolved and optionally adds resolution notes.
    """
    service = OfficerService(db)
    
    try:
        result = service.acknowledge_alert(alert_id, current_user.id, notes)
        return {
            "message": "Alert acknowledged successfully",
            "acknowledged_by": current_user.full_name,
            "acknowledgment": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/statistics/processing")
def get_processing_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days")
) -> Any:
    """
    Get processing performance statistics (Officers/Admins only)
    
    Returns detailed metrics about application processing times,
    SLA compliance, and efficiency measures.
    """
    service = OfficerService(db)
    stats = service.get_processing_statistics(period_days)
    
    return {
        "message": "Processing statistics retrieved successfully",
        "generated_by": current_user.full_name,
        "generated_at": datetime.utcnow().isoformat(),
        "statistics": stats
    }

@router.get("/reports/fraud-detection")
def get_fraud_detection_report(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer)
) -> Any:
    """
    Get fraud detection and suspicious activity report (Officers/Admins only)
    
    Returns analysis of potentially fraudulent or suspicious applications,
    including fast-track abuse and unusual processing patterns.
    """
    service = OfficerService(db)
    report = service.get_fraud_detection_report()
    
    return {
        "message": "Fraud detection report generated successfully",
        "generated_by": current_user.full_name,
        "generated_at": datetime.utcnow().isoformat(),
        "report": report,
        "security_notice": "This report contains sensitive information. Handle according to security protocols."
    }

@router.get("/queue/priority")
def get_priority_queue(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of applications to return")
) -> Any:
    """
    Get high-priority applications queue (Officers/Admins only)
    
    Returns applications that require immediate attention due to
    emergency/urgent priority levels or overdue status.
    """
    service = OfficerService(db)
    workload = service.get_workload_assignment(current_user.id)
    
    return {
        "message": "Priority queue retrieved successfully",
        "queue_size": len(workload["priority_queue"]),
        "applications": workload["priority_queue"][:limit]
    }

@router.get("/queue/document-review")
def get_document_review_queue(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    limit: int = Query(15, ge=1, le=50, description="Maximum number of applications to return")
) -> Any:
    """
    Get document review queue (Officers/Admins only)
    
    Returns applications waiting for document verification
    and additional document submission.
    """
    service = OfficerService(db)
    workload = service.get_workload_assignment(current_user.id)
    
    return {
        "message": "Document review queue retrieved successfully",
        "queue_size": len(workload["document_review_queue"]),
        "applications": workload["document_review_queue"][:limit]
    }

@router.get("/queue/quality-check")
def get_quality_check_queue(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    limit: int = Query(10, ge=1, le=30, description="Maximum number of applications to return")
) -> Any:
    """
    Get quality control queue (Officers/Admins only)
    
    Returns applications ready for final quality checks
    before being marked as ready for pickup.
    """
    service = OfficerService(db)
    workload = service.get_workload_assignment(current_user.id)
    
    return {
        "message": "Quality check queue retrieved successfully",
        "queue_size": len(workload["quality_check_queue"]),
        "applications": workload["quality_check_queue"][:limit]
    }

@router.get("/queue/ready-for-pickup")
def get_ready_for_pickup_queue(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    location_id: Optional[uuid.UUID] = Query(None, description="Filter by pickup location ID"),
    date_from: Optional[datetime] = Query(None, description="Start date for scheduled appointments"),
    date_to: Optional[datetime] = Query(None, description="End date for scheduled appointments"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page")
) -> Any:
    """
    Get appointments for passports ready for pickup (Officers/Admins only)
    
    Supports filtering by location and date range, plus pagination.
    """
    service = OfficerService(db)

    offset = (page - 1) * page_size
    result = service.get_ready_for_pickup_appointments(
        location_id=location_id,
        date_from=date_from,
        date_to=date_to,
        limit=page_size,
        offset=offset,
    )

    total_pages = (result["total"] + page_size - 1) // page_size

    return {
        "message": "Ready-for-pickup appointments retrieved successfully",
        "retrieved_by": current_user.full_name,
        "retrieved_at": datetime.utcnow().isoformat(),
        "filters": {
            "location_id": str(location_id) if location_id else None,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
        },
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_records": result["total"],
        },
        "appointments": result["appointments"],
    }


@router.get("/analytics/trends")
def get_application_trends(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    days: int = Query(30, ge=7, le=180, description="Number of days for trend analysis")
) -> Any:
    """
    Get application submission and processing trends (Officers/Admins only)
    
    Returns trend data for visualizing application volumes,
    processing times, and seasonal patterns.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract
    
    # Calculate trends over the specified period
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Daily submission trends
    daily_submissions = db.query(
        func.date(PassportApplication.submitted_at).label('date'),
        func.count(PassportApplication.id).label('count')
    ).filter(
        func.date(PassportApplication.submitted_at).between(start_date, end_date)
    ).group_by(
        func.date(PassportApplication.submitted_at)
    ).all()
    
    # Priority distribution over time
    priority_trends = db.query(
        PassportApplication.priority_level,
        func.count(PassportApplication.id).label('count')
    ).filter(
        func.date(PassportApplication.submitted_at).between(start_date, end_date)
    ).group_by(
        PassportApplication.priority_level
    ).all()
    
    return {
        "message": "Application trends retrieved successfully",
        "period": f"{days} days",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "trends": {
            "daily_submissions": [
                {"date": item.date.isoformat(), "count": item.count}
                for item in daily_submissions
            ],
            "priority_distribution": [
                {"priority": item.priority_level, "count": item.count}
                for item in priority_trends
            ]
        }
    }

@router.get("/export/applications")
def export_applications_data(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),  # Admin only for exports
    status_filter: Optional[str] = Query(None, description="Filter by application status"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include")
) -> Any:
    """
    Export applications data for reporting (Admin only)
    
    Returns comprehensive application data for external reporting,
    compliance audits, or data analysis.
    """
    from datetime import datetime, timedelta
    
    # Build query with filters
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = db.query(PassportApplication).filter(
        PassportApplication.submitted_at >= cutoff_date
    )
    
    if status_filter:
        query = query.filter(PassportApplication.status == status_filter)
    
    applications = query.order_by(PassportApplication.submitted_at.desc()).all()
    
    # Format for export
    export_data = []
    for app in applications:
        applicant = db.query(User).filter(User.id == app.applicant_id).first()
        export_data.append({
            "application_number": app.application_number,
            "applicant_name": applicant.full_name if applicant else "Unknown",
            "applicant_email": applicant.email if applicant else "Unknown",
            "status": app.status,
            "priority_level": app.priority_level,
            "priority_reason": app.priority_reason,
            "passport_type": app.passport_type,
            "pages": app.pages,
            "submitted_at": app.submitted_at.isoformat(),
            "estimated_completion": app.estimated_completion_date.isoformat() if app.estimated_completion_date else None,
            "actual_completion": app.actual_completion_date.isoformat() if app.actual_completion_date else None,
            "days_in_processing": app.days_in_processing,
            "is_overdue": app.is_overdue,
            "is_fast_tracked": app.is_fast_tracked,
            "fast_track_reason": app.fast_track_reason
        })
    
    return {
        "message": "Applications data exported successfully",
        "exported_by": current_user.full_name,
        "export_timestamp": datetime.utcnow().isoformat(),
        "total_records": len(export_data),
        "filters_applied": {
            "status_filter": status_filter,
            "days_included": days
        },
        "data": export_data
    }