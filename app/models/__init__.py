# app/models/__init__.py
"""
Database models for the Passport Notification System

This package contains all SQLAlchemy models that define the database schema.
Models are organized by domain:
- User: Authentication and user management
- PassportApplication: Core business logic for passport processing
- Notification: SMS notifications and delivery tracking
- SystemAlert: Internal alerts for officers
- PickupAppointment: Appointment scheduling
"""

# app/models/__init__.py
"""
Database models for the Passport Notification System
"""
from app.security.audit_logging import AuditLog
# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User, UserRole
from app.models.passport_application import (
    PassportApplication, 
    ApplicationStatus, 
    PriorityLevel, 
    PriorityReason
)
from app.models.notification import (
    Notification, 
    NotificationType, 
    NotificationStatus,
    SystemAlert,
    AlertType,
    AlertSeverity
)
from app.models.appointment import (
    PickupLocation,
    TimeSlot, 
    PickupAppointment,
    AppointmentStatus,
    TimeSlotStatus
)

# Export all models and enums
__all__ = [
    # Models
    "User",
    "PassportApplication", 
    "Notification",
    "SystemAlert",
    "PickupLocation",
    "TimeSlot",
    "PickupAppointment",
    
    # Enums
    "UserRole",
    "ApplicationStatus",
    "PriorityLevel", 
    "PriorityReason",
    "NotificationType",
    "NotificationStatus",
    "AlertType",
    "AlertSeverity",
    "AppointmentStatus",
    "TimeSlotStatus",
]