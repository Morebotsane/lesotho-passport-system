# app/api/passport_applications.py - UPDATED WITH CACHING
"""
Passport Application API endpoints with Redis caching
High-performance version with smart caching strategies
"""
from fastapi import Body
from datetime import datetime
from typing import Any, List, Optional
import uuid
import json

from fastapi import File, UploadFile
from pathlib import Path
import os
import shutil
from fastapi.responses import FileResponse

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Body
from sqlalchemy.orm import Session
import logging
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.passport_application import (
    PassportApplication, 
    ApplicationStatus, 
    PriorityLevel
)
from app.schemas.passport_application import (
    PassportApplicationCreate,
    PassportApplicationResponse,
    PassportApplicationSummary,
    PassportApplicationWithApplicant,
    PassportApplicationUpdate,
    ApplicationFilter,
    ApplicationSearchResponse,
    FastTrackRequest,
    ApplicationStats
)
from app.api.deps import (
    get_current_active_user, 
    get_current_officer, 
    get_current_admin,
    check_user_permission
)
from app.services.passport_service import PassportApplicationService
from app.core.caching import (
    cache_response, 
    cache_invalidate, 
    cache_user_data, 
    cache_application_data,
    cache_statistics
)

UPLOAD_DIR = Path("uploads/applications")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=PassportApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_passport_application(
    application_data: PassportApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new passport application (no file uploads yet)"""
   
    # Generate application number
    application_number = f"LSO{datetime.now().year}{str(uuid.uuid4())[:6].upper()}"
    
    # Convert submission_location_id to UUID if it's a string
    submission_location_id = None
    if application_data.submission_location_id:
        if isinstance(application_data.submission_location_id, str):
            submission_location_id = uuid.UUID(application_data.submission_location_id)
        else:
            submission_location_id = application_data.submission_location_id
   
    # Create application
    db_application = PassportApplication(
        application_number=application_number,
        applicant_id=current_user.id,
        first_name=application_data.first_name,
        last_name=application_data.last_name,
        date_of_birth=application_data.date_of_birth,
        place_of_birth=application_data.place_of_birth,
        nationality=application_data.nationality,
        gender=application_data.gender,
        email=application_data.email,
        phone=application_data.phone,
        residential_address=application_data.residential_address,
        national_id_number=application_data.national_id_number,
        previous_passport_number=application_data.previous_passport_number,
        reason_for_issuance=application_data.reason_for_issuance,
        passport_type=application_data.passport_type,
        pages=application_data.pages,
        emergency_contact_name=application_data.emergency_contact_name,
        emergency_contact_phone=application_data.emergency_contact_phone,
        emergency_contact_relationship=application_data.emergency_contact_relationship,
        travel_purpose=application_data.travel_purpose,
        intended_travel_date=application_data.intended_travel_date,
        priority_reason=application_data.priority_reason,
        notes=application_data.notes,
        submission_location_id=submission_location_id,
        status=ApplicationStatus.SUBMITTED,
        priority_level=PriorityLevel.NORMAL,
        processing_stages={},
        is_fast_tracked=False
    )
   
    db.add(db_application)
    db.commit()
    
    # ADD THIS: Refresh with eagerly loaded relationship
    db_application = db.query(PassportApplication).options(
        joinedload(PassportApplication.submission_location)
    ).filter(PassportApplication.id == db_application.id).first()
   
    return db_application

def generate_application_number() -> str:
    """Generate unique application number"""
    import random
    import string
    prefix = "LSO"
    year = datetime.now().year
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{year}{random_part}"

# Add this endpoint after the create application endpoint
@router.post("/{application_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_documents(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    application_id: uuid.UUID,
    passport_photo: UploadFile = File(None),
    id_document: UploadFile = File(None),
    previous_passport: UploadFile = File(None)
) -> Any:
    """Upload documents for an application"""
    
    # Get application
    application = db.query(PassportApplication).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check ownership
    if current_user.role not in ['officer', 'admin']:
        if application.applicant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
    
    # Create application folder
    app_folder = UPLOAD_DIR / str(application_id)
    app_folder.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = {}
    
    # Upload passport photo
    if passport_photo:
        # Validate file type
        if not passport_photo.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passport photo must be an image"
            )
        
        # Validate file size (5MB)
        contents = await passport_photo.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passport photo must be less than 5MB"
            )
        
        # Save file
        file_extension = passport_photo.filename.split('.')[-1]
        file_path = app_folder / f"passport_photo.{file_extension}"
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        application.passport_photo_path = str(file_path)
        uploaded_files['passport_photo'] = str(file_path)
    
    # Upload ID document
    if id_document:
        # Validate file type
        allowed_types = ['image/', 'application/pdf']
        if not any(id_document.content_type.startswith(t) for t in allowed_types):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID document must be an image or PDF"
            )
        
        # Validate file size (5MB)
        contents = await id_document.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID document must be less than 5MB"
            )
        
        # Save file
        file_extension = id_document.filename.split('.')[-1]
        file_path = app_folder / f"id_document.{file_extension}"
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        application.id_document_path = str(file_path)
        uploaded_files['id_document'] = str(file_path)
    
    # Upload previous passport (optional)
    if previous_passport:
        # Validate file type
        allowed_types = ['image/', 'application/pdf']
        if not any(previous_passport.content_type.startswith(t) for t in allowed_types):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Previous passport must be an image or PDF"
            )
        
        # Validate file size (5MB)
        contents = await previous_passport.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Previous passport must be less than 5MB"
            )
        
        # Save file
        file_extension = previous_passport.filename.split('.')[-1]
        file_path = app_folder / f"previous_passport.{file_extension}"
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        uploaded_files['previous_passport'] = str(file_path)
    
    db.commit()
    db.refresh(application)
    
    return {
        "message": "Documents uploaded successfully",
        "uploaded_files": uploaded_files
    }

# Add this endpoint to serve files securely
@router.get("/{application_id}/documents/{document_type}")
async def get_document(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    application_id: uuid.UUID,
    document_type: str
) -> Any:
    """Download/view a document"""
    
    # Get application
    application = db.query(PassportApplication).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check permissions
    if current_user.role not in ['officer', 'admin']:
        if application.applicant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this document"
            )
    
    # Get file path
    if document_type == 'passport_photo':
        file_path = application.passport_photo_path
    elif document_type == 'id_document':
        file_path = application.id_document_path
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document type"
        )
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return FileResponse(file_path)

@router.get("/", response_model=List[PassportApplicationResponse])
def get_all_applications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None)
) -> Any:
    """
    Get all applications
    - Applicants see only their own applications
    - Officers see only applications from their assigned location
    - Admins see all applications
    """
    from app.models.user import UserRole
    from sqlalchemy.orm import joinedload  # ADD THIS
    
    # Start query with eagerly loaded relationship
    query = db.query(PassportApplication).options(
        joinedload(PassportApplication.submission_location)  # ADD THIS
    )
    
    if current_user.role == UserRole.APPLICANT:
        # Applicants see only their applications
        query = query.filter(PassportApplication.applicant_id == current_user.id)
    
    elif current_user.role == UserRole.OFFICER:
        if not current_user.assigned_location_id:
            print(f"⚠️ Officer {current_user.email} has NO assigned location!")
            return []
        
        print(f"🔍 Officer: {current_user.email}")
        print(f"   Officer's location ID: {current_user.assigned_location_id}")
        print(f"   Type: {type(current_user.assigned_location_id)}")
        
        # Get sample application to compare
        sample = db.query(PassportApplication).first()
        if sample:
            print(f"   Sample app location ID: {sample.submission_location_id}")
            print(f"   Type: {type(sample.submission_location_id)}")
        
        query = query.filter(
            PassportApplication.submission_location_id == current_user.assigned_location_id
        )
        
        count = query.count()
        print(f"   ✅ Found {count} matching applications")
    
    # Admins see everything (no filter)
    
    if status:
        query = query.filter(PassportApplication.status == status)
    
    applications = query.order_by(
        PassportApplication.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    # Debug logging
    print(f"📊 Returning {len(applications)} applications for {current_user.email} (role: {current_user.role})")
    
    return applications

@router.get("/my-applications", response_model=List[PassportApplicationSummary])
@cache_user_data(ttl=900)
def get_my_applications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    status_filter: List[ApplicationStatus] = Query(None),
    limit: int = Query(10, ge=1, le=100)
) -> Any:
    """Get current user's passport applications"""
    from sqlalchemy.orm import joinedload
    
    print(f"📱 MY APPLICATIONS for user: {current_user.email}")
    
    query = db.query(PassportApplication).options(
        joinedload(PassportApplication.submission_location)
    ).filter(
        PassportApplication.applicant_id == current_user.id
    )
    
    if status_filter:
        query = query.filter(PassportApplication.status.in_(status_filter))
    
    applications = query.order_by(PassportApplication.submitted_at.desc()).limit(limit).all()
    
    print(f"   Found {len(applications)} applications")
    
    result = []
    for app in applications:
        try:
            result.append({
                "id": app.id,
                "application_number": app.application_number,
                
                # Personal info
                "first_name": app.first_name,
                "last_name": app.last_name,
                "email": app.email,
                "phone": app.phone,
                "date_of_birth": app.date_of_birth,
                "place_of_birth": app.place_of_birth,
                "residential_address": app.residential_address,
                
                # Passport details
                "reason_for_issuance": app.reason_for_issuance,
                
                # Status
                "status": app.status,
                "priority_level": app.priority_level,
                "submitted_at": app.submitted_at,
                "days_in_processing": app.days_in_processing,
                "is_overdue": app.is_overdue
            })
            print(f"   ✅ Added application {app.application_number}")
        except Exception as e:
            print(f"   ❌ Error processing application {app.id}: {e}")
            continue
    
    print(f"   Returning {len(result)} applications")
    return result

@router.get("/all", response_model=List[PassportApplicationSummary])
def list_all_applications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # ← Changed!
    limit: int = 100
) -> Any:
    """Get all applications - filtered by location for officers, all for admins"""
    
    # Start with base query
    query = db.query(PassportApplication)
    
    # If officer, filter by assigned location
    if current_user.role == 'officer':
        if not current_user.assigned_location_id:
            print(f"⚠️ Officer {current_user.email} has NO assigned location!")
            return []
        
        print(f"🔍 OFFICER FILTER on /all endpoint")
        print(f"   Officer: {current_user.email}")
        print(f"   Assigned Location: {current_user.assigned_location_id}")
        
        query = query.filter(
            PassportApplication.submission_location_id == current_user.assigned_location_id
        )
    else:
        # Admin sees all applications
        print(f"👑 ADMIN viewing ALL applications")
        print(f"   Admin: {current_user.email}")
    
    count = query.count()
    print(f"   ✅ Found {count} applications")
    
    applications = query.order_by(
        PassportApplication.submitted_at.desc()
    ).limit(limit).all()
    
    result = []
    for app in applications:
        result.append({
            "id": app.id,
            "application_number": app.application_number,
            "first_name": app.first_name,
            "last_name": app.last_name,
            "email": app.email,
            "phone": app.phone,
            "date_of_birth": app.date_of_birth,
            "place_of_birth": app.place_of_birth,
            "residential_address": app.residential_address,
            "reason_for_issuance": app.reason_for_issuance,
            "status": app.status,
            "priority_level": app.priority_level,
            "submitted_at": app.submitted_at,
            "days_in_processing": app.days_in_processing,
            "is_overdue": app.is_overdue
        })
    
    return result

