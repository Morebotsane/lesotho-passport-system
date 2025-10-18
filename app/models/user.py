# app/models/user.py - FIXED VERSION
from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base

class UserRole(str, enum.Enum):
    """User roles in the system"""
    APPLICANT = "applicant"
    OFFICER = "officer" 
    ADMIN = "admin"

class User(Base):
    """
    User model for authentication and authorization
    Supports applicants, passport officers, and system administrators
    """
    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    
    # System fields
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.APPLICANT)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Location assignment for officers 
    assigned_location_id = Column(UUID(as_uuid=True), ForeignKey("pickup_locations.id"), nullable=True)

    # Relationship
    assigned_location = relationship("PickupLocation", foreign_keys=[assigned_location_id])
    
    # Relationships - Fixed with explicit foreign_keys
    passport_applications = relationship(
        "PassportApplication", 
        back_populates="applicant", 
        cascade="all, delete-orphan",
        foreign_keys="PassportApplication.applicant_id"
    )
    
    fast_tracked_applications = relationship(
        "PassportApplication",
        back_populates="fast_track_approver",
        foreign_keys="PassportApplication.fast_track_approved_by"
    )
    
    sent_notifications = relationship(
        "Notification", 
        back_populates="sender", 
        foreign_keys="Notification.sender_id"
    )
    
    acknowledged_alerts = relationship(
        "SystemAlert", 
        back_populates="acknowledged_by_user",
        foreign_keys="SystemAlert.acknowledged_by_id"
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"