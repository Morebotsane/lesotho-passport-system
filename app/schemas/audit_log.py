# app/schemas/audit_log.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.security.audit_logging import AuditEventType, AuditSeverity

class AuditLogResponse(BaseModel):
    """Schema for audit log API responses"""
    id: UUID
    event_type: str
    severity: str
    event_description: str
    user_id: Optional[UUID]
    user_email: Optional[str]
    user_role: Optional[str]
    client_ip: str
    request_path: Optional[str]
    response_status_code: Optional[int]
    response_time_ms: Optional[int]
    resource_type: Optional[str]
    resource_id: Optional[str]
    event_metadata: Optional[Dict[str, Any]]
    is_sensitive: bool
    requires_review: bool
    timestamp: datetime
    
    class Config:
        from_attributes = True

class AuditLogSearch(BaseModel):
    """Schema for audit log search parameters"""
    user_id: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    client_ip: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    requires_review: Optional[bool] = None
    is_sensitive: Optional[bool] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)