@router.get("/{application_id}", response_model=PassportApplicationResponse)
@cache_response(ttl=600, prefix="app_detail", vary_on_user=True)
def get_application_by_id(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    application_id: uuid.UUID
) -> Any:
    """Get a specific passport application by ID"""
    from sqlalchemy.orm import joinedload
    
    application = db.query(PassportApplication).options(
        joinedload(PassportApplication.submission_location)
    ).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check permissions
    if current_user.role not in ['officer', 'admin']:
        if application.applicant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # IMPORTANT: Serialize location BEFORE the return statement
    location_dict = None
    if application.submission_location:
        location_dict = {
            "id": str(application.submission_location.id),
            "name": application.submission_location.name,
            "address": application.submission_location.address
        }
    
    # Return complete dictionary with ALL fields
    return {
        "id": application.id,
        "application_number": application.application_number,
        "applicant_id": application.applicant_id,
        "first_name": application.first_name,
        "last_name": application.last_name,
        "gender": application.gender,
        "date_of_birth": application.date_of_birth,
        "place_of_birth": application.place_of_birth,
        "nationality": application.nationality,
        "email": application.email,
        "phone": application.phone,
        "residential_address": application.residential_address,
        "national_id_number": application.national_id_number,
        "submission_location_id": application.submission_location_id,
        "submission_location": location_dict,
        "passport_type": application.passport_type,
        "pages": application.pages,
        "reason_for_issuance": application.reason_for_issuance,
        "previous_passport_number": application.previous_passport_number,
        "emergency_contact_name": application.emergency_contact_name,
        "emergency_contact_phone": application.emergency_contact_phone,
        "emergency_contact_relationship": application.emergency_contact_relationship,
        "travel_purpose": application.travel_purpose,
        "intended_travel_date": application.intended_travel_date,
        "status": application.status,
        "priority_level": application.priority_level,
        "priority_reason": application.priority_reason,
        "processing_stages": application.processing_stages,
        "is_fast_tracked": application.is_fast_tracked,
        "fast_track_reason": application.fast_track_reason,
        "fast_track_approved_by": application.fast_track_approved_by,
        "submitted_at": application.submitted_at,
        "estimated_completion_date": application.estimated_completion_date,
        "actual_completion_date": application.actual_completion_date,
        "pickup_deadline": application.pickup_deadline,
        "collected_at": application.collected_at,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
        "passport_photo_path": application.passport_photo_path,
        "id_document_path": application.id_document_path,
        "passport_photo_path": application.passport_photo_path,
        "id_document_path": application.id_document_path,
        "notes": application.notes,
        "days_in_processing": application.days_in_processing,
        "is_overdue": application.is_overdue,
        "pickup_expires_in_days": application.pickup_expires_in_days
    }

@router.get("/", response_model=ApplicationSearchResponse)
@cache_response(ttl=180, prefix="app_search", vary_on_user=False)  # 3 minutes for officers
def search_applications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Only officers/admins
    filters: ApplicationFilter = Depends()
) -> Any:
    """
    Search and filter passport applications (Officers only)
    
    Cached for 3 minutes since officers need relatively fresh data
    """
    service = PassportApplicationService(db)
    
    result = service.search_applications(
        filters=filters,
        user_role=current_user.role
    )
    
    # Convert applications to include applicant info
    applications_with_applicants = []
    for app in result["applications"]:
        # Get applicant info (this could be optimized with joins)
        applicant = db.query(User).filter(User.id == app.applicant_id).first()
        if applicant:
            app_with_applicant = PassportApplicationWithApplicant.from_application_and_user(app, applicant)
            applications_with_applicants.append(app_with_applicant)
    
    return ApplicationSearchResponse(
        applications=applications_with_applicants,
        total_count=result["total_count"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
        has_next=result["has_next"],
        has_previous=result["has_previous"]
    )
       
@router.put("/{application_id}/status", status_code=status.HTTP_200_OK)
def update_application_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    application_id: uuid.UUID,
    status_data: dict = Body(...)
) -> Any:
    """Update application status (Officers only)"""
    from app.services.sms_service import SMSService
    from app.models.passport_application import ApplicationStatus
    
    application = db.query(PassportApplication).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get the new status and other data
    new_status = status_data.get('status')
    notes = status_data.get('notes')
    send_notification = status_data.get('send_notification', True)  # Default to True
    
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status is required"
        )
    
    # Store old status for comparison
    old_status = application.status
    
    # Update the application
    application.status = new_status
    
    if notes:
        # Append notes to existing notes
        existing_notes = application.notes or ""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        application.notes = f"{existing_notes}\n[{timestamp}] {current_user.email}: {notes}".strip()
    
    application.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    
    # Send automatic SMS notification if requested
    if send_notification and old_status != new_status:
        applicant = db.query(User).filter(User.id == application.applicant_id).first()
        
        if applicant:
            try:
                sms_service = SMSService(db)
                sms_service.send_status_update_notification(
                    application=application,
                    applicant=applicant,
                    new_status=ApplicationStatus(new_status),
                    sender_id=current_user.id
                )
                logger.info(f"Auto-sent SMS for status change: {old_status} -> {new_status}")
            except Exception as e:
                logger.error(f"Failed to send auto SMS notification: {str(e)}")
                # Don't fail the status update if SMS fails
    
    return {
        "message": "Status updated successfully",
        "application_id": str(application.id),
        "old_status": old_status,
        "new_status": new_status,
        "notification_sent": send_notification and old_status != new_status
    }

@router.post("/{application_id}/fast-track", response_model=PassportApplicationResponse)
@cache_invalidate(["app:*", "stats:*"])  # Invalidate when fast-tracking
def request_fast_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Only officers/admins
    application_id: uuid.UUID,
    fast_track_data: FastTrackRequest
) -> Any:
    """
    Request fast-track processing for an application (Officers only)
    
    Cache invalidation: Clears related caches since this changes priority
    """
    service = PassportApplicationService(db)
    
    try:
        application = service.flag_fast_track_request(
            application_id=application_id,
            reason=fast_track_data.reason,
            requested_priority=fast_track_data.priority_level,
            officer_id=current_user.id
        )
        return application
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/statistics/overview", response_model=ApplicationStats)
@cache_statistics(ttl=300)  # Cache stats for 5 minutes
def get_application_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer)  # Only officers/admins
) -> Any:
    """
    Get application processing statistics (Officers only)
    
    Heavily cached since stats are expensive to compute and don't change rapidly
    """
    service = PassportApplicationService(db)
    
    stats = service.generate_processing_statistics()
    
    return ApplicationStats(
        total_applications=stats["total_applications"],
        by_status=stats["by_status"],
        by_priority=stats["by_priority"],
        average_processing_days=0.0,  # TODO: Calculate from actual data
        overdue_applications=stats["overdue_applications"],
        fast_tracked_applications=stats["fast_tracked_applications"],
        completed_this_month=stats["completed_this_month"]
    )

