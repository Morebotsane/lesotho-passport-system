# app/services/passport_service.py
"""
Business logic for passport application operations
This service layer handles the core business rules and processes
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta
import uuid

from app.models.passport_application import PassportApplication, ApplicationStatus, PriorityLevel, PriorityReason
from app.models.user import User, UserRole
from app.models.notification import SystemAlert, AlertType, AlertSeverity
from app.schemas.passport_application import (
    PassportApplicationCreate,
    ApplicationFilter,
    PassportApplicationUpdate
)
from app.core.security import generate_application_number
from app.core.config import settings

class PassportApplicationService:
    """Service class for passport application business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_application(
        self, 
        application_data: PassportApplicationCreate, 
        applicant_id: uuid.UUID
    ) -> PassportApplication:
        """
        Create a new passport application
        
        Args:
            application_data: Application details
            applicant_id: ID of the applicant
            
        Returns:
            Created PassportApplication object
        """
        # Generate unique application number
        application_number = generate_application_number()
        
        # Ensure application number is unique
        while self.db.query(PassportApplication).filter(
            PassportApplication.application_number == application_number
        ).first():
            application_number = generate_application_number()
        
        # Determine initial priority level based on priority reason
        priority_level = self._determine_priority_level(application_data.priority_reason)
        
        # Create application
        db_application = PassportApplication(
            application_number=application_number,
            applicant_id=applicant_id,
            passport_type=application_data.passport_type,
            pages=application_data.pages,
            priority_level=priority_level.value,
            priority_reason=application_data.priority_reason.value if application_data.priority_reason else None,
            processing_stages=self._initialize_processing_stages(),
            estimated_completion_date=self._calculate_estimated_completion(priority_level)
        )
        
        self.db.add(db_application)
        self.db.commit()
        self.db.refresh(db_application)
        
        # Create initial system alert if high priority
        if priority_level in [PriorityLevel.URGENT, PriorityLevel.EMERGENCY]:
            self._create_priority_alert(db_application)
        
        return db_application
    
    def update_application_status(
        self, 
        application_id: uuid.UUID, 
        new_status: ApplicationStatus,
        officer_id: uuid.UUID,
        notes: Optional[str] = None
    ) -> PassportApplication:
        """
        Update application status (officer only)
        
        Args:
            application_id: ID of the application
            new_status: New status to set
            officer_id: ID of the officer making the change
            notes: Optional notes about the status change
            
        Returns:
            Updated PassportApplication object
        """
        application = self.db.query(PassportApplication).filter(
            PassportApplication.id == application_id
        ).first()
        
        if not application:
            raise ValueError("Application not found")
        
        old_status = application.status
        application.status = new_status.value
        
        # Update processing stages
        self._update_processing_stage(application, new_status, officer_id, notes)
        
        # Handle status-specific logic
        if new_status == ApplicationStatus.READY_FOR_PICKUP:
            application.set_ready_for_pickup()
            # TODO: Trigger SMS notification
            
        elif new_status == ApplicationStatus.COLLECTED:
            application.collected_at = datetime.utcnow()
            
        self.db.commit()
        self.db.refresh(application)
        
        return application
    
    def get_applications_by_user(
        self, 
        user_id: uuid.UUID,
        filters: Optional[ApplicationFilter] = None
    ) -> List[PassportApplication]:
        """
        Get applications for a specific user
        
        Args:
            user_id: ID of the user
            filters: Optional filters to apply
            
        Returns:
            List of PassportApplication objects
        """
        query = self.db.query(PassportApplication).filter(
            PassportApplication.applicant_id == user_id
        )
        
        if filters:
            query = self._apply_filters(query, filters)
        
        # Default sorting by submission date (newest first)
        query = query.order_by(desc(PassportApplication.submitted_at))
        
        return query.all()
    
    def search_applications(
        self, 
        filters: ApplicationFilter,
        user_role: UserRole
    ) -> Dict[str, Any]:
        """
        Search applications with filtering and pagination
        
        Args:
            filters: Search and filter parameters
            user_role: Role of the requesting user
            
        Returns:
            Dictionary containing applications and pagination info
        """
        query = self.db.query(PassportApplication)
        
        # Apply filters
        query = self._apply_filters(query, filters)
        
        # Apply sorting
        sort_field = getattr(PassportApplication, filters.sort_by)
        if filters.sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        applications = query.offset(offset).limit(filters.page_size).all()
        
        # Calculate pagination info
        total_pages = (total_count + filters.page_size - 1) // filters.page_size
        
        return {
            "applications": applications,
            "total_count": total_count,
            "page": filters.page,
            "page_size": filters.page_size,
            "total_pages": total_pages,
            "has_next": filters.page < total_pages,
            "has_previous": filters.page > 1
        }
    
    def flag_fast_track_request(
        self, 
        application_id: uuid.UUID, 
        reason: str,
        requested_priority: PriorityLevel,
        officer_id: uuid.UUID
    ) -> PassportApplication:
        """
        Flag an application for fast-track processing
        
        Args:
            application_id: ID of the application
            reason: Reason for fast-tracking
            requested_priority: Requested priority level
            officer_id: ID of the approving officer
            
        Returns:
            Updated PassportApplication object
        """
        application = self.db.query(PassportApplication).filter(
            PassportApplication.id == application_id
        ).first()
        
        if not application:
            raise ValueError("Application not found")
        
        # Check if this is suspicious (too fast)
        processing_days = application.days_in_processing
        if processing_days < 1:
            # Create suspicious activity alert
            self._create_suspicious_fast_track_alert(application, officer_id, reason)
        
        # Update application
        application.is_fast_tracked = True
        application.fast_track_reason = reason
        application.fast_track_approved_by = officer_id
        application.priority_level = requested_priority.value
        application.estimated_completion_date = self._calculate_estimated_completion(requested_priority)
        
        self.db.commit()
        self.db.refresh(application)
        
        return application
    
    def get_overdue_applications(self) -> List[PassportApplication]:
        """
        Get all applications that are overdue for processing
        
        Returns:
            List of overdue PassportApplication objects
        """
        applications = self.db.query(PassportApplication).filter(
            PassportApplication.status.notin_([
                ApplicationStatus.COLLECTED.value,
                ApplicationStatus.REJECTED.value,
                ApplicationStatus.EXPIRED.value
            ])
        ).all()
        
        # Filter to only overdue applications
        overdue_apps = [app for app in applications if app.is_overdue]
        
        return overdue_apps
    
    def generate_processing_statistics(self) -> Dict[str, Any]:
        """
        Generate processing statistics for dashboard
        
        Returns:
            Dictionary containing various statistics
        """
        total_applications = self.db.query(PassportApplication).count()
        
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
        
        # Other metrics
        overdue_count = len(self.get_overdue_applications())
        fast_tracked_count = self.db.query(PassportApplication).filter(
            PassportApplication.is_fast_tracked == True
        ).count()
        
        # Completed this month
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_this_month = self.db.query(PassportApplication).filter(
            and_(
                PassportApplication.status == ApplicationStatus.COLLECTED.value,
                PassportApplication.collected_at >= month_start
            )
        ).count()
        
        return {
            "total_applications": total_applications,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "overdue_applications": overdue_count,
            "fast_tracked_applications": fast_tracked_count,
            "completed_this_month": completed_this_month
        }
    
    # Private helper methods
    def _determine_priority_level(self, priority_reason: Optional[PriorityReason]) -> PriorityLevel:
        """Determine initial priority level based on reason"""
        if not priority_reason:
            return PriorityLevel.NORMAL
        
        priority_mapping = {
            PriorityReason.EMERGENCY_TRAVEL: PriorityLevel.EMERGENCY,
            PriorityReason.MEDICAL_TREATMENT: PriorityLevel.URGENT,
            PriorityReason.MIGRANT_WORKER: PriorityLevel.HIGH,
            PriorityReason.STUDENT_ABROAD: PriorityLevel.HIGH,
            PriorityReason.OFFICIAL_DUTY: PriorityLevel.URGENT
        }
        
        return priority_mapping.get(priority_reason, PriorityLevel.NORMAL)
    
    def _initialize_processing_stages(self) -> Dict[str, Any]:
        """Initialize processing stages tracking"""
        return {
            "submitted": {
                "completed": True,
                "completed_at": datetime.utcnow().isoformat(),
                "notes": "Application submitted successfully"
            },
            "document_verification": {
                "completed": False,
                "assigned_officer": None,
                "notes": None
            },
            "background_check": {
                "completed": False,
                "started_at": None,
                "notes": None
            },
            "passport_production": {
                "completed": False,
                "started_at": None,
                "notes": None
            },
            "quality_control": {
                "completed": False,
                "completed_at": None,
                "notes": None
            }
        }
    
    def _calculate_estimated_completion(self, priority_level: PriorityLevel) -> datetime:
        """Calculate estimated completion date based on priority"""
        business_days_mapping = {
            PriorityLevel.EMERGENCY: 3,
            PriorityLevel.URGENT: 7,
            PriorityLevel.HIGH: 14,
            PriorityLevel.NORMAL: 21
        }
        
        days = business_days_mapping.get(priority_level, 21)
        return datetime.utcnow() + timedelta(days=days)
    
    def _update_processing_stage(
        self, 
        application: PassportApplication, 
        new_status: ApplicationStatus,
        officer_id: uuid.UUID,
        notes: Optional[str]
    ):
        """Update processing stages based on status change"""
        stages = application.processing_stages.copy()
        current_time = datetime.utcnow().isoformat()
        
        # Map status to stage
        status_to_stage = {
            ApplicationStatus.UNDER_REVIEW: "document_verification",
            ApplicationStatus.PROCESSING: "background_check",
            ApplicationStatus.QUALITY_CHECK: "quality_control",
            ApplicationStatus.READY_FOR_PICKUP: "passport_production"
        }
        
        stage_name = status_to_stage.get(new_status)
        if stage_name and stage_name in stages:
            stages[stage_name].update({
                "completed": True,
                "completed_at": current_time,
                "officer_id": str(officer_id),
                "notes": notes or f"Status updated to {new_status.value}"
            })
        
        application.processing_stages = stages
    
    def _apply_filters(self, query, filters: ApplicationFilter):
        """Apply search filters to query"""
        if filters.status:
            query = query.filter(PassportApplication.status.in_([s.value for s in filters.status]))
        
        if filters.priority_level:
            query = query.filter(PassportApplication.priority_level.in_([p.value for p in filters.priority_level]))
        
        if filters.is_fast_tracked is not None:
            query = query.filter(PassportApplication.is_fast_tracked == filters.is_fast_tracked)
        
        if filters.submitted_after:
            query = query.filter(PassportApplication.submitted_at >= filters.submitted_after)
        
        if filters.submitted_before:
            query = query.filter(PassportApplication.submitted_at <= filters.submitted_before)
        
        return query
    
    def _create_priority_alert(self, application: PassportApplication):
        """Create system alert for high-priority applications"""
        alert = SystemAlert(
            alert_type=AlertType.STUCK_PIPELINE,
            severity=AlertSeverity.HIGH,
            title=f"High Priority Application: {application.application_number}",
            description=f"Application {application.application_number} requires priority processing due to {application.priority_reason}",
            passport_application_id=application.id
        )
        
        self.db.add(alert)
        self.db.commit()
    
    def _create_suspicious_fast_track_alert(self, application: PassportApplication, officer_id: uuid.UUID, reason: str):
        """Create alert for suspicious fast-track approval"""
        alert = SystemAlert(
            alert_type=AlertType.SUSPICIOUS_FAST_TRACK,
            severity=AlertSeverity.HIGH,
            title=f"Suspicious Fast-Track: {application.application_number}",
            description=f"Application {application.application_number} was fast-tracked within {application.days_in_processing} days by officer {officer_id}. Reason: {reason}",
            passport_application_id=application.id
        )
        
        self.db.add(alert)
        self.db.commit()