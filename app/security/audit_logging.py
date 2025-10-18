"""
Comprehensive Audit Logging System for Lesotho Passport Processing
Government-grade audit trails for compliance and security investigations
"""
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import Base
from app.core.config import settings

class AuditEventType(str, Enum):
    """Types of events to audit"""
    # Authentication events
    LOGIN_SUCCESS = "auth_login_success"
    LOGIN_FAILURE = "auth_login_failure"
    LOGOUT = "auth_logout"
    PASSWORD_CHANGE = "auth_password_change"
    ACCOUNT_LOCKED = "auth_account_locked"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DEACTIVATED = "user_deactivated"
    ROLE_CHANGED = "user_role_changed"
    
    # Passport application events
    APPLICATION_CREATED = "application_created"
    APPLICATION_UPDATED = "application_updated"
    APPLICATION_STATUS_CHANGED = "application_status_changed"
    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_APPROVED = "application_approved"
    APPLICATION_REJECTED = "application_rejected"
    
    # Document events
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_VERIFIED = "document_verified"
    DOCUMENT_REJECTED = "document_rejected"
    
    # System events
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    SYSTEM_ERROR = "system_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SECURITY_VIOLATION = "security_violation"
    
    # Officer actions
    OFFICER_ACTION = "officer_action"
    BULK_NOTIFICATION = "bulk_notification"
    FAST_TRACK_APPROVED = "fast_track_approved"
    
    # Data access
    DATA_EXPORT = "data_export"
    REPORT_GENERATED = "report_generated"

