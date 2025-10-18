# app/schemas/user.py
"""
Pydantic schemas for user-related API operations
These define the structure of data coming in and going out of the API
"""
from email_validator import validate_email, EmailNotValidError
from app.security.input_validation import LesothoValidators, SecuritySanitizer
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
import uuid
import re

from app.models.user import UserRole

# ============================================================================
# BASE SCHEMAS
# ============================================================================

class PickupLocationBase(BaseModel):
    """Basic location info for user response"""
    id: uuid.UUID
    name: str
    address: str
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    role: UserRole = UserRole.APPLICANT
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format for Lesotho"""
        # Remove spaces, dashes and plus signs
        phone = re.sub(r'[\s\-\+]', '', v)
        
        # Accept:
        #- 8 digits (Local Lesotho): 59123456
        #- 11 digits (with country code): 266591234456
        if not re.match(r'^(266)?[5-9]\d{7}$', phone):
            raise ValueError('Phone number must be valid Lesotho format (8 digits or country code + 8 digits)')
        
        return phone
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        if not v.strip():
            raise ValueError('Name cannot be empty or just spaces')
        
        # Allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        
        return v.strip().title()  # Capitalize properly

# ============================================================================
# REQUEST SCHEMAS (Data coming INTO the API)
# ============================================================================

class UserCreate(UserBase):
    email: str
    first_name: str  
    last_name: str     
    phone: str       
    role: UserRole = UserRole.APPLICANT  

    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('phone')
    def validate_phone_number(cls, v):
        is_valid, formatted = LesothoValidators.validate_lesotho_phone(v)
        if not is_valid:
            raise ValueError("Invalid Lesotho phone number format")
        return formatted
    
    @validator('email')
    def validate_email_address(cls, v):
        """Validate email format and security"""
        # Sanitize first
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=100)
        
        # Validate email format
        try:
            valid_email = validate_email(sanitized)
            return valid_email.email.lower()  # Normalize to lowercase
        except EmailNotValidError:
            raise ValueError("Invalid email address format")
        
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=50)
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", sanitized):
            raise ValueError("Name contains invalid characters")
        return sanitized

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Ensure password and confirm_password match"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str = Field(..., min_length=1)

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v is None:
            return v
            
        # Remove spaces and dashes
        phone = re.sub(r'[\s-]', '', v)
        
        # Check if it matches international format or local format
        if not re.match(r'^(\+\d{1,3})?\d{9,12}$', phone):
            raise ValueError('Phone number must be valid (9-12 digits with optional country code)')
        
        return phone
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        if v is None:
            return v
            
        if not v.strip():
            raise ValueError('Name cannot be empty or just spaces')
        
        # Allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        
        return v.strip().title()

class PasswordChange(BaseModel):
    """Schema for changing user password"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        """Ensure new_password and confirm_new_password match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v

# ============================================================================
# RESPONSE SCHEMAS (Data going OUT of the API)
# ============================================================================

# In app/schemas/user.py, update the UserResponse class:
class UserResponse(UserBase):
    """Schema for user data in API responses"""
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    assigned_location_id: Optional[uuid.UUID] = None  # ADD THIS
    assigned_location: Optional[PickupLocationBase] = None  # ADD THIS
    
    @classmethod
    def from_orm(cls, obj):
        """Create from SQLAlchemy model"""
        return cls(
            id=obj.id,
            email=obj.email,
            first_name=obj.first_name,
            last_name=obj.last_name,
            phone=obj.phone,
            role=obj.role,
            is_active=obj.is_active,
            is_verified=obj.is_verified,
            created_at=obj.created_at,
            last_login=obj.last_login,
            assigned_location_id=obj.assigned_location_id,  # ADD THIS
            assigned_location=obj.assigned_location  # ADD THIS
        )
    
    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: lambda v: str(v)
        }

class UserSummary(BaseModel):
    """Minimal user info for listings"""
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    
    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: lambda v: str(v)
        }

class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse

class UserStats(BaseModel):
    """User statistics for admin dashboard"""
    total_users: int
    active_users: int
    applicants: int
    officers: int
    admins: int
    recent_registrations: int  # Last 30 days
    
# ============================================================================
# ADMIN SCHEMAS
# ============================================================================

class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin only)"""
    role: UserRole
    
class UserStatusUpdate(BaseModel):
    """Schema for updating user status (admin only)"""
    is_active: bool
    is_verified: bool
    