# app/schemas/dashboard.py
"""
Pydantic schemas for officer dashboard responses
Define the structure of dashboard API responses
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# ============================================================================
# DASHBOARD OVERVIEW SCHEMAS
# ============================================================================

class DashboardOverview(BaseModel):
    """Overview metrics for the dashboard"""
    total_applications: int
    active_applications: int
    today_submitted: int
    today_completed: int
    overdue_count: int
    unresolved_alerts: int

class RecentApplicationSummary(BaseModel):
    """Summary of recent applications for dashboard"""
    id: uuid.UUID
    application_number: str
    applicant_name: str
    status: str
    priority_level: str
    submitted_at: datetime
    days_processing: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }

class DashboardData(BaseModel):
    """Complete dashboard data response"""
    overview: DashboardOverview
    status_breakdown: Dict[str, int]
    priority_breakdown: Dict[str, int]
    recent_applications: List[RecentApplicationSummary]

# ============================================================================
# WORKLOAD SCHEMAS
# ============================================================================

class WorkloadApplication(BaseModel):
    """Application in workload queue"""
    id: uuid.UUID
    application_number: str
    applicant_name: str
    status: str
    priority_level: str
    submitted_at: datetime
    days_in_processing: int
    is_overdue: bool
    estimated_completion: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: lambda v: str(v)
        }

class WorkloadAssignment(BaseModel):
    """Officer workload assignment"""
    priority_queue: List[WorkloadApplication]
    document_review_queue: List[WorkloadApplication]
    quality_check_queue: List[WorkloadApplication]
    total_pending_work: int

# ============================================================================
# ALERT SCHEMAS
# ============================================================================

class SystemAlertSummary(BaseModel):
    """System alert summary for dashboard"""
    id: uuid.UUID
    type: str
    severity: str
    title: str
    description: str
    application_number: Optional[str] = None
    created_at: datetime
    age_hours: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }

class AlertAcknowledgment(BaseModel):
    """Alert acknowledgment response"""
    alert_id: uuid.UUID
    acknowledged_by: uuid.UUID
    acknowledged_at: datetime
    notes: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }

# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class SLACompliance(BaseModel):
    """SLA compliance statistics for a priority level"""
    total: int
    compliant: int
    compliance_rate: float

class ProcessingStatistics(BaseModel):
    """Processing performance statistics"""
    period_days: int
    total_completed: int
    average_processing_days: float
    fastest_processing_days: int
    slowest_processing_days: int
    sla_compliance: Dict[str, SLACompliance]
    overall_efficiency: float

class FraudApplication(BaseModel):
    """Suspicious application details"""
    application_number: str
    applicant_name: str
    days_in_processing: int
    fast_track_reason: Optional[str] = None
    approved_by: Optional[uuid.UUID] = None
    submitted_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v) if v else None
        }

class FraudDetectionReport(BaseModel):
    """Fraud detection analysis report"""
    total_fast_tracked: int
    suspicious_fast_tracks: int
    suspicious_applications: List[FraudApplication]
    recommendations: List[str]

# ============================================================================
# TREND ANALYSIS SCHEMAS
# ============================================================================

class DailySubmission(BaseModel):
    """Daily submission count"""
    date: str
    count: int

class PriorityDistribution(BaseModel):
    """Priority level distribution"""
    priority: str
    count: int

class ApplicationTrends(BaseModel):
    """Application trend analysis"""
    daily_submissions: List[DailySubmission]
    priority_distribution: List[PriorityDistribution]

class TrendAnalysis(BaseModel):
    """Complete trend analysis response"""
    period: str
    start_date: str
    end_date: str
    trends: ApplicationTrends

# ============================================================================
# EXPORT SCHEMAS
# ============================================================================

class ExportApplication(BaseModel):
    """Application data for export"""
    application_number: str
    applicant_name: str
    applicant_email: str
    status: str
    priority_level: str
    priority_reason: Optional[str] = None
    passport_type: str
    pages: int
    submitted_at: datetime
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    days_in_processing: int
    is_overdue: bool
    is_fast_tracked: bool
    fast_track_reason: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class ExportFilters(BaseModel):
    """Export filter criteria"""
    status_filter: Optional[str] = None
    days_included: int

class ApplicationExport(BaseModel):
    """Application export response"""
    exported_by: str
    export_timestamp: datetime
    total_records: int
    filters_applied: ExportFilters
    data: List[ExportApplication]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }