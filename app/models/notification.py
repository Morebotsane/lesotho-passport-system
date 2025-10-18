# app/models/notification.py
#from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base

class NotificationType(str, enum.Enum):
    """Types of notifications"""
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKUP_REMINDER = "pickup_reminder"
    PICKUP_URGENT = "pickup_urgent"
    STATUS_UPDATE = "status_update"
    DOCUMENTS_REQUIRED = "documents_required"
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    APPOINTMENT_REMINDER = "appointment_reminder"

class NotificationStatus(str, enum.Enum):
    """Status of notification delivery"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"

class Notification(Base):
    """
    SMS notification model
    Tracks all notifications sent to passport applicants
    """
    __tablename__ = "notifications"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationships
    passport_application_id = Column(UUID(as_uuid=True), ForeignKey("passport_applications.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # System notifications have null sender
    
    # Notification content
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    message = Column(Text, nullable=False)
    recipient_phone = Column(String(20), nullable=False)

    # ADD THESE FIELDS for Celery integration
    celery_task_id = Column(String(255), nullable=True, index=True)  # Track Celery task
    celery_queue = Column(String(100), nullable=True)  # Which queue processed it
    max_retries = Column(Integer, default=3, nullable=False)  # Max retry attempts
    
    # Delivery tracking
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    twilio_message_sid = Column(String(100), nullable=True)  # Twilio's unique message ID
    delivery_status = Column(String(20), nullable=True)  # Twilio's delivery status
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    passport_application = relationship("PassportApplication", back_populates="notifications")
    sender = relationship("User", back_populates="sent_notifications", foreign_keys=[sender_id])
    
    def __repr__(self):
        return f"<Notification {self.notification_type.value} to {self.recipient_phone} ({self.status.value})>"

# ============================================================================

class AlertType(str, enum.Enum):
    """Types of system alerts"""
    STUCK_PIPELINE = "stuck_pipeline"
    SUSPICIOUS_FAST_TRACK = "suspicious_fast_track"
    PICKUP_OVERDUE = "pickup_overdue"
    DOCUMENTS_PENDING = "documents_pending"
    SYSTEM_ERROR = "system_error"

class AlertSeverity(str, enum.Enum):
    """Severity levels for alerts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SystemAlert(Base):
    """
    System alerts for passport officers
    Monitors pipeline issues, suspicious activities, and overdue items
    """
    __tablename__ = "system_alerts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Alert details
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, default=AlertSeverity.MEDIUM)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Related entities
    passport_application_id = Column(UUID(as_uuid=True), ForeignKey("passport_applications.id"), nullable=True)
    
    # Status tracking  
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    passport_application = relationship("PassportApplication", back_populates="alerts")
    acknowledged_by_user = relationship("User", back_populates="acknowledged_alerts")
    
    def acknowledge(self, officer_id: uuid.UUID, notes: str = None):
        """Acknowledge the alert"""
        self.is_acknowledged = True
        self.acknowledged_by_id = officer_id
        self.acknowledged_at = datetime.utcnow()
        if notes:
            self.resolution_notes = notes
    
    def __repr__(self):
        return f"<SystemAlert {self.alert_type.value} - {self.severity.value}>"

# ============================================================================