@router.get("/overdue/list", response_model=List[PassportApplicationWithApplicant])
@cache_response(ttl=600, prefix="overdue_apps")  # Cache for 10 minutes
def get_overdue_applications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer)  # Only officers/admins
) -> Any:
    """
    Get list of overdue applications (Officers only)
    
    Cached for 10 minutes since overdue calculations are expensive
    """
    service = PassportApplicationService(db)
    
    overdue_apps = service.get_overdue_applications()
    
    # Convert to include applicant info
    result = []
    for app in overdue_apps:
        applicant = db.query(User).filter(User.id == app.applicant_id).first()
        if applicant:
            app_with_applicant = PassportApplicationWithApplicant.from_application_and_user(app, applicant)
            result.append(app_with_applicant)
    
    return result

@router.get("/track/{application_number}", response_model=PassportApplicationResponse)
@cache_response(ttl=300, prefix="public_track", vary_on_user=False)  # Public endpoint, 5 min cache
def track_application_by_number(
    *,
    db: Session = Depends(get_db),
    application_number: str
) -> Any:
    """
    Track passport application by application number (Public endpoint)
    
    Cached for 5 minutes since this is a public endpoint that could get heavy traffic
    """
    application = db.query(PassportApplication).filter(
        PassportApplication.application_number == application_number
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Return limited info for public tracking
    return application

# Cache warming endpoint for testing
@router.post("/admin/warm-cache")
def warm_application_cache(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Warm up cache with frequently accessed data (Admin only)
    """
    from app.core.caching import warm_cache
    
    try:
        warm_cache()
        
        # Pre-load critical data
        service = PassportApplicationService(db)
        stats = service.generate_processing_statistics()
        
        # Cache the stats
        from app.core.redis_config import cache_service
        cache_service.set("stats", stats, 300)
        
        return {"message": "Cache warming completed successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache warming failed: {str(e)}"
        )

# Cache health check endpoint
@router.get("/admin/cache-health")
def check_cache_health(
    *,
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Check cache system health (Admin only)
    """
    from app.core.caching import cache_health_check
    
    return cache_health_check()

@router.post("/{application_id}/documents", response_model=PassportApplicationResponse)
async def upload_application_documents(
    application_id: uuid.UUID,
    passport_photo: UploadFile = File(...),
    id_document: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload documents for an existing application"""
    from app.utils.file_handler import save_upload_file
    
    # Get application
    application = db.query(PassportApplication).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Verify ownership
    if application.applicant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Save files
        photo_path = await save_upload_file(passport_photo, "passport_photos")
        id_path = await save_upload_file(id_document, "id_documents")
        
        # Update application
        application.passport_photo_path = photo_path
        application.id_document_path = id_path
        
        db.commit()
        db.refresh(application)
        
        return application
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/{application_id}/notify", status_code=status.HTTP_200_OK)
def send_notification(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    application_id: uuid.UUID,
    message: str = Body(..., embed=True)
) -> Any:
    """Send SMS notification to applicant (Officers only)"""
    from app.services.sms_service import SMSService
    
    application = db.query(PassportApplication).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    applicant = db.query(User).filter(User.id == application.applicant_id).first()
    
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )
    
    # Use your existing SMS service
    sms_service = SMSService(db)
    
    # Create a custom notification using the base _queue_sms method
    from app.models.notification import NotificationType
    
    notification = sms_service._queue_sms(
        recipient_phone=applicant.phone,
        message=message,
        notification_type=NotificationType.STATUS_UPDATE,
        application=application,
        sender_id=current_user.id
    )
    
    return {
        "message": "Notification queued successfully",
        "recipient": f"{applicant.first_name} {applicant.last_name}",
        "phone": applicant.phone,
        "notification_id": str(notification.id),
        "status": notification.status.value
    }
