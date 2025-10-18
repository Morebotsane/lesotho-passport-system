# app/schemas/appointment.py
"""
Pydantic schemas for appointment scheduling
Defines API contracts for appointment management
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, time, date
import uuid

from app.models.appointment import AppointmentStatus, TimeSlotStatus, AppointmentType

# ============================================================================
# LOCATION SCHEMAS
# ============================================================================

class PickupLocationBase(BaseModel):
    """Base pickup location schema"""
    name: str = Field(..., min_length=2, max_length=200)
    address: str = Field(..., min_length=10, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    opens_at: time = Field(default=time(8, 0))
    closes_at: time = Field(default=time(17, 0))
    operating_days: str = Field(default="0,1,2,3,4")  # Mon-Fri
    slot_duration_minutes: int = Field(default=15, ge=5, le=60)
    max_appointments_per_slot: int = Field(default=1, ge=1, le=10)
    advance_booking_days: int = Field(default=14, ge=1, le=90)

class PickupLocationCreate(PickupLocationBase):
    """Schema for creating pickup location"""
    pass

class PickupLocationUpdate(BaseModel):
    """Schema for updating pickup location"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    address: Optional[str] = Field(None, min_length=10, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    opens_at: Optional[time] = None
    closes_at: Optional[time] = None
    operating_days: Optional[str] = None
    slot_duration_minutes: Optional[int] = Field(None, ge=5, le=60)
    max_appointments_per_slot: Optional[int] = Field(None, ge=1, le=10)
    advance_booking_days: Optional[int] = Field(None, ge=1, le=90)
    is_active: Optional[bool] = None

class PickupLocationResponse(PickupLocationBase):
    """Schema for pickup location in responses"""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            time: lambda v: v.strftime("%H:%M"),
            uuid.UUID: lambda v: str(v)
        }

# ============================================================================
# TIME SLOT SCHEMAS
# ============================================================================

class TimeSlotResponse(BaseModel):
    """Schema for time slot information"""
    id: uuid.UUID
    location_id: uuid.UUID
    slot_date: datetime
    start_time: time
    end_time: time
    max_capacity: int
    current_bookings: int
    remaining_capacity: int
    status: TimeSlotStatus
    is_available: bool
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            time: lambda v: v.strftime("%H:%M"),
            uuid.UUID: lambda v: str(v)
        }

class AvailabilityRequest(BaseModel):
    """Request schema for checking appointment availability"""
    location_id: uuid.UUID
    preferred_date: date
    alternative_dates: Optional[List[date]] = Field(None, max_items=5)
    preferred_time_range: Optional[Dict[str, time]] = None  # {"start": "09:00", "end": "12:00"}
    
    @validator('preferred_date')
    def validate_preferred_date(cls, v):
        """Ensure preferred date is in the future"""
        if v <= date.today():
            raise ValueError('Preferred date must be in the future')
        return v

class AvailabilityResponse(BaseModel):
    """Response schema for appointment availability"""
    location: PickupLocationResponse
    requested_date: date
    available_slots: List[TimeSlotResponse]
    alternative_dates: Dict[str, List[TimeSlotResponse]]  # date -> slots
    total_available_slots: int

# ============================================================================
# APPOINTMENT SCHEMAS
# ============================================================================

class AppointmentCreate(BaseModel):
    """Schema for creating an appointment"""
    passport_application_id: uuid.UUID
    location_id: uuid.UUID
    time_slot_id: uuid.UUID
    appointment_type: AppointmentType
    notes: Optional[str] = Field(None, max_length=500)
    special_requirements: Optional[str] = Field(None, max_length=500)

class AppointmentReschedule(BaseModel):
    """Schema for rescheduling an appointment"""
    new_time_slot_id: uuid.UUID
    reason: Optional[str] = Field(None, max_length=500)

class AppointmentCancel(BaseModel):
    """Schema for cancelling an appointment"""
    reason: str = Field(..., min_length=5, max_length=500)

class AppointmentUpdate(BaseModel):
    """Schema for updating appointment details"""
    notes: Optional[str] = Field(None, max_length=500)
    special_requirements: Optional[str] = Field(None, max_length=500)

class AppointmentResponse(BaseModel):
    """Schema for appointment in responses"""
    id: uuid.UUID
    passport_application_id: uuid.UUID
    application_number: str  # From related application
    location_name: str  # From related location
    scheduled_datetime: datetime
    duration_minutes: int
    status: AppointmentStatus
    confirmation_code: Optional[str] = None
    notes: Optional[str] = None
    special_requirements: Optional[str] = None
    reschedule_count: int
    can_be_rescheduled: bool
    is_upcoming: bool
    is_today: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }

class AppointmentWithDetails(AppointmentResponse):
    """Extended appointment info with related data"""
    applicant_name: str
    applicant_phone: str
    location: PickupLocationResponse
    checked_in_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

# ============================================================================
# SEARCH & FILTER SCHEMAS
# ============================================================================

class AppointmentFilter(BaseModel):
    """Filter parameters for appointment searches"""
    location_id: Optional[uuid.UUID] = None
    status: Optional[List[AppointmentStatus]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    applicant_name: Optional[str] = Field(None, min_length=2)
    confirmation_code: Optional[str] = Field(None, min_length=6, max_length=6)
    
    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    # Sorting
    sort_by: str = Field(default="scheduled_datetime", pattern="^(scheduled_datetime|created_at|status|location_name)$")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")

class AppointmentSearchResponse(BaseModel):
    """Response for appointment search/listing"""
    appointments: List[AppointmentWithDetails]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

# ============================================================================
# CALENDAR SCHEMAS
# ============================================================================

class CalendarDay(BaseModel):
    """Single day in calendar view"""
    date: date
    day_of_week: str
    total_slots: int
    booked_slots: int
    available_slots: int
    appointments: List[AppointmentResponse]
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class CalendarWeek(BaseModel):
    """Weekly calendar view"""
    week_start: date
    week_end: date
    days: List[CalendarDay]
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class CalendarMonth(BaseModel):
    """Monthly calendar view"""
    year: int
    month: int
    month_name: str
    weeks: List[CalendarWeek]
    total_appointments: int
    
# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class AppointmentStats(BaseModel):
    """Appointment statistics"""
    total_appointments: int
    by_status: Dict[str, int]
    by_location: Dict[str, int]
    upcoming_appointments: int
    today_appointments: int
    overdue_appointments: int
    no_show_rate: float
    average_reschedules_per_appointment: float

class LocationPerformance(BaseModel):
    """Performance metrics for pickup locations"""
    location_id: uuid.UUID
    location_name: str
    total_appointments: int
    completion_rate: float
    no_show_rate: float
    average_wait_time_minutes: float
    utilization_rate: float  # Percentage of slots used
    
    class Config:
        json_encoders = {
            uuid.UUID: lambda v: str(v)
        }

# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================

class AppointmentNotification(BaseModel):
    """Notification related to appointments"""
    appointment_id: uuid.UUID
    notification_type: str  # reminder, confirmation, cancellation
    message: str
    recipient_phone: str
    send_at: datetime  # When to send the notification
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }

class BulkRescheduleRequest(BaseModel):
    """Request to reschedule multiple appointments (e.g., due to closure)"""
    original_date: date
    location_id: Optional[uuid.UUID] = None
    reason: str = Field(..., min_length=10, max_length=500)
    notify_applicants: bool = True
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }