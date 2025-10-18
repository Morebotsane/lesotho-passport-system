# app/models/appointment.py
"""
Enhanced appointment model with scheduling capabilities
Extends the existing PickupAppointment model with additional features
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Time, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, time
import uuid
import enum

from app.database import Base

# Define enums
class AppointmentType(str, enum.Enum):
    SUBMISSION = "submission"  # For lodging application + biometrics
    COLLECTION = "collection"  # For picking up passport

class AppointmentStatus(str, enum.Enum):
    """Status of pickup appointments"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

class TimeSlotStatus(str, enum.Enum):
    """Availability status of time slots"""
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"  # Blocked by admin (holidays, maintenance, etc.)
    UNAVAILABLE = "unavailable"

class PickupLocation(Base):
    """
    Pickup locations/offices where passports can be collected
    Supports multiple offices with different schedules
    """
    __tablename__ = "pickup_locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Operating hours
    opens_at = Column(Time, nullable=False, default=time(8, 0))  # 08:00
    closes_at = Column(Time, nullable=False, default=time(17, 0))  # 17:00
    
    # Operating days (JSON array of weekday numbers: 0=Monday, 6=Sunday)
    operating_days = Column(String(50), nullable=False, default="0,1,2,3,4")  # Mon-Fri
    
    # Appointment settings
    slot_duration_minutes = Column(Integer, nullable=False, default=15)
    max_appointments_per_slot = Column(Integer, nullable=False, default=1)
    advance_booking_days = Column(Integer, nullable=False, default=14)  # How far ahead can book
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    appointments = relationship("PickupAppointment", back_populates="location")
    time_slots = relationship("TimeSlot", back_populates="location", cascade="all, delete-orphan")
    
    def is_open_on_day(self, weekday: int) -> bool:
        """Check if location is open on given weekday (0=Monday)"""
        operating_days = [int(d) for d in self.operating_days.split(',')]
        return weekday in operating_days
    
    def is_open_at_time(self, check_time: time) -> bool:
        """Check if location is open at given time"""
        return self.opens_at <= check_time <= self.closes_at
    
    def __repr__(self):
        # Use object,__getattribut__ to avoid triggering lazy loading
        try: 
            name = object.__getattribute__(self, '__dict__').get('name','Unknown')
            return f"<PickupLocation {name}>"
        except: 
            return f"<PickupLocation {self.name}>"


