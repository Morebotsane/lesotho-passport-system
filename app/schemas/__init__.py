# app/schemas/__init__.py
from app.schemas.user import *
from app.schemas.passport_application import *
from app.schemas.dashboard import *

__all__ = [
    # User schemas
    "UserCreate", 
    "UserLogin", 
    "UserResponse", 
    "LoginResponse", 
    "UserUpdate", 
    "PasswordChange",
    "UserSummary",
    "UserStats",
    "UserRoleUpdate",
    "UserStatusUpdate",
    
    # Passport application schemas
    "PassportApplicationCreate",
    "PassportApplicationResponse", 
    "PassportApplicationSummary",
    "PassportApplicationWithApplicant",
    "PassportApplicationUpdate",
    "ApplicationFilter",
    "ApplicationSearchResponse",
    "FastTrackRequest",
    "ApplicationStats",
    "ProcessingMetrics",
    "NotificationPreview",
    "BulkNotificationRequest",
    
    # Dashboard schemas
    "DashboardOverview",
    "RecentApplicationSummary", 
    "DashboardData",
    "WorkloadApplication",
    "WorkloadAssignment",
    "SystemAlertSummary",
    "AlertAcknowledgment",
    "SLACompliance",
    "ProcessingStatistics",
    "FraudApplication",
    "FraudDetectionReport",
    "DailySubmission",
    "PriorityDistribution",
    "ApplicationTrends",
    "TrendAnalysis",
    "ExportApplication",
    "ExportFilters",
    "ApplicationExport"
]