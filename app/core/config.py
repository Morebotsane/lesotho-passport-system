# app/core/config.py - CORRECTED VERSION
from typing import Any, Dict, Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings using Pydantic for validation and environment management
    """
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Passport Notification System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A REST API for managing passport notifications and scheduling"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECURITY_LEVEL: str = "development"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    
    # Password Requirements
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_DIGITS: bool = True
    REQUIRE_SPECIAL_CHARS: bool = True
    
    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: Optional[str] = None
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_CACHE_DB: int = 1
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_URL: str = "redis://localhost:6379"
    
    # Cache Configuration  
    CACHE_DEFAULT_TTL: int = 3600  # 1 hour
    CACHE_USER_TTL: int = 1800     # 30 minutes
    CACHE_STATS_TTL: int = 300     # 5 minutes
    
    # Session Configuration
    SESSION_TTL: int = 86400       # 24 hours
    SESSION_REFRESH_TTL: int = 3600 # Refresh if accessed within 1 hour of expiry
    
    # SMS Service (Twilio)
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 1000
    RATE_LIMIT_PER_HOUR: int = 10000
    
    # Application Business Rules
    DEFAULT_PICKUP_DEADLINE_DAYS: int = 30
    MAX_PROCESSING_DAYS_NORMAL: int = 21
    MAX_PROCESSING_DAYS_HIGH: int = 14
    MAX_PROCESSING_DAYS_URGENT: int = 7
    MAX_PROCESSING_DAYS_EMERGENCY: int = 3
    
    # Notification Settings
    SMS_RETRY_ATTEMPTS: int = 3
    SMS_RETRY_DELAY_MINUTES: int = 5

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # File Upload Settings
    UPLOAD_DIR: str = "uploads/passport_documents"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf"]
        
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError("SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @property
    def redis_url_computed(self) -> str:
        """Build Redis URL from components"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    def get_upload_path(self) -> Path:
        """Get absolute path for uploads directory"""
        base_dir = Path(__file__).resolve().parent.parent.parent
        upload_path = base_dir / self.UPLOAD_DIR
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Database configuration
def get_database_url() -> str:
    """Get the appropriate database URL based on environment"""
    if settings.ENVIRONMENT == "testing" and settings.TEST_DATABASE_URL:
        return settings.TEST_DATABASE_URL
    return settings.DATABASE_URL