class TimeSlot(Base):
    """
    Available time slots for appointments
    Pre-generated slots based on location schedule
    """
    __tablename__ = "time_slots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("pickup_locations.id"), nullable=False)
    
    # Slot timing
    slot_date = Column(DateTime, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Capacity management
    max_capacity = Column(Integer, nullable=False, default=1)
    current_bookings = Column(Integer, nullable=False, default=0)
    
    # Status
    status = Column(String(20), nullable=False, default=TimeSlotStatus.AVAILABLE.value)
    blocked_reason = Column(String(255), nullable=True)  # Why slot is blocked
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    location = relationship("PickupLocation", back_populates="time_slots")
    appointments = relationship("PickupAppointment", back_populates="time_slot")
    
    @property
    def is_available(self) -> bool:
        """Check if slot has availability"""
        return (
            self.status == TimeSlotStatus.AVAILABLE.value and 
            self.current_bookings < self.max_capacity and
            self.slot_date > datetime.utcnow()
        )
    
    @property
    def remaining_capacity(self) -> int:
        """Get remaining appointment capacity"""
        return max(0, self.max_capacity - self.current_bookings)
    
    def book_slot(self):
        """Book this time slot (increment counter)"""
        if self.current_bookings >= self.max_capacity:
            raise ValueError("Time slot is fully booked")
        
        self.current_bookings += 1
        if self.current_bookings >= self.max_capacity:
            self.status = TimeSlotStatus.BOOKED.value
    
    def release_slot(self):
        """Release a booking from this slot"""
        if self.current_bookings > 0:
            self.current_bookings -= 1
            if self.current_bookings < self.max_capacity:
                self.status = TimeSlotStatus.AVAILABLE.value
    
    def __repr__(self):
        return f"<TimeSlot {self.slot_date.date()} {self.start_time}-{self.end_time}>"

class PickupAppointment(Base):
    """
    Enhanced pickup appointment model
    Replaces the basic appointment model with full scheduling features
    """
    __tablename__ = "pickup_appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Core relationships
    passport_application_id = Column(UUID(as_uuid=True), ForeignKey("passport_applications.id"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("pickup_locations.id"), nullable=False)
    time_slot_id = Column(UUID(as_uuid=True), ForeignKey("time_slots.id"), nullable=False)
    
    # Appointment details
    scheduled_datetime = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=15, nullable=False)
    
    # Status tracking
    status = Column(String(20), nullable=False, default=AppointmentStatus.SCHEDULED.value)
    confirmation_code = Column(String(10), nullable=True, unique=True, index=True)
    
    # Additional information
    notes = Column(Text, nullable=True)
    special_requirements = Column(Text, nullable=True)  # Wheelchair access, language needs, etc.
    
    # Attendance tracking
    checked_in_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Rescheduling tracking
    original_appointment_id = Column(UUID(as_uuid=True), ForeignKey("pickup_appointments.id"), nullable=True)
    rescheduled_from_datetime = Column(DateTime, nullable=True)
    reschedule_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # ADD Appointment type
    appointment_type = Column(SQLEnum(AppointmentType), nullable=False, default=AppointmentType.COLLECTION.value)

    # Relationships
    passport_application = relationship("PassportApplication", back_populates="appointments")
    location = relationship("PickupLocation", back_populates="appointments")
    time_slot = relationship("TimeSlot", back_populates="appointments")
    original_appointment = relationship("PickupAppointment", remote_side=[id])
    
    @property
    def is_upcoming(self) -> bool:
        """Check if appointment is in the future"""
        return self.scheduled_datetime > datetime.utcnow()
    
    @property
    def is_today(self) -> bool:
        """Check if appointment is today"""
        return self.scheduled_datetime.date() == datetime.utcnow().date()
    
    @property
    def is_overdue(self) -> bool:
        """Check if appointment time has passed but not completed"""
        return (
            self.scheduled_datetime < datetime.utcnow() and 
            self.status in [AppointmentStatus.SCHEDULED.value, AppointmentStatus.CONFIRMED.value]
        )
    
    @property
    def can_be_rescheduled(self) -> bool:
        """Check if appointment can be rescheduled"""
        if self.status not in [AppointmentStatus.SCHEDULED.value, AppointmentStatus.CONFIRMED.value]:
            return False
        
        # Remove or increase the limit
        # OLD: if self.reschedule_count >= 1:  # Only 1 reschedule allowed
        if self.reschedule_count >= 3:  # Allow up to 3 reschedules
            return False
        
        # Can't reschedule if less than 24 hours away
        if self.scheduled_datetime - datetime.utcnow() < timedelta(hours=24):
            return False
        
        return True
    
    def check_in(self):
        """Check in for the appointment"""
        if self.status != AppointmentStatus.CONFIRMED.value:
            raise ValueError("Only confirmed appointments can be checked in")
        
        self.status = AppointmentStatus.CHECKED_IN.value
        self.checked_in_at = datetime.utcnow()
    
    def complete(self):
        """Mark appointment as completed"""
        if self.status != AppointmentStatus.CHECKED_IN.value:
            raise ValueError("Only checked-in appointments can be completed")
        
        self.status = AppointmentStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
    
    def cancel(self, reason: str = None):
        """Cancel the appointment"""
        if self.status in [AppointmentStatus.COMPLETED.value, AppointmentStatus.CANCELLED.value]:
            raise ValueError("Cannot cancel completed or already cancelled appointment")
        
        self.status = AppointmentStatus.CANCELLED.value
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.cancellation_reason = reason
        
        # Release the time slot
        if self.time_slot:
            self.time_slot.release_slot()
    
    def mark_no_show(self):
        """Mark appointment as no-show"""
        if not self.is_overdue:
            raise ValueError("Cannot mark as no-show before appointment time")
        
        self.status = AppointmentStatus.NO_SHOW.value
        
        # Release the time slot
        if self.time_slot:
            self.time_slot.release_slot()
    
    def generate_confirmation_code(self):
        """Generate a unique confirmation code"""
        import random
        import string
        
        # Generate 6-digit alphanumeric code
        self.confirmation_code = ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
    
    def __repr__(self):
        return f"<PickupAppointment {self.confirmation_code} - {self.scheduled_datetime}>"