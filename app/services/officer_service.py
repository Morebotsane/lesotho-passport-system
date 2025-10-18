# app/services/officer_service.py
"""
Officer dashboard service
Handles administrative functions for passport officers
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, case, extract
from datetime import datetime, timedelta
import uuid

from app.models.passport_application import PassportApplication, ApplicationStatus, PriorityLevel
from app.models.user import User, UserRole
from app.models.notification import SystemAlert, AlertType, AlertSeverity, Notification
from app.core.config import settings

class OfficerService:
    """Service for officer dashboard and administrative functions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_overview(self, officer_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get comprehensive dashboard overview for officers
        
        Args:
            officer_id: ID of the requesting officer
            
        Returns:
            Dictionary containing dashboard metrics and data
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Basic counts
        total_applications = self.db.query(PassportApplication).count()
        active_applications = self.db.query(PassportApplication).filter(
            PassportApplication.status.notin_([
                ApplicationStatus.COLLECTED.value,
                ApplicationStatus.REJECTED.value,
                ApplicationStatus.EXPIRED.value
            ])
        ).count()
        
        # Today's metrics
        today_submitted = self.db.query(PassportApplication).filter(
            PassportApplication.submitted_at >= today_start
        ).count()
        
        today_completed = self.db.query(PassportApplication).filter(
            and_(
                PassportApplication.actual_completion_date >= today_start,
                PassportApplication.status == ApplicationStatus.READY_FOR_PICKUP.value
            )
        ).count()
        
        # Status breakdown
        status_counts = {}
        for status in ApplicationStatus:
            count = self.db.query(PassportApplication).filter(
                PassportApplication.status == status.value
            ).count()
            status_counts[status.value] = count
        
        # Priority breakdown
        priority_counts = {}
        for priority in PriorityLevel:
            count = self.db.query(PassportApplication).filter(
                PassportApplication.priority_level == priority.value
            ).count()
            priority_counts[priority.value] = count
        
        # Overdue applications
        overdue_apps = self._get_overdue_applications()
        
        # Pending alerts
        unresolved_alerts = self.db.query(SystemAlert).filter(
            SystemAlert.is_acknowledged == False
        ).count()
        
        # Recent activity
        recent_applications = self.db.query(PassportApplication).order_by(
            desc(PassportApplication.submitted_at)
        ).limit(10).all()
        
        return {
            "overview": {
                "total_applications": total_applications,
                "active_applications": active_applications,
                "today_submitted": today_submitted,
                "today_completed": today_completed,
                "overdue_count": len(overdue_apps),
                "unresolved_alerts": unresolved_alerts
            },
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "recent_applications": [
                {
                    "id": str(app.id),
                    "application_number": app.application_number,
                    "applicant_name": self._get_applicant_name(app.applicant_id),
                    "status": app.status,
                    "priority_level": app.priority_level,
                    "submitted_at": app.submitted_at.isoformat(),
                    "days_processing": app.days_in_processing
                }
                for app in recent_applications
            ]
        }
    
    def get_workload_assignment(self, officer_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get applications assigned to or suitable for a specific officer
        
        Args:
            officer_id: ID of the officer
            
        Returns:
            Dictionary containing assigned and available work
        """
        # Applications needing attention (high priority or overdue)
        priority_queue = self.db.query(PassportApplication).filter(
            and_(
                PassportApplication.priority_level.in_([
                    PriorityLevel.URGENT.value,
                    PriorityLevel.EMERGENCY.value
                ]),
                PassportApplication.status.notin_([
                    ApplicationStatus.COLLECTED.value,
                    ApplicationStatus.REJECTED.value,
                    ApplicationStatus.EXPIRED.value
                ])
            )
        ).order_by(
            case(
                (PassportApplication.priority_level == PriorityLevel.EMERGENCY.value, 1),
                (PassportApplication.priority_level == PriorityLevel.URGENT.value, 2),
                else_=3
            ),
            PassportApplication.submitted_at
        ).limit(20).all()
        
        # Applications requiring document review
        document_review_queue = self.db.query(PassportApplication).filter(
            PassportApplication.status == ApplicationStatus.DOCUMENTS_REQUIRED.value
        ).order_by(PassportApplication.submitted_at).limit(15).all()
        
        # Applications ready for quality check
        quality_check_queue = self.db.query(PassportApplication).filter(
            PassportApplication.status == ApplicationStatus.QUALITY_CHECK.value
        ).order_by(PassportApplication.submitted_at).limit(10).all()
        
        return {
            "priority_queue": self._format_application_list(priority_queue),
            "document_review_queue": self._format_application_list(document_review_queue),
            "quality_check_queue": self._format_application_list(quality_check_queue),
            "total_pending_work": len(priority_queue) + len(document_review_queue) + len(quality_check_queue)
        }
    
    def get_system_alerts(self, severity_filter: Optional[AlertSeverity] = None) -> List[Dict[str, Any]]:
        """
        Get system alerts for officer attention
        
        Args:
            severity_filter: Filter by alert severity
            
        Returns:
            List of system alerts
        """
        query = self.db.query(SystemAlert).filter(
            SystemAlert.is_acknowledged == False
        )
        
        if severity_filter:
            query = query.filter(SystemAlert.severity == severity_filter)
        
        alerts = query.order_by(
            case(
                (SystemAlert.severity == AlertSeverity.CRITICAL.value, 1),
                (SystemAlert.severity == AlertSeverity.HIGH.value, 2),
                (SystemAlert.severity == AlertSeverity.MEDIUM.value, 3),
                else_=4
            ),
            desc(SystemAlert.created_at)
        ).limit(50).all()
        
        return [
            {
                "id": str(alert.id),
                "type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "application_number": self._get_application_number(alert.passport_application_id) if alert.passport_application_id else None,
                "created_at": alert.created_at.isoformat(),
                "age_hours": int((datetime.utcnow() - alert.created_at).total_seconds() / 3600)
            }
            for alert in alerts
        ]
    
    def acknowledge_alert(self, alert_id: uuid.UUID, officer_id: uuid.UUID, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Acknowledge a system alert
        
        Args:
            alert_id: ID of the alert to acknowledge
            officer_id: ID of the acknowledging officer
            notes: Optional resolution notes
            
        Returns:
            Acknowledgment confirmation
        """
        alert = self.db.query(SystemAlert).filter(
            SystemAlert.id == alert_id
        ).first()
        
        if not alert:
            raise ValueError("Alert not found")
        
        if alert.is_acknowledged:
            raise ValueError("Alert has already been acknowledged")
        
        alert.acknowledge(officer_id, notes)
        self.db.commit()
        
        return {
            "alert_id": str(alert_id),
            "acknowledged_by": str(officer_id),
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "notes": notes
        }
    
    def get_processing_statistics(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Generate processing performance statistics
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Processing performance metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Applications completed in period
        completed_apps = self.db.query(PassportApplication).filter(
            and_(
                PassportApplication.actual_completion_date >= cutoff_date,
                PassportApplication.status == ApplicationStatus.READY_FOR_PICKUP.value
            )
        ).all()
        
        if not completed_apps:
            return {"message": "No completed applications in the specified period"}
        
        # Calculate processing times
        processing_times = []
        for app in completed_apps:
            if app.submitted_at and app.actual_completion_date:
                processing_days = (app.actual_completion_date - app.submitted_at).days
                processing_times.append(processing_days)
        
        if processing_times:
            avg_processing_time = sum(processing_times) / len(processing_times)
            fastest_processing = min(processing_times)
            slowest_processing = max(processing_times)
        else:
            avg_processing_time = fastest_processing = slowest_processing = 0
        
        # SLA compliance by priority
        sla_targets = {
            PriorityLevel.EMERGENCY.value: 3,
            PriorityLevel.URGENT.value: 7,
            PriorityLevel.HIGH.value: 14,
            PriorityLevel.NORMAL.value: 21
        }
        
        compliance_stats = {}
        for priority, target_days in sla_targets.items():
            priority_apps = [app for app in completed_apps if app.priority_level == priority]
            if priority_apps:
                compliant = sum(1 for app in priority_apps if app.days_in_processing <= target_days)
                compliance_rate = (compliant / len(priority_apps)) * 100
                compliance_stats[priority] = {
                    "total": len(priority_apps),
                    "compliant": compliant,
                    "compliance_rate": round(compliance_rate, 1)
                }
        
        return {
            "period_days": period_days,
            "total_completed": len(completed_apps),
            "average_processing_days": round(avg_processing_time, 1),
            "fastest_processing_days": fastest_processing,
            "slowest_processing_days": slowest_processing,
            "sla_compliance": compliance_stats,
            "overall_efficiency": round((len([t for t in processing_times if t <= 21]) / len(processing_times)) * 100, 1) if processing_times else 0
        }
    
    def get_fraud_detection_report(self) -> Dict[str, Any]:
        """
        Generate fraud detection and suspicious activity report
        
        Returns:
            Fraud detection metrics and flagged applications
        """
        # Fast-tracked applications (potential corruption indicator)
        fast_tracked = self.db.query(PassportApplication).filter(
            PassportApplication.is_fast_tracked == True
        ).all()
        
        # Suspicious fast-tracks (approved very quickly)
        suspicious_fast_tracks = [
            app for app in fast_tracked 
            if app.days_in_processing <= 1
        ]
        
        # Applications with multiple status changes in short time
        recent_apps = self.db.query(PassportApplication).filter(
            PassportApplication.submitted_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        return {
            "total_fast_tracked": len(fast_tracked),
            "suspicious_fast_tracks": len(suspicious_fast_tracks),
            "suspicious_applications": [
                {
                    "application_number": app.application_number,
                    "applicant_name": self._get_applicant_name(app.applicant_id),
                    "days_in_processing": app.days_in_processing,
                    "fast_track_reason": app.fast_track_reason,
                    "approved_by": str(app.fast_track_approved_by) if app.fast_track_approved_by else None,
                    "submitted_at": app.submitted_at.isoformat()
                }
                for app in suspicious_fast_tracks
            ],
            "recommendations": self._generate_fraud_recommendations(suspicious_fast_tracks)
        }
    
    # Private helper methods
    def _get_overdue_applications(self) -> List[PassportApplication]:
        """Get applications that are overdue for processing"""
        applications = self.db.query(PassportApplication).filter(
            PassportApplication.status.notin_([
                ApplicationStatus.COLLECTED.value,
                ApplicationStatus.REJECTED.value,
                ApplicationStatus.EXPIRED.value
            ])
        ).all()
        
        return [app for app in applications if app.is_overdue]
    
    def _get_applicant_name(self, applicant_id: uuid.UUID) -> str:
        """Get applicant's full name"""
        user = self.db.query(User).filter(User.id == applicant_id).first()
        return user.full_name if user else "Unknown"
    
    def _get_application_number(self, application_id: uuid.UUID) -> Optional[str]:
        """Get application number by ID"""
        app = self.db.query(PassportApplication).filter(
            PassportApplication.id == application_id
        ).first()
        return app.application_number if app else None
    
    def _format_application_list(self, applications: List[PassportApplication]) -> List[Dict[str, Any]]:
        """Format application list for API response"""
        return [
            {
                "id": str(app.id),
                "application_number": app.application_number,
                "applicant_name": self._get_applicant_name(app.applicant_id),
                "status": app.status,
                "priority_level": app.priority_level,
                "submitted_at": app.submitted_at.isoformat(),
                "days_in_processing": app.days_in_processing,
                "is_overdue": app.is_overdue,
                "estimated_completion": app.estimated_completion_date.isoformat() if app.estimated_completion_date else None
            }
            for app in applications
        ]
    
    def _generate_fraud_recommendations(self, suspicious_apps: List[PassportApplication]) -> List[str]:
        """Generate fraud prevention recommendations"""
        recommendations = []
        
        if len(suspicious_apps) > 5:
            recommendations.append("High number of suspicious fast-tracks detected - consider implementing additional approval layers")
        
        if any(app.days_in_processing == 0 for app in suspicious_apps):
            recommendations.append("Same-day approvals detected - review fast-track approval processes")
        
        if suspicious_apps:
            recommendations.append("Review fast-track justifications for adequacy and authenticity")
            recommendations.append("Cross-reference approving officers for patterns")
        
        return recommendations or ["No immediate fraud concerns detected"]

    def get_ready_for_pickup_appointments(
        self,
        location_id: Optional[uuid.UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """
        Retrieve appointments for passports ready for pickup with optional filters.
        """
        from app.models.appointment import PickupAppointment, PickupLocation
        from app.models.passport_application import ApplicationStatus

        query = (
            self.db.query(PickupAppointment)
            .join(PassportApplication)
            .join(PickupLocation)
            .filter(PassportApplication.status == ApplicationStatus.READY_FOR_PICKUP.value)
        )

        if location_id:
            query = query.filter(PickupAppointment.location_id == location_id)

        if date_from:
            query = query.filter(PickupAppointment.scheduled_datetime >= date_from)

        if date_to:
            query = query.filter(PickupAppointment.scheduled_datetime <= date_to)

        total_count = query.count()

        appointments = (
            query.order_by(PickupAppointment.scheduled_datetime.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        formatted = [
            {
                "appointment_id": str(a.id),
                "application_number": a.passport_application.application_number,
                "applicant_name": f"{a.passport_application.first_name} {a.passport_application.last_name}",
                "applicant_phone": a.passport_application.phone,
                "location_name": a.location.name,
                "scheduled_datetime": a.scheduled_datetime.isoformat(),
                "status": a.status,
                "confirmation_code": a.confirmation_code,
            }
            for a in appointments
        ]

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "appointments": formatted,
        }

