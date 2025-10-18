# app/schemas/passport_application.py
"""
Pydantic schemas for passport application operations
These define the API contracts for passport-related endpoints
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.models.passport_application import ApplicationStatus, PriorityLevel, PriorityReason

# ============================================================================
# BASE SCHEMAS
# ============================================================================

class LocationBasic(BaseModel):
    """Basic location information"""
    id: uuid.UUID
    name: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    
    class Config:
        from_attributes = True

class PassportApplicationBase(BaseModel):
    """Base passport application schema"""
    passport_type: str = Field(default="regular", pattern="^(regular|diplomatic|official)$")
    pages: int = Field(default=32, ge=32, le=64, description="Number of pages (32 or 64)")
    priority_reason: Optional[PriorityReason] = None
    
    @validator('pages')
    def validate_pages(cls, v):
        """Validate passport pages"""
        if v not in [32, 64]:
            raise ValueError('Pages must be either 32 or 64')
        return v

# ============================================================================
# REQUEST SCHEMAS (Data coming INTO the API)
# ============================================================================

class PassportApplicationCreate(PassportApplicationBase):
    """Schema for creating a new passport application - Complete with personal info"""
    
    # ========================================================================
    # PERSONAL INFORMATION (Snapshot at application time)
    # ========================================================================
    first_name: str = Field(..., min_length=2, max_length=50, description="Applicant's first name")
    last_name: str = Field(..., min_length=2, max_length=50, description="Applicant's last name")
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    place_of_birth: str = Field(..., min_length=2, max_length=100, description="City, Country")
    nationality: str = Field(default="Lesotho", max_length=50)
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    
    # ========================================================================
    # CONTACT INFORMATION
    # ========================================================================
    email: str = Field(..., description="Contact email")
    phone: str = Field(..., min_length=8, max_length=20, description="Contact phone number")
    residential_address: str = Field(..., min_length=10, max_length=200, description="Full residential address")
    
    # ========================================================================
    # SUBMISSION LOCATION
    # ========================================================================
    submission_location_id: uuid.UUID = Field(..., description="Passport office where application will be lodged")

    # ========================================================================
    # IDENTIFICATION
    # ========================================================================
    national_id_number: Optional[str] = Field(None, max_length=20, description="National ID number")
    previous_passport_number: Optional[str] = Field(None, max_length=20, description="Previous passport number if renewal")
    
    # ========================================================================
    # PASSPORT DETAILS
    # ========================================================================
    reason_for_issuance: str = Field(..., pattern="^(new|renewal|lost|damaged|name_change)$")
    
    # ========================================================================
    # EMERGENCY CONTACT
    # ========================================================================
    emergency_contact_name: Optional[str] = Field(None, min_length=2, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, min_length=8, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50, description="e.g., spouse, parent, sibling")
    
    # ========================================================================
    # TRAVEL INFORMATION (Optional)
    # ========================================================================
    travel_purpose: Optional[str] = Field(None, max_length=200)
    intended_travel_date: Optional[datetime] = None
    
    # ========================================================================
    # ADDITIONAL INFORMATION
    # ========================================================================
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes or special requests")
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth format and age"""
        from datetime import datetime
        try:
            birth_date = datetime.strptime(v, '%Y-%m-%d')
            age = (datetime.now() - birth_date).days / 365.25
            if age < 0:
                raise ValueError('Date of birth cannot be in the future')
            if age > 120:
                raise ValueError('Invalid date of birth - age too old')
            if age < 16:
                raise ValueError('Applicant must be at least 16 years old')
            return v
        except ValueError as e:
            if 'does not match format' in str(e):
                raise ValueError('Date must be in YYYY-MM-DD format')
            raise
    
    @validator('intended_travel_date')    
    def validate_travel_date(cls, v):
        """Validate intended travel date is in the future"""
        if v and v.replace(tzinfo=None) <= datetime.now():
            raise ValueError('Intended travel date must be in the future')
        return v
    
    @validator('phone', 'emergency_contact_phone')
    def validate_phone_format(cls, v):
        """Validate Lesotho phone number format"""
        if v:
            import re
            phone = re.sub(r'[\s\-\+]', '', v)
            if not re.match(r'^(266)?[5-9]\d{7}$', phone):
                raise ValueError('Phone must be valid Lesotho format (8 digits starting with 5-9)')
        return v

class PassportApplicationUpdate(BaseModel):
    """Schema for updating passport application (officer only)"""
    status: Optional[ApplicationStatus] = None
    priority_level: Optional[PriorityLevel] = None
    priority_reason: Optional[PriorityReason] = None
    processing_stages: Optional[Dict[str, Any]] = None
    estimated_completion_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)

