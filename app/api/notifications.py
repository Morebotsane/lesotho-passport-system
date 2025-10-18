# app/api/notifications.py
"""
Notification API endpoints
Handles SMS notifications and delivery tracking
NOW WITH CELERY ASYNC SUPPORT! 🚀
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.api.deps import get_current_active_user, get_current_officer, get_db
from app.models.user import User
from app.models.passport_application import PassportApplication, ApplicationStatus
from app.models.notification import Notification, NotificationType
from app.schemas.passport_application import BulkNotificationRequest, NotificationPreview
from app.services.sms_service import SMSService  # Now uses Celery internally!

router = APIRouter()

@router.post("/{application_id}/send-ready-notification")
def send_passport_ready_notification(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Officers only
    application_id: uuid.UUID
) -> Any:
    """
    Send "passport ready for pickup" notification (Officers only)
    
    NOW ASYNC: Returns immediately, SMS sent by Celery worker in background.
    """
    application = db.query(PassportApplication).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application.status != ApplicationStatus.READY_FOR_PICKUP.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application must be in 'ready_for_pickup' status to send this notification"
        )
    
    # Get applicant
    applicant = db.query(User).filter(User.id == application.applicant_id).first()
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )
    
    # Send notification (NOW ASYNC - queues Celery task)
    sms_service = SMSService(db)
    notification = sms_service.send_passport_ready_notification(application, applicant)
    
    # UPDATED RESPONSE - includes Celery task info
    return {
        "message": "Passport ready notification queued for sending",
        "notification_id": str(notification.id),
        "sent_to": applicant.phone,
        "status": notification.status.value,  # Will be "pending"
        "celery_task_id": notification.celery_task_id  # NEW: Track background task
    }

@router.post("/{application_id}/send-status-update")
def send_status_update_notification(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Officers only
    application_id: uuid.UUID,
    new_status: ApplicationStatus
) -> Any:
    """
    Send status update notification (Officers only)
    
    NOW ASYNC: Returns immediately, SMS sent by Celery worker.
    """
    application = db.query(PassportApplication).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get applicant
    applicant = db.query(User).filter(User.id == application.applicant_id).first()
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )
    
    # Send notification (NOW ASYNC)
    sms_service = SMSService(db)
    notification = sms_service.send_status_update_notification(
        application, applicant, new_status, current_user.id
    )
    
    return {
        "message": "Status update notification queued for sending",
        "notification_id": str(notification.id),
        "sent_to": applicant.phone,
        "status": notification.status.value,
        "new_application_status": new_status.value,
        "celery_task_id": notification.celery_task_id  # NEW
    }

@router.post("/{application_id}/send-pickup-reminder")
def send_pickup_reminder_notification(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Officers only
    application_id: uuid.UUID
) -> Any:
    """
    Send pickup reminder notification (Officers only)
    
    NOW ASYNC: Returns immediately, SMS sent by Celery worker.
    """
    application = db.query(PassportApplication).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application.status != ApplicationStatus.READY_FOR_PICKUP.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application must be ready for pickup to send reminder"
        )
    
    if not application.pickup_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pickup deadline set for this application"
        )
    
    # Get applicant
    applicant = db.query(User).filter(User.id == application.applicant_id).first()
    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant not found"
        )
    
    # Send notification (NOW ASYNC)
    sms_service = SMSService(db)
    days_remaining = application.pickup_expires_in_days
    notification = sms_service.send_pickup_reminder(application, applicant, days_remaining)
    
    return {
        "message": "Pickup reminder queued for sending",
        "notification_id": str(notification.id),
        "sent_to": applicant.phone,
        "days_remaining": days_remaining,
        "status": notification.status.value,
        "celery_task_id": notification.celery_task_id  # NEW
    }

@router.post("/bulk-send")
def send_bulk_notifications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Officers only
    bulk_request: BulkNotificationRequest
) -> Any:
    """
    Send bulk notifications to multiple applications (Officers only)
    
    NOW ASYNC: All notifications queued instantly, sent by Celery workers.
    """
    # Get applications
    applications = db.query(PassportApplication).filter(
        PassportApplication.id.in_(bulk_request.application_ids)
    ).all()
    
    if len(applications) != len(bulk_request.application_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some applications not found"
        )
    
    # Map notification type string to enum
    notification_type_mapping = {
        "status_update": NotificationType.STATUS_UPDATE,
        "pickup_reminder": NotificationType.PICKUP_REMINDER,
        "urgent_reminder": NotificationType.PICKUP_URGENT
    }
    
    notification_type = notification_type_mapping.get(bulk_request.notification_type)
    if not notification_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid notification type"
        )
    
    # Send bulk notifications (ALL QUEUED INSTANTLY!)
    sms_service = SMSService(db)
    notifications = sms_service.send_bulk_notifications(
        applications=applications,
        message_template=bulk_request.message_template,
        notification_type=notification_type,
        sender_id=current_user.id
    )
    
    return {
        "message": "Bulk notifications queued for sending",
        "total_queued": len(notifications),
        "notification_ids": [str(n.id) for n in notifications],
        "celery_task_ids": [n.celery_task_id for n in notifications if n.celery_task_id]
    }

@router.get("/{application_id}/notifications")
def get_application_notifications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    application_id: uuid.UUID
) -> Any:
    """
    Get all notifications for a specific application
    
    Users can view notifications for their own applications.
    Officers can view notifications for any application.
    """
    application = db.query(PassportApplication).filter(
        PassportApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check permissions (same as viewing application)
    from app.api.deps import check_user_permission
    if not check_user_permission(
        current_user=current_user,
        target_user_id=str(application.applicant_id),
        allow_officer_access=True
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view notifications for this application"
        )
    
    # Get notifications
    notifications = db.query(Notification).filter(
        Notification.passport_application_id == application_id
    ).order_by(Notification.created_at.desc()).all()
    
    return {
        "application_id": str(application_id),
        "application_number": application.application_number,
        "total_notifications": len(notifications),
        "notifications": [
            {
                "id": str(n.id),
                "type": n.notification_type.value,
                "message": n.message,
                "status": n.status.value,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
                "recipient_phone": n.recipient_phone,
                "failure_reason": n.failure_reason,
                "celery_task_id": n.celery_task_id,  # NEW
                "retry_count": n.retry_count  # NEW
            }
            for n in notifications
        ]
    }

@router.get("/notification/{notification_id}/status")
def check_notification_delivery_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Officers only
    notification_id: uuid.UUID
) -> Any:
    """
    Check delivery status of a specific notification (Officers only)
    
    Shows both Celery task status and Twilio delivery status.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Get detailed status from service
    sms_service = SMSService(db)
    status_details = sms_service.get_notification_status(notification)
    
    return status_details

