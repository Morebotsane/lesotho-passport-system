# app/tasks/notification_tasks.py
"""
Background tasks for sending SMS notifications via Twilio.
Adapted to work with existing Notification model using UUIDs.
"""
from celery import Task
from celery.utils.log import get_task_logger
from typing import Dict, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from app.core.celery_app import celery_app
from app.core.config import settings
from app.database import SessionLocal
from app.models.notification import Notification, NotificationStatus

logger = get_task_logger(__name__)


class CallbackTask(Task):
    """Base task with database session and error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failures."""
        logger.error(f"Task {task_id} failed: {exc}")
        
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Log task retries."""
        logger.warning(f"Task {task_id} retrying: {exc}")
        
    def on_success(self, retval, task_id, args, kwargs):
        """Log successful task completion."""
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(TwilioRestException, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def send_sms_notification(
    self,
    notification_id: str,  # UUID as string
) -> Dict:
    """
    Send SMS notification via Twilio.
    Works with your existing Notification model.
    
    Args:
        notification_id: UUID of the notification record (as string)
    
    Returns:
        Dict with delivery status and Twilio response
    """
    logger.info(f"Processing SMS notification {notification_id} (attempt {self.request.retries + 1})")
    
    db: Session = SessionLocal()
    try:
        # Load notification from database
        notification = db.query(Notification).filter(
            Notification.id == uuid.UUID(notification_id)
        ).first()
        
        if not notification:
            logger.error(f"Notification {notification_id} not found")
            return {"status": "error", "message": "Notification not found"}
        
        # Update status to RETRY (during processing)
        notification.status = NotificationStatus.RETRY
        notification.retry_count += 1
        db.commit()
        
        # Initialize Twilio client
        twilio_client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        # Send SMS via Twilio
        message = twilio_client.messages.create(
            body=notification.message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=notification.recipient_phone
        )
        
        # Update notification with Twilio response
        notification.status = NotificationStatus.SENT
        notification.twilio_message_sid = message.sid
        notification.delivery_status = message.status
        notification.sent_at = datetime.utcnow()
        
        # Note: Twilio delivery status will be updated via webhook
        # Initial status is usually "queued" or "sent"
        
        db.commit()
        
        logger.info(f"SMS sent successfully: {message.sid}")
        return {
            "status": "success",
            "notification_id": notification_id,
            "twilio_sid": message.sid,
            "twilio_status": message.status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except TwilioRestException as exc:
        logger.error(f"Twilio error sending SMS: {exc}")
        
        # Update notification with failure info
        notification = db.query(Notification).filter(
            Notification.id == uuid.UUID(notification_id)
        ).first()
        
        if notification:
            notification.status = NotificationStatus.FAILED
            notification.failure_reason = str(exc)
            db.commit()
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        else:
            # Max retries exceeded, mark as permanently failed
            return {
                "status": "failed",
                "notification_id": notification_id,
                "error": str(exc),
                "retries": self.request.retries
            }
        
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}")
        
        # Update notification status
        notification = db.query(Notification).filter(
            Notification.id == uuid.UUID(notification_id)
        ).first()
        
        if notification:
            notification.status = NotificationStatus.FAILED
            notification.failure_reason = f"Unexpected error: {str(exc)}"
            db.commit()
        
        raise self.retry(exc=exc)
        
    finally:
        db.close()


@celery_app.task(bind=True, base=CallbackTask)
def send_application_status_notification(
    self,
    passport_application_id: str,  # UUID as string
    notification_type: str,
    message: str,
    recipient_phone: str
) -> Dict:
    """
    Create and send notification for passport application status changes.
    
    Args:
        passport_application_id: UUID of passport application
        notification_type: Type from NotificationType enum
        message: SMS message content
        recipient_phone: Recipient phone number
    
    Returns:
        Dict with notification details
    """
    from app.models.notification import NotificationType
    
    logger.info(f"Creating status notification for application {passport_application_id}")
    
    db: Session = SessionLocal()
    try:
        # Create notification record
        notification = Notification(
            id=uuid.uuid4(),
            passport_application_id=uuid.UUID(passport_application_id),
            notification_type=NotificationType(notification_type),
            message=message,
            recipient_phone=recipient_phone,
            status=NotificationStatus.PENDING,
            celery_task_id=self.request.id,
            celery_queue="notifications",
            retry_count=0,
            created_at=datetime.utcnow()
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Queue the SMS sending task
        task = send_sms_notification.delay(str(notification.id))
        
        # Update with Celery task ID
        notification.celery_task_id = task.id
        db.commit()
        
        logger.info(f"Notification {notification.id} created and queued")
        return {
            "status": "queued",
            "notification_id": str(notification.id),
            "task_id": task.id
        }
        
    except Exception as exc:
        logger.error(f"Error creating notification: {exc}")
        db.rollback()
        raise
        
    finally:
        db.close()


@celery_app.task
def send_bulk_notifications(
    passport_application_ids: list,
    notification_type: str,
    message_template: str
) -> Dict:
    """
    Send notifications to multiple passport applicants.
    
    Args:
        passport_application_ids: List of application UUIDs (as strings)
        notification_type: NotificationType value
        message_template: Message template with {variables}
    
    Returns:
        Dict with batch processing results
    """
    from app.models.passport_application import PassportApplication
    
    logger.info(f"Sending bulk notifications to {len(passport_application_ids)} applicants")
    
    db: Session = SessionLocal()
    task_ids = []
    
    try:
        for app_id_str in passport_application_ids:
            # Get application to extract phone number and personalization data
            application = db.query(PassportApplication).filter(
                PassportApplication.id == uuid.UUID(app_id_str)
            ).first()
            
            if not application or not application.applicant_phone:
                logger.warning(f"Skipping application {app_id_str}: no phone number")
                continue
            
            # Personalize message (you can extend this with more variables)
            message = message_template.format(
                application_id=str(application.id)[:8],  # Short ID for SMS
                applicant_name=getattr(application, 'applicant_name', 'Applicant')
            )
            
            # Queue notification task
            task = send_application_status_notification.delay(
                passport_application_id=app_id_str,
                notification_type=notification_type,
                message=message,
                recipient_phone=application.applicant_phone
            )
            
            task_ids.append(task.id)
        
        return {
            "status": "queued",
            "total_queued": len(task_ids),
            "task_ids": task_ids
        }
        
    finally:
        db.close()


@celery_app.task
def process_twilio_status_callback(
    twilio_message_sid: str,
    message_status: str
) -> Dict:
    """
    Process Twilio delivery status callbacks.
    Updates notification record when Twilio reports delivery status.
    
    Args:
        twilio_message_sid: Twilio's message SID
        message_status: Twilio delivery status (delivered, failed, etc.)
    
    Returns:
        Dict with update status
    """
    logger.info(f"Processing Twilio callback for {twilio_message_sid}: {message_status}")
    
    db: Session = SessionLocal()
    try:
        notification = db.query(Notification).filter(
            Notification.twilio_message_sid == twilio_message_sid
        ).first()
        
        if not notification:
            logger.warning(f"Notification not found for Twilio SID: {twilio_message_sid}")
            return {"status": "not_found"}
        
        # Update delivery status
        notification.delivery_status = message_status
        
        # Map Twilio status to our NotificationStatus
        if message_status == "delivered":
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.utcnow()
        elif message_status in ["failed", "undelivered"]:
            notification.status = NotificationStatus.FAILED
        
        db.commit()
        
        logger.info(f"Updated notification {notification.id} with status: {message_status}")
        return {
            "status": "updated",
            "notification_id": str(notification.id),
            "delivery_status": message_status
        }
        
    finally:
        db.close()