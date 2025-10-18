# app/security/input_validation.py - UPDATED VERSION
"""
Input Validation Hardening for Lesotho Passport Processing System
Comprehensive security validation with Lesotho-specific rules
Updated to focus on notification system needs, not personal data storage
"""
import re
import html
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, validator, Field
from email_validator import validate_email, EmailNotValidError
from app.models.passport_application import PriorityReason
import phonenumbers
from phonenumbers import NumberParseException

# Import enums from models
from app.models.passport_application import PriorityReason

class SecurityError(Exception):
    """Custom exception for security-related validation failures"""
    pass

class LesothoValidators:
    """Lesotho-specific validation rules"""
    
    # Lesotho passport number format: LP followed by 8 digits
    PASSPORT_PATTERN = re.compile(r'^LP\d{8}$')
    
    # Lesotho national ID patterns (various historical formats)
    NATIONAL_ID_PATTERNS = [
        re.compile(r'^\d{13}$'),        # 13-digit format
        re.compile(r'^\d{8}$'),         # 8-digit format  
        re.compile(r'^[A-Z]{2}\d{6}$'), # Letter prefix format
    ]
    
    # Valid Lesotho districts
    VALID_DISTRICTS = {
        'maseru', 'leribe', 'berea', 'mafeteng', 'mohale\'s hoek',
        'quthing', 'qacha\'s nek', 'mokhotlong', 'thaba-tseka', 'butha-buthe'
    }
    
    @staticmethod
    def validate_passport_number(passport_num: str) -> bool:
        """Validate Lesotho passport number format"""
        if not passport_num:
            return False
        return bool(LesothoValidators.PASSPORT_PATTERN.match(passport_num.upper().strip()))
    
    @staticmethod
    def validate_national_id(national_id: str) -> bool:
        """Validate Lesotho national ID format"""
        if not national_id:
            return False
        
        national_id = national_id.upper().strip()
        return any(pattern.match(national_id) for pattern in LesothoValidators.NATIONAL_ID_PATTERNS)
    
    @staticmethod
    def validate_lesotho_phone(phone: str) -> tuple[bool, Optional[str]]:
        """Validate and format Lesotho phone number"""
        try:
            # Parse phone number for Lesotho (country code: +266)
            parsed_number = phonenumbers.parse(phone, 'LS')
            
            # Check if it's a valid Lesotho number
            if not phonenumbers.is_valid_number(parsed_number):
                return False, None
                
            # Format in E164 format for storage
            formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            return True, formatted
            
        except NumberParseException:
            return False, None
    
    @staticmethod
    def validate_lesotho_address(address: str) -> tuple[bool, str]:
        """Validate Lesotho address contains valid location"""
        if not address or len(address.strip()) < 10:
            return False, "Address too short (minimum 10 characters)"
        
        address_lower = address.lower()
        
        # Check if contains valid Lesotho district or major town
        has_valid_location = any(
            district in address_lower 
            for district in LesothoValidators.VALID_DISTRICTS
        )
        
        if not has_valid_location:
            return False, "Address must contain a valid Lesotho district"
        
        return True, address.strip()

class SecuritySanitizer:
    """Advanced input sanitization for security threats"""
    
    # Dangerous patterns for XSS detection
    XSS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'vbscript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
        re.compile(r'expression\s*\(', re.IGNORECASE),  # CSS expressions
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        re.compile(r'(\b(ALTER|CREATE|DELETE|DROP|EXEC(UTE)?|INSERT|SELECT|UNION|UPDATE)\b)', re.IGNORECASE),
        re.compile(r'(\b(OR|AND)\s+[\'"]?\d+[\'"]?\s*=\s*[\'"]?\d+[\'"]?)', re.IGNORECASE),
        re.compile(r'[\'";][\s]*((DROP|EXEC|EXECUTE)\s)', re.IGNORECASE),
    ]
    
    @staticmethod
    def detect_xss_attempts(input_data: str) -> bool:
        """Detect potential XSS attempts"""
        if not input_data:
            return False
        return any(pattern.search(input_data) for pattern in SecuritySanitizer.XSS_PATTERNS)
    
    @staticmethod
    def detect_sql_injection(input_data: str) -> bool:
        """Detect potential SQL injection attempts"""
        if not input_data:
            return False
        return any(pattern.search(input_data) for pattern in SecuritySanitizer.SQL_PATTERNS)
    
    @staticmethod
    def sanitize_text(input_data: str, max_length: int = 1000) -> str:
        """Sanitize text input with security checks"""
        if not input_data:
            return ""
        
        # Check for malicious patterns
        if SecuritySanitizer.detect_xss_attempts(input_data):
            raise SecurityError("Potentially malicious XSS content detected")
        
        if SecuritySanitizer.detect_sql_injection(input_data):
            raise SecurityError("Potentially malicious SQL patterns detected")
        
        # HTML escape and clean
        sanitized = html.escape(input_data.strip())
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized

# Secure Pydantic Models for Passport System

class SecurePassportApplication(BaseModel):
    """
    Security-hardened passport application model for notification system
    Focuses on application preferences, not personal identification data
    Personal info comes from the user account that submits the application
    """
    
    # Application preferences (what type of passport they want)
    passport_type: str = Field(..., pattern=r'^(regular|diplomatic|official)$')
    pages: int = Field(default=32, ge=32, le=64)
    priority_reason: Optional[PriorityReason] = None
    
    # Emergency contact for urgent notifications
    emergency_contact_name: str = Field(..., min_length=2, max_length=100)
    emergency_contact_phone: str = Field(..., min_length=8, max_length=20)
    
    # Travel context (helps with notification timing)
    travel_purpose: Optional[str] = Field(None, max_length=200)
    intended_travel_date: Optional[datetime] = None
    
    class Config:
        validate_assignment = True
        str_strip_whitespace = True
    
    @validator('passport_type')
    def validate_passport_type(cls, v):
        """Validate and sanitize passport type"""
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=20)
        valid_types = ['regular', 'diplomatic', 'official']
        if sanitized.lower() not in valid_types:
            raise ValueError(f"Passport type must be one of: {', '.join(valid_types)}")
        return sanitized.lower()
    
    @validator('pages')
    def validate_pages(cls, v):
        """Validate passport pages"""
        if v not in [32, 64]:
            raise ValueError('Pages must be either 32 or 64')
        return v
    
    @validator('emergency_contact_name')
    def validate_emergency_contact_name(cls, v):
        """Validate emergency contact name"""
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=100)
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", sanitized):
            raise ValueError("Emergency contact name contains invalid characters")
        return sanitized
    
    @validator('emergency_contact_phone')
    def validate_emergency_contact_phone(cls, v):
        """Validate emergency contact phone number"""
        sanitized = SecuritySanitizer.sanitize_text(v)
        is_valid, formatted = LesothoValidators.validate_lesotho_phone(sanitized)
        if not is_valid:
            raise ValueError("Invalid Lesotho phone number format for emergency contact")
        return formatted
    
    @validator('travel_purpose')
    def validate_travel_purpose(cls, v):
        """Validate travel purpose if provided"""
        if not v:
            return None
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=200)
        if len(sanitized.strip()) < 3:
            raise ValueError("Travel purpose must be at least 3 characters")
        return sanitized
    
    @validator('intended_travel_date')
    def validate_intended_travel_date(cls, v):
        """Validate intended travel date if provided"""
        if not v:
            return None
        if v.replace(tzinfo=None) <= datetime.now():
            raise ValueError('Intended travel date must be in the future')
        max_future = datetime.now().replace(year=datetime.now().year + 10)
        if v.replace(tzinfo=None) > max_future:
            raise ValueError('Intended travel date cannot be more than 10 years in the future')
        return v