@router.post("/notification/{notification_id}/retry")
def retry_failed_notification(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Officers only
    notification_id: uuid.UUID
) -> Any:
    """
    Retry sending a failed notification (Officers only)
    
    NOW ASYNC: Queues a new Celery task for retry.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if notification.status.value not in ["failed", "retry"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed notifications can be retried"
        )
    
    # Retry notification (NOW ASYNC - queues new task)
    sms_service = SMSService(db)
    updated_notification = sms_service.retry_failed_notification(notification)
    
    return {
        "message": "Notification retry queued",
        "notification_id": str(updated_notification.id),
        "new_status": updated_notification.status.value,
        "retry_count": updated_notification.retry_count,
        "celery_task_id": updated_notification.celery_task_id,  # NEW
        "max_retries": updated_notification.max_retries
    }

# Development/Testing endpoint (keep as-is for now)
@router.post("/test-sms")
def send_test_sms(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    phone: str,
    message: str
) -> Any:
    """
    Send test SMS (Development only)
    Remove this endpoint in production
    
    NOTE: This still sends synchronously for testing purposes.
    """
    sms_service = SMSService(db)
    
    # Debug info
    print(f"Attempting to send SMS to: {phone}")
    print(f"From number: {sms_service.from_number}")
    print(f"Message: {message}")
    
    try:
        # Send test message directly via Twilio (SYNC for testing)
        from twilio.rest import Client
        client = Client(sms_service.settings.TWILIO_ACCOUNT_SID, sms_service.settings.TWILIO_AUTH_TOKEN)
        twilio_message = client.messages.create(
            body=f"TEST MESSAGE from Passport System: {message}",
            from_=sms_service.from_number,
            to=phone
        )
        
        return {
            "message": "Test SMS sent successfully (synchronous)",
            "twilio_message_sid": twilio_message.sid,
            "sent_to": phone,
            "test_message": message
        }
        
    except Exception as e:
        # Detailed error logging
        print(f"Twilio Error Type: {type(e).__name__}")
        print(f"Twilio Error Message: {str(e)}")
        print(f"Phone format used: {repr(phone)}")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Failed to send test SMS",
                "twilio_error": str(e),
                "phone_used": phone,
                "from_number": sms_service.from_number
            }
        )