class FastTrackRequest(BaseModel):
    """Schema for fast-track approval request"""
    reason: str = Field(..., min_length=10, max_length=500)
    priority_level: PriorityLevel = Field(..., description="Requested priority level")
    justification: str = Field(..., min_length=20, max_length=1000)

# ============================================================================
# RESPONSE SCHEMAS (Data going OUT of the API)
# ============================================================================

class PassportApplicationResponse(PassportApplicationBase):
    """Complete passport application data for API responses"""
    id: uuid.UUID
    application_number: str
    applicant_id: uuid.UUID
    status: ApplicationStatus
    priority_level: PriorityLevel
    processing_stages: Dict[str, Any]
    is_fast_tracked: bool
    
    # Dates
    submitted_at: datetime
    estimated_completion_date: Optional[datetime]
    actual_completion_date: Optional[datetime]
    pickup_deadline: Optional[datetime]
    collected_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    days_in_processing: int
    is_overdue: bool
    pickup_expires_in_days: int
    
    # Personal info
    first_name: str 
    last_name: str 
    gender: Optional[str] = None 
    date_of_birth: str 
    place_of_birth: str 
    nationality: str 
    email: str
    phone: str
    residential_address: str
    national_id_number: Optional[str] = None
    
    # Location information - ADD THIS
    submission_location_id: Optional[uuid.UUID] = None
    submission_location: Optional[LocationBasic] = None 
    
    # Passport details 
    #passport_type: PassportType 
    pages: int 
    reason_for_issuance: str 
    previous_passport_number: Optional[str] = None

    # Documents uploaded
    passport_photo_path: Optional[str] = None 
    id_document_path: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: lambda v: str(v)
        }

class PassportApplicationSummary(BaseModel):
    """Application summary for listings - includes key personal info"""
    id: uuid.UUID
    application_number: str
    
    # Personal info
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: str
    place_of_birth: str
    residential_address: str
    
    # Passport details
    reason_for_issuance: str
    
    # Status tracking
    status: ApplicationStatus
    priority_level: PriorityLevel
    submitted_at: datetime
    days_in_processing: Optional[int] = 0
    is_overdue: Optional[bool] = False
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: lambda v: str(v)
        }


class PassportApplicationWithApplicant(PassportApplicationResponse):
    """Application data with applicant information (for officers)"""
    applicant_name: str
    applicant_email: str
    applicant_phone: str
    
    @classmethod
    def from_application_and_user(cls, application, user):
        """Create from application and user models"""
        app_data = PassportApplicationResponse.from_orm(application).dict()
        app_data.update({
            "applicant_name": user.full_name,
            "applicant_email": user.email,
            "applicant_phone": user.phone
        })
        return cls(**app_data)

# ============================================================================
# STATISTICS & ANALYTICS SCHEMAS
# ============================================================================

class ApplicationStats(BaseModel):
    """Application statistics for dashboards"""
    total_applications: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    average_processing_days: float
    overdue_applications: int
    fast_tracked_applications: int
    completed_this_month: int

class ProcessingMetrics(BaseModel):
    """Processing performance metrics"""
    applications_submitted_today: int
    applications_completed_today: int
    average_processing_time_days: float
    fastest_processing_time_hours: int
    slowest_processing_time_days: int
    efficiency_score: float  # Percentage of applications completed within SLA

# ============================================================================
# SEARCH & FILTER SCHEMAS
# ============================================================================

class ApplicationFilter(BaseModel):
    """Filter parameters for application searches"""
    status: Optional[List[ApplicationStatus]] = None
    priority_level: Optional[List[PriorityLevel]] = None
    priority_reason: Optional[List[PriorityReason]] = None
    is_fast_tracked: Optional[bool] = None
    is_overdue: Optional[bool] = None
    submitted_after: Optional[datetime] = None
    submitted_before: Optional[datetime] = None
    applicant_email: Optional[str] = None
    
    # Pagination
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    
    # Sorting
    sort_by: str = Field(default="submitted_at", pattern="^(submitted_at|status|priority_level|days_in_processing|application_number)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class ApplicationSearchResponse(BaseModel):
    """Response for application search/listing"""
    applications: List[PassportApplicationWithApplicant]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================

class NotificationPreview(BaseModel):
    """Preview of notification that would be sent"""
    recipient_phone: str
    message: str
    notification_type: str
    estimated_cost: float = 0.0075  # Approximate SMS cost

class BulkNotificationRequest(BaseModel):
    """Request for bulk notifications"""
    application_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=100)
    message_template: str = Field(..., min_length=10, max_length=160)
    notification_type: str = Field(..., pattern="^(status_update|pickup_reminder|urgent_reminder)$")
    send_immediately: bool = True