class SecureUserRegistration(BaseModel):
    """Security-hardened user registration model"""
    
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=100)
    phone_number: str = Field(..., min_length=8, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name"""
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=100)
        
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", sanitized):
            raise ValueError("Name contains invalid characters")
        
        return sanitized
    
    @validator('email')
    def validate_email_registration(cls, v):
        """Validate email for registration"""
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=100)
        
        try:
            valid_email = validate_email(sanitized)
            return valid_email.email.lower()
        except EmailNotValidError:
            raise ValueError("Invalid email address format")
    
    @validator('phone_number')
    def validate_phone_registration(cls, v):
        """Validate phone number for registration"""
        sanitized = SecuritySanitizer.sanitize_text(v)
        
        is_valid, formatted = LesothoValidators.validate_lesotho_phone(sanitized)
        if not is_valid:
            raise ValueError("Invalid Lesotho phone number format")
        
        return formatted
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets security requirements"""
        # Don't sanitize passwords - preserve exact input
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', v):
            raise ValueError("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = {
            'password123', '12345678', 'qwerty123', 'admin123',
            'letmein123', 'welcome123', 'password!', 'Password1'
        }
        
        if v.lower() in [p.lower() for p in weak_passwords]:
            raise ValueError("Password is too common, please choose a stronger password")
        
        return v
    
    @validator('confirm_password')
    def validate_password_confirmation(cls, v, values):
        """Validate password confirmation matches"""
        if 'password' in values and v != values['password']:
            raise ValueError("Password confirmation does not match")
        return v

# Utility functions for validation

def validate_input_data(data: dict, model_class) -> dict:
    """Validate input data against security model"""
    try:
        validated_model = model_class(**data)
        return validated_model.dict()
    except Exception as e:
        raise SecurityError(f"Input validation failed: {str(e)}")

def create_data_hash(data: dict) -> str:
    """Create hash for duplicate detection"""
    import hashlib
    import json
    
    # Sort keys for consistent hashing
    sorted_data = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(sorted_data.encode()).hexdigest()

# Test the validators (remove in production)
if __name__ == "__main__":
    # Test Lesotho validators
    print("Testing Lesotho validators:")
    print(f"LP12345678: {LesothoValidators.validate_passport_number('LP12345678')}")
    print(f"Invalid passport: {LesothoValidators.validate_passport_number('XX123456')}")
    
    # Test phone validation
    is_valid, formatted = LesothoValidators.validate_lesotho_phone("+266 5123 4567")
    print(f"Phone +266 5123 4567: {is_valid}, formatted: {formatted}")
    
    print("✅ Input validation system ready!")
    pages: int = Field(default=32, ge=32, le=64)
    priority_reason: Optional[PriorityReason] = None
    
    # Emergency contact for urgent notifications
    emergency_contact_name: str = Field(..., min_length=2, max_length=100)
    emergency_contact_phone: str = Field(..., min_length=8, max_length=20)
    
    # Travel context (helps with notification timing)
    travel_purpose: Optional[str] = Field(None, max_length=200)
    intended_travel_date: Optional[datetime] = None
    
    class Config:
        # Enable validation on assignment
        validate_assignment = True
        # Strip whitespace from strings
        str_strip_whitespace = True
    
    @validator('passport_type')
    def validate_passport_type(cls, v):
        """Validate and sanitize passport type"""
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=20)
        
        valid_types = ['regular', 'diplomatic', 'official']
        if sanitized.lower() not in valid_types:
            raise ValueError(f"Passport type must be one of: {', '.join(valid_types)}")
        
        return sanitized.lower()
    
    @validator('pages')
    def validate_pages(cls, v):
        """Validate passport pages"""
        if v not in [32, 64]:
            raise ValueError('Pages must be either 32 or 64')
        return v
    
    @validator('priority_reason')
    def validate_priority_reason(cls, v):
        """Validate priority reason if provided"""
        if not v:
            return None
            
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=50)
        
        valid_reasons = [
            'migrant_worker', 'student_abroad', 'medical_treatment', 
            'emergency_travel', 'official_duty'
        ]
        
        if sanitized.lower() not in valid_reasons:
            raise ValueError(f"Priority reason must be one of: {', '.join(valid_reasons)}")
        
        return sanitized.lower()
    
    @validator('emergency_contact_name')
    def validate_emergency_contact_name(cls, v):
        """Validate emergency contact name"""
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=100)
        
        # Check name pattern (letters, spaces, hyphens, apostrophes only)
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", sanitized):
            raise ValueError("Emergency contact name contains invalid characters")
        
        return sanitized
    
    @validator('emergency_contact_phone')
    def validate_emergency_contact_phone(cls, v):
        """Validate emergency contact phone number"""
        sanitized = SecuritySanitizer.sanitize_text(v)
        
        is_valid, formatted = LesothoValidators.validate_lesotho_phone(sanitized)
        if not is_valid:
            raise ValueError("Invalid Lesotho phone number format for emergency contact")
        
        return formatted
    
    @validator('travel_purpose')
    def validate_travel_purpose(cls, v):
        """Validate travel purpose if provided"""
        if not v:
            return None
            
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=200)
        
        # Basic length check
        if len(sanitized.strip()) < 3:
            raise ValueError("Travel purpose must be at least 3 characters")
        
        return sanitized
    
    @validator('intended_travel_date')
    def validate_intended_travel_date(cls, v):
        """Validate intended travel date if provided"""
        if not v:
            return None
        
        # Must be in the future
        if v.replace(tzinfo=None) <= datetime.now():
            raise ValueError('Intended travel date must be in the future')
        
        # Not too far in the future (10 years max)
        max_future = datetime.now().replace(year=datetime.now().year + 10)
        if v.replace(tzinfo=None) > max_future:
            raise ValueError('Intended travel date cannot be more than 10 years in the future')
        
        return v

