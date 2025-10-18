# app/models/passport_application.py - FIXED VERSION
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import enum

from app.database import Base

class ApplicationStatus(str, enum.Enum):
    """Status of passport application"""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    DOCUMENTS_REQUIRED = "documents_required"
    PROCESSING = "processing"
    QUALITY_CHECK = "quality_check"
    READY_FOR_PICKUP = "ready_for_pickup"
    COLLECTED = "collected"
    EXPIRED = "expired"
    REJECTED = "rejected"

class PriorityLevel(str, enum.Enum):
    """Priority levels for applications"""
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class PriorityReason(str, enum.Enum):
    """Reasons for priority processing"""
    MIGRANT_WORKER = "migrant_worker"
    STUDENT_ABROAD = "student_abroad" 
    MEDICAL_TREATMENT = "medical_treatment"
    EMERGENCY_TRAVEL = "emergency_travel"
    OFFICIAL_DUTY = "official_duty"

class PassportApplication(Base):
    """
    Core passport application model
    Tracks the entire lifecycle from submission to collection
    """
    __tablename__ = "passport_applications"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Application identification
    application_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Applicant relationship
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Application details
    passport_type = Column(String(20), nullable=False, default="regular")  # regular, diplomatic, official
    pages = Column(Integer, nullable=False, default=32)  # 32 or 64 pages
    
    # Status tracking
    status = Column(String(30), nullable=False, default=ApplicationStatus.SUBMITTED.value)
    priority_level = Column(String(20), nullable=False, default=PriorityLevel.NORMAL.value)
    priority_reason = Column(String(30), nullable=True)
    
    # Processing stages (JSON field to track detailed progress)
    processing_stages = Column(JSON, nullable=False, default=dict)
    
    # Fast-tracking detection
    is_fast_tracked = Column(Boolean, default=False, nullable=False)
    fast_track_reason = Column(Text, nullable=True)
    fast_track_approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Important dates
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    estimated_completion_date = Column(DateTime, nullable=True)
    actual_completion_date = Column(DateTime, nullable=True)
    pickup_deadline = Column(DateTime, nullable=True)  # When uncollected passport expires
    collected_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ========================================================================
    # ADD THESE NEW COLUMNS FOR PERSONAL INFORMATION
    # ========================================================================
    
    # Personal Information (snapshot at application time)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(String(10), nullable=False)  # YYYY-MM-DD format
    place_of_birth = Column(String(100), nullable=False)
    nationality = Column(String(50), nullable=False, default="Lesotho")
    gender = Column(String(10), nullable=True)
    
    # Contact Information
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    residential_address = Column(Text, nullable=False)
    
    # Identification
    national_id_number = Column(String(20), nullable=True)
    previous_passport_number = Column(String(20), nullable=True)
    reason_for_issuance = Column(String(20), nullable=False)
    
    # Emergency Contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    
    # Travel Information
    travel_purpose = Column(String(200), nullable=True)
    intended_travel_date = Column(DateTime, nullable=True)
    
    # Document File Paths (for uploaded documents)
    passport_photo_path = Column(String(255), nullable=True)
    id_document_path = Column(String(255), nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)

    # Location where application was lodged
    submission_location_id = Column(UUID(as_uuid=True), ForeignKey("pickup_locations.id"),nullable=True)

    # Relationship
    submission_location = relationship("PickupLocation", foreign_keys=[submission_location_id])

    # Relationships - Fixed with explicit foreign_keys
    applicant = relationship(
        "User", 
        back_populates="passport_applications", 
        foreign_keys=[applicant_id]
    )
    
    fast_track_approver = relationship(
        "User", 
        back_populates="fast_tracked_applications",
        foreign_keys=[fast_track_approved_by]
    )
    
    notifications = relationship(
        "Notification", 
        back_populates="passport_application", 
        cascade="all, delete-orphan"
    )
    
    appointments = relationship(
        "PickupAppointment", 
        back_populates="passport_application", 
        cascade="all, delete-orphan"
    )
    
    alerts = relationship(
        "SystemAlert", 
        back_populates="passport_application"
    )
    
    @property
    def days_in_processing(self) -> int:
        """Calculate how many days the application has been in processing"""
        if self.status == ApplicationStatus.COLLECTED.value:
            end_date = self.collected_at or datetime.utcnow()
        else:
            end_date = datetime.utcnow()
        
        return (end_date - self.submitted_at).days
    
    @property
    def is_overdue(self) -> bool:
        """Check if application is taking too long"""
        max_processing_days = {
            PriorityLevel.EMERGENCY.value: 3,
            PriorityLevel.URGENT.value: 7,
            PriorityLevel.HIGH.value: 14,
            PriorityLevel.NORMAL.value: 21
        }
        
        max_days = max_processing_days.get(self.priority_level, 21)
        return self.days_in_processing > max_days and self.status not in [
            ApplicationStatus.COLLECTED.value,
            ApplicationStatus.REJECTED.value,
            ApplicationStatus.EXPIRED.value
        ]
    
    @property 
    def pickup_expires_in_days(self) -> int:
        """Days until pickup deadline (if ready for pickup)"""
        if self.pickup_deadline:
            return (self.pickup_deadline - datetime.utcnow()).days
        return 0
    
    def set_ready_for_pickup(self):
        """Mark application as ready for pickup and set deadline"""
        self.status = ApplicationStatus.READY_FOR_PICKUP.value
        self.actual_completion_date = datetime.utcnow()
        # Give 30 days to collect passport
        self.pickup_deadline = datetime.utcnow() + timedelta(days=30)
    
    def __repr__(self):
        # Use object.__getattribute__ to avoid triggering lazy loading
        try:
            name = object.__getattribute__(self, '__dict__').get('name', 'Unknown')
            return f"<PickupLocation {name}>"
        except:
            return f"<PickupLocation (detached)>"