class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLog(Base):
    """Database model for audit logs"""
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default=AuditSeverity.MEDIUM.value)
    event_description = Column(Text, nullable=False)
    
    # User and session information
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Request information
    request_id = Column(String(255), nullable=True)
    client_ip = Column(String(45), nullable=False, index=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    request_params = Column(JSON, nullable=True)
    
    # Response information
    response_status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Additional context
    resource_type = Column(String(100), nullable=True)  # application, user, document, etc.
    resource_id = Column(String(255), nullable=True)
    old_values = Column(JSON, nullable=True)  # Previous state for updates
    new_values = Column(JSON, nullable=True)  # New state for updates
    event_metadata = Column(JSON, nullable=True)  # Additional event-specific data
    
    # Flags
    is_sensitive = Column(Boolean, default=False)  # Contains sensitive data
    requires_review = Column(Boolean, default=False)  # Flagged for security review
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class AuditLogger:
    """Main audit logging class"""
    
    def __init__(self, db_session: Session = None):
        self.db_session = db_session
        self.logger = logging.getLogger("audit")
        
        # Configure file logging with error handling
        if not self.logger.handlers:
            try:
                import os
                os.makedirs("logs", exist_ok=True)
                handler = logging.FileHandler("logs/audit.log")
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
            except Exception as e:
                # If file logging fails, just continue without it
                # Database logging will still work
                print(f"Warning: Could not set up file logging: {e}")
                self.logger.setLevel(logging.INFO)
    
    def log_event(
        self,
        event_type: AuditEventType,
        event_description: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        client_ip: Optional[str] = None,
        request_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        event_metadata: Optional[Dict] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        is_sensitive: bool = False,
        requires_review: bool = False
    ):
        """Log an audit event to both database and file"""
        
        print(f"🔍 AUDIT: Starting log_event for {event_type.value}")
        print(f"🔍 AUDIT: DB Session available: {self.db_session is not None}")
        
        audit_entry = AuditLog(
            event_type=event_type.value,
            severity=severity.value,
            event_description=event_description,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            client_ip=client_ip or "unknown",
            request_id=request_id,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            event_metadata=event_metadata,
            is_sensitive=is_sensitive,
            requires_review=requires_review
        )
        
        print(f"✅ AUDIT: Created audit entry with ID: {audit_entry.id}")
        
        # Save to database if session available
        if self.db_session:
            try:
                print(f"💾 AUDIT: Adding to database session...")
                self.db_session.add(audit_entry)
                print(f"💾 AUDIT: Committing to database...")
                self.db_session.commit()
                print(f"✅ AUDIT: Successfully committed to database!")
            except Exception as e:
                print(f"❌ AUDIT: Database save failed: {e}")
                self.logger.error(f"Failed to save audit log to database: {e}")
                try:
                    self.db_session.rollback()
                    print(f"🔄 AUDIT: Database rollback completed")
                except Exception as rollback_error:
                    print(f"❌ AUDIT: Rollback also failed: {rollback_error}")
        else:
            print(f"⚠️ AUDIT: No database session - skipping database save")
        
        # Always log to file as backup
        try:
            self._log_to_file(audit_entry)
            print(f"📝 AUDIT: Logged to file successfully")
        except Exception as file_error:
            print(f"❌ AUDIT: File logging failed: {file_error}")
        
        return audit_entry
    
    def _log_to_file(self, audit_entry: AuditLog):
        """Log audit entry to file"""
        log_data = {
            "timestamp": audit_entry.timestamp.isoformat() if audit_entry.timestamp else datetime.utcnow().isoformat(),
            "event_type": audit_entry.event_type,
            "severity": audit_entry.severity,
            "description": audit_entry.event_description,
            "user_id": str(audit_entry.user_id) if audit_entry.user_id else None,
            "user_email": audit_entry.user_email,
            "client_ip": audit_entry.client_ip,
            "resource": f"{audit_entry.resource_type}:{audit_entry.resource_id}" if audit_entry.resource_type else None,
        }
        
        self.logger.info(json.dumps(log_data))
    
    def log_authentication_event(
        self,
        event_type: AuditEventType,
        user_email: str,
        client_ip: str,
        success: bool,
        failure_reason: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log authentication-related events"""
        
        description = f"Authentication attempt for {user_email}"
        if success:
            description += " - SUCCESS"
            severity = AuditSeverity.LOW
        else:
            description += f" - FAILED: {failure_reason or 'Unknown reason'}"
            severity = AuditSeverity.MEDIUM
        
        return self.log_event(
            event_type=event_type,
            event_description=description,
            user_id=user_id,
            user_email=user_email,
            client_ip=client_ip,
            severity=severity,
            event_metadata=metadata or {},
            requires_review=not success  # Failed logins should be reviewed
        )
    
    def log_application_event(
        self,
        event_type: AuditEventType,
        application_id: str,
        user_id: str,
        user_email: str,
        description: str,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log passport application lifecycle events"""
        
        old_values = {"status": old_status} if old_status else None
        new_values = {"status": new_status} if new_status else None
        
        return self.log_event(
            event_type=event_type,
            event_description=description,
            user_id=user_id,
            user_email=user_email,
            resource_type="passport_application",
            resource_id=application_id,
            old_values=old_values,
            new_values=new_values,
            event_metadata=metadata,
            severity=AuditSeverity.MEDIUM,
            is_sensitive=True  # Passport applications contain sensitive data
        )
    
    def log_officer_action(
        self,
        action_description: str,
        officer_id: str,
        officer_email: str,
        client_ip: str,
        affected_resource_type: Optional[str] = None,
        affected_resource_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log officer/admin actions"""
        
        return self.log_event(
            event_type=AuditEventType.OFFICER_ACTION,
            event_description=f"Officer action: {action_description}",
            user_id=officer_id,
            user_email=officer_email,
            user_role="officer",
            client_ip=client_ip,
            resource_type=affected_resource_type,
            resource_id=affected_resource_id,
            event_metadata=metadata,
            severity=AuditSeverity.HIGH,  # Officer actions are high importance
            requires_review=True
        )
    
    def log_security_violation(
        self,
        violation_type: str,
        description: str,
        client_ip: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        request_path: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log security violations"""
        
        return self.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            event_description=f"Security violation - {violation_type}: {description}",
            user_id=user_id,
            user_email=user_email,
            client_ip=client_ip,
            request_path=request_path,
            event_metadata=metadata,
            severity=AuditSeverity.CRITICAL,
            requires_review=True
        )

class AuditMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic API request/response auditing"""
    
    def __init__(self, app, db_session_factory=None):
        super().__init__(app)
        self.db_session_factory = db_session_factory
        self.sensitive_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register", 
            "/api/v1/auth/change-password",
            "/api/v1/passport-applications/"
        }
        print(f"🔧 AUDIT MIDDLEWARE: Initialized with db_session_factory: {db_session_factory is not None}")
    
    async def dispatch(self, request: Request, call_next):
        """Audit all API requests and responses"""
        
        start_time = datetime.utcnow()
        request_id = str(uuid.uuid4())
        
        # Extract request information
        client_ip = self._get_client_ip(request)
        user_info = await self._extract_user_info(request)
        
        print(f"🌐 AUDIT MIDDLEWARE: Processing {request.method} {request.url.path}")
        
        # Skip auditing for certain paths
        if self._should_skip_audit(request.url.path):
            print(f"⏭️ AUDIT MIDDLEWARE: Skipping audit for {request.url.path}")
            return await call_next(request)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Log successful API request
            await self._log_api_request(
                request=request,
                response=response,
                request_id=request_id,
                client_ip=client_ip,
                user_info=user_info,
                response_time_ms=response_time_ms,
                is_error=False
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log API error
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            print(f"❌ AUDIT MIDDLEWARE: Exception occurred: {e}")
            
            await self._log_api_request(
                request=request,
                response=None,
                request_id=request_id,
                client_ip=client_ip,
                user_info=user_info,
                response_time_ms=response_time_ms,
                is_error=True,
                error_details=str(e)
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip.strip()
        
        return request.client.host if request.client else 'unknown'
    
    async def _extract_user_info(self, request: Request) -> Dict[str, Optional[str]]:
        """Extract user information from JWT token"""
        try:
            # Get Authorization header
            auth_header = request.headers.get('authorization', '')
            if not auth_header.startswith('Bearer '):
                return {"user_id": None, "user_email": None, "user_role": None}
            
            # Extract token (remove 'Bearer ' prefix)
            jwt_token = auth_header[7:]
            
            # Use your existing JWT verification function
            from app.core.security import verify_token
            
            # Decode the JWT token to get user_id
            user_id = verify_token(jwt_token)
            if user_id is None:
                return {"user_id": None, "user_email": None, "user_role": None}
            
            # Get database session to fetch user details
            if not self.db_session_factory:
                # If no DB session available, return just the user_id
                return {"user_id": user_id, "user_email": None, "user_role": None}
            
            # Query database for full user information
            db_session = None
            try:
                db_session = self.db_session_factory()
                
                # Import User model and query for user details
                from app.models.user import User
                user = db_session.query(User).filter(User.id == user_id).first()
                
                if user:
                    return {
                        "user_id": str(user.id),
                        "user_email": user.email,
                        "user_role": user.role.value if user.role else None
                    }
                else:
                    return {"user_id": user_id, "user_email": None, "user_role": None}
                    
            except Exception as db_error:
                print(f"⚠️ AUDIT: Database error fetching user details: {db_error}")
                return {"user_id": user_id, "user_email": None, "user_role": None}
            finally:
                if db_session:
                    db_session.close()
            
        except Exception as e:
            # If token is invalid/expired or any other error, log it but don't crash
            print(f"⚠️ AUDIT: Failed to extract user info from token: {e}")
            return {"user_id": None, "user_email": None, "user_role": None}
    
    def _should_skip_audit(self, path: str) -> bool:
        """Check if path should be skipped from auditing"""
        skip_paths = [
            "/health",
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/favicon.ico",
            "/static/"
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    async def _log_api_request(
        self,
        request: Request,
        response: Optional[Response],
        request_id: str,
        client_ip: str,
        user_info: Dict[str, Optional[str]],
        response_time_ms: int,
        is_error: bool,
        error_details: Optional[str] = None
    ):
        """Log API request to audit system"""
        
        print(f"📊 AUDIT MIDDLEWARE: Logging API request {request_id}")
        
        # Get database session if available
        db_session = None
        if self.db_session_factory:
            try:
                print(f"🔗 AUDIT MIDDLEWARE: Creating database session...")
                db_session = self.db_session_factory()
                print(f"✅ AUDIT MIDDLEWARE: Database session created successfully")
            except Exception as session_error:
                print(f"❌ AUDIT MIDDLEWARE: Failed to create database session: {session_error}")
                db_session = None
        else:
            print(f"⚠️ AUDIT MIDDLEWARE: No db_session_factory available")
        
        auditor = AuditLogger(db_session)
        
        # Determine if this is a sensitive path
        is_sensitive = any(sens_path in request.url.path for sens_path in self.sensitive_paths)
        
        # Build request parameters (sanitized for sensitive endpoints)
        request_params = dict(request.query_params) if not is_sensitive else {"[REDACTED]": "sensitive_endpoint"}
        
        # Extract user agent
        user_agent = request.headers.get("user-agent", "")
        
        # Create event description
        if is_error:
            event_type = AuditEventType.API_ERROR
            description = f"API Error: {request.method} {request.url.path} - {error_details}"
            severity = AuditSeverity.HIGH
        else:
            event_type = AuditEventType.API_REQUEST
            description = f"API Request: {request.method} {request.url.path}"
            severity = AuditSeverity.LOW
        
        # Create the audit entry with ALL fields populated
        try:
            audit_entry = AuditLog(
                event_type=event_type.value,
                severity=severity.value,
                event_description=description,
                
                # User information
                user_id=user_info["user_id"],
                user_email=user_info["user_email"],
                user_role=user_info["user_role"],
                
                # Request information
                request_id=request_id,
                client_ip=client_ip,
                user_agent=user_agent,
                request_method=request.method,
                request_path=request.url.path,
                request_params=request_params,
                
                # Response information
                response_status_code=response.status_code if response else None,
                response_time_ms=response_time_ms,
                
                # Additional metadata for complex data
                event_metadata={
                    "error_details": error_details if is_error else None,
                    "is_sensitive_endpoint": is_sensitive,
                    "request_headers": dict(request.headers) if not is_sensitive else {"[REDACTED]": "sensitive_endpoint"}
                },
                
                # Flags
                is_sensitive=is_sensitive
            )
            
            # Save to database if session available
            if db_session:
                try:
                    print(f"💾 AUDIT: Adding API request to database session...")
                    db_session.add(audit_entry)
                    print(f"💾 AUDIT: Committing API request to database...")
                    db_session.commit()
                    print(f"✅ AUDIT: Successfully committed API request to database!")
                except Exception as e:
                    print(f"❌ AUDIT: Database save failed: {e}")
                    try:
                        db_session.rollback()
                        print(f"🔄 AUDIT: Database rollback completed")
                    except Exception as rollback_error:
                        print(f"❌ AUDIT: Rollback also failed: {rollback_error}")
            else:
                print(f"⚠️ AUDIT: No database session - skipping database save")
            
            # Always log to file as backup
            try:
                auditor._log_to_file(audit_entry)
                print(f"📝 AUDIT: Logged API request to file successfully")
            except Exception as file_error:
                print(f"❌ AUDIT: File logging failed: {file_error}")
                
            print(f"✅ AUDIT MIDDLEWARE: Successfully logged API request")
            
        except Exception as audit_error:
            print(f"❌ AUDIT MIDDLEWARE: Failed to create audit entry: {audit_error}")
        
        # Close database session
        if db_session:
            try:
                db_session.close()
                print(f"🔒 AUDIT MIDDLEWARE: Database session closed")
            except Exception as close_error:
                print(f"⚠️ AUDIT MIDDLEWARE: Error closing database session: {close_error}")

# Utility functions for manual audit logging
def log_user_action(
    db: Session,
    action_type: AuditEventType,
    description: str,
    user_id: str,
    user_email: str,
    client_ip: str = "unknown",
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    metadata: Optional[Dict] = None
):
    """Helper function to log user actions from your application code"""
    
    auditor = AuditLogger(db)
    return auditor.log_event(
        event_type=action_type,
        event_description=description,
        user_id=user_id,
        user_email=user_email,
        client_ip=client_ip,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        event_metadata=metadata
    )

def get_audit_statistics(db: Session) -> Dict[str, Any]:
    """Get audit logging statistics"""
    
    # Total logs count
    total_logs = db.query(AuditLog).count()
    
    # Logs by severity
    severity_counts = {}
    for severity in AuditSeverity:
        count = db.query(AuditLog).filter(AuditLog.severity == severity.value).count()
        severity_counts[severity.value] = count
    
    # Recent security violations
    recent_violations = db.query(AuditLog).filter(
        AuditLog.event_type == AuditEventType.SECURITY_VIOLATION.value
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    # Logs requiring review
    pending_review = db.query(AuditLog).filter(AuditLog.requires_review == True).count()
    
    return {
        "total_audit_logs": total_logs,
        "logs_by_severity": severity_counts,
        "pending_review": pending_review,
        "recent_security_violations": len(recent_violations),
        "generated_at": datetime.utcnow().isoformat()
    }

def search_audit_logs(
    db: Session,
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    client_ip: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[AuditLog]:
    """Search audit logs with filters"""
    
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    
    if client_ip:
        query = query.filter(AuditLog.client_ip == client_ip)
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()