class SecureUserRegistration(BaseModel):
    """Security-hardened user registration model"""
    
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=100)
    phone_number: str = Field(..., min_length=8, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name"""
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=100)
        
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", sanitized):
            raise ValueError("Name contains invalid characters")
        
        return sanitized
    
    @validator('email')
    def validate_email_registration(cls, v):
        """Validate email for registration"""
        sanitized = SecuritySanitizer.sanitize_text(v, max_length=100)
        
        try:
            valid_email = validate_email(sanitized)
            return valid_email.email.lower()
        except EmailNotValidError:
            raise ValueError("Invalid email address format")
    
    @validator('phone_number')
    def validate_phone_registration(cls, v):
        """Validate phone number for registration"""
        sanitized = SecuritySanitizer.sanitize_text(v)
        
        is_valid, formatted = LesothoValidators.validate_lesotho_phone(sanitized)
        if not is_valid:
            raise ValueError("Invalid Lesotho phone number format")
        
        return formatted
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets security requirements"""
        # Don't sanitize passwords - preserve exact input
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', v):
            raise ValueError("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = {
            'password123', '12345678', 'qwerty123', 'admin123',
            'letmein123', 'welcome123', 'password!', 'Password1'
        }
        
        if v.lower() in [p.lower() for p in weak_passwords]:
            raise ValueError("Password is too common, please choose a stronger password")
        
        return v
    
    @validator('confirm_password')
    def validate_password_confirmation(cls, v, values):
        """Validate password confirmation matches"""
        if 'password' in values and v != values['password']:
            raise ValueError("Password confirmation does not match")
        return v

# Utility functions for validation

def validate_input_data(data: dict, model_class) -> dict:
    """Validate input data against security model"""
    try:
        validated_model = model_class(**data)
        return validated_model.dict()
    except Exception as e:
        raise SecurityError(f"Input validation failed: {str(e)}")

def create_data_hash(data: dict) -> str:
    """Create hash for duplicate detection"""
    import hashlib
    import json
    
    # Sort keys for consistent hashing
    sorted_data = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(sorted_data.encode()).hexdigest()

# Test the validators (remove in production)
if __name__ == "__main__":
    # Test Lesotho validators
    print("Testing Lesotho validators:")
    print(f"LP12345678: {LesothoValidators.validate_passport_number('LP12345678')}")
    print(f"Invalid passport: {LesothoValidators.validate_passport_number('XX123456')}")
    
    # Test phone validation
    is_valid, formatted = LesothoValidators.validate_lesotho_phone("+266 5123 4567")
    print(f"Phone +266 5123 4567: {is_valid}, formatted: {formatted}")
    
    print("✅ Input validation system ready!")