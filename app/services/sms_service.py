# app/services/sms_service.py
"""
SMS notification service using Twilio with Celery background tasks.
Handles all SMS communications for passport notifications asynchronously.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid

from app.core.config import settings
from app.models.notification import Notification, NotificationType, NotificationStatus
from app.models.passport_application import PassportApplication, ApplicationStatus
from app.models.user import User
from app.tasks.notification_tasks import send_sms_notification

from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)

class SMSService:
    """
    Service for sending SMS notifications via Twilio.
    Now with ASYNC Celery task queuing! 🚀
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def send_passport_ready_notification(
        self, 
        application: PassportApplication, 
        applicant: User
    ) -> Notification:
        """
        Send SMS notification when passport is ready for pickup.
        NOW ASYNC - returns immediately, SMS sent in background.
        
        Args:
            application: PassportApplication object
            applicant: User object (applicant)
            
        Returns:
            Notification object (status will be PENDING/QUEUED)
        """
        message = self._format_ready_message(application, applicant)
        
        return self._queue_sms(
            recipient_phone=applicant.phone,
            message=message,
            notification_type=NotificationType.READY_FOR_PICKUP,
            application=application,
            sender_id=None  # System notification
        )
    
    def send_pickup_reminder(
        self, 
        application: PassportApplication, 
        applicant: User,
        days_remaining: int
    ) -> Notification:
        """
        Send pickup reminder notification (async).
        
        Args:
            application: PassportApplication object
            applicant: User object
            days_remaining: Days until pickup deadline
            
        Returns:
            Notification object (queued for sending)
        """
        message = self._format_reminder_message(application, applicant, days_remaining)
        
        notification_type = (
            NotificationType.PICKUP_URGENT 
            if days_remaining <= 5 
            else NotificationType.PICKUP_REMINDER
        )
        
        return self._queue_sms(
            recipient_phone=applicant.phone,
            message=message,
            notification_type=notification_type,
            application=application,
            sender_id=None
        )
    
    def send_status_update_notification(
        self, 
        application: PassportApplication, 
        applicant: User,
        new_status: ApplicationStatus,
        sender_id: Optional[uuid.UUID] = None
    ) -> Notification:
        """
        Send status update notification (async).
        
        Args:
            application: PassportApplication object
            applicant: User object
            new_status: New application status
            sender_id: ID of officer sending the update (optional)
            
        Returns:
            Notification object (queued for sending)
        """
        message = self._format_status_update_message(application, applicant, new_status)
        
        return self._queue_sms(
            recipient_phone=applicant.phone,
            message=message,
            notification_type=NotificationType.STATUS_UPDATE,
            application=application,
            sender_id=sender_id
        )
    
    def send_documents_required_notification(
        self, 
        application: PassportApplication, 
        applicant: User,
        required_documents: List[str],
        sender_id: uuid.UUID
    ) -> Notification:
        """
        Send notification for required documents (async).
        
        Args:
            application: PassportApplication object
            applicant: User object
            required_documents: List of required document names
            sender_id: ID of officer requesting documents
            
        Returns:
            Notification object (queued for sending)
        """
        message = self._format_documents_required_message(
            application, applicant, required_documents
        )
        
        return self._queue_sms(
            recipient_phone=applicant.phone,
            message=message,
            notification_type=NotificationType.DOCUMENTS_REQUIRED,
            application=application,
            sender_id=sender_id
        )
    
    def send_bulk_notifications(
        self, 
        applications: List[PassportApplication],
        message_template: str,
        notification_type: NotificationType,
        sender_id: uuid.UUID
    ) -> List[Notification]:
        """
        Send bulk notifications to multiple applicants (all async).
        Creates notification records and queues them for sending.
        
        Args:
            applications: List of PassportApplication objects
            message_template: Message template with placeholders
            notification_type: Type of notification
            sender_id: ID of user sending bulk notifications
            
        Returns:
            List of Notification objects (all queued)
        """
        notifications = []
        
        for application in applications:
            applicant = self.db.query(User).filter(
                User.id == application.applicant_id
            ).first()
            
            if not applicant:
                logger.warning(f"Applicant not found for application {application.id}")
                continue
            
            # Format message with application-specific data
            formatted_message = self._format_bulk_message(
                message_template, application, applicant
            )
            
            notification = self._queue_sms(
                recipient_phone=applicant.phone,
                message=formatted_message,
                notification_type=notification_type,
                application=application,
                sender_id=sender_id
            )
            
            notifications.append(notification)
        
        logger.info(f"Queued {len(notifications)} bulk notifications")
        return notifications
    
    def get_notification_status(self, notification: Notification) -> Dict[str, Any]:
        """
        Get detailed status of a notification.
        
        Args:
            notification: Notification object
            
        Returns:
            Dict with current status details
        """
        return {
            "id": str(notification.id),
            "status": notification.status.value,
            "delivery_status": notification.delivery_status,
            "retry_count": notification.retry_count,
            "twilio_message_sid": notification.twilio_message_sid,
            "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
            "delivered_at": notification.delivered_at.isoformat() if notification.delivered_at else None,
            "failure_reason": notification.failure_reason,
            "celery_task_id": notification.celery_task_id
        }
    
    def retry_failed_notification(self, notification: Notification) -> Notification:
        """
        Retry sending a failed notification by queuing a new Celery task.
        
        Args:
            notification: Failed notification to retry
            
        Returns:
            Updated notification object
        """
        if notification.retry_count >= notification.max_retries:
            logger.warning(f"Max retry attempts reached for notification {notification.id}")
            return notification
        
        # Update retry count and status
        notification.retry_count += 1
        notification.status = NotificationStatus.RETRY
        self.db.commit()
        
        print(f"🚀 ABOUT TO QUEUE CELERY TASK for notification {notification.id}")
        print(f"🚀 Celery broker URL: {settings.CELERY_BROKER_URL}")

        try:
            task = send_sms_notification.delay(str(notification.id))
            print(f"✅ CELERY TASK QUEUED! Task ID: {task.id}")
        except Exception as e:
            print(f"❌ ERROR QUEUING CELERY TASK: {e}")
            raise

        # Queue new Celery task for retry
        task = send_sms_notification.delay(str(notification.id))
        
        # Update with new task ID
        notification.celery_task_id = task.id
        self.db.commit()
        
        logger.info(f"Notification {notification.id} queued for retry (attempt {notification.retry_count})")
        
        return notification
    
    # Private helper methods
    
    def _queue_sms(
        self, 
        recipient_phone: str, 
        message: str,
        notification_type: NotificationType,
        application: PassportApplication,
        sender_id: Optional[uuid.UUID]
    ) -> Notification:
        """
        Create notification record and queue Celery task for sending.
        This is now ASYNC - returns immediately!
        
        Args:
            recipient_phone: Recipient phone number
            message: SMS message content
            notification_type: Type of notification
            application: Related passport application
            sender_id: Optional sender user ID
            
        Returns:
            Notification object with PENDING/QUEUED status
        """
        # Create notification record in database
        notification = Notification(
            id=uuid.uuid4(),
            passport_application_id=application.id,
            sender_id=sender_id,
            notification_type=notification_type,
            message=message,
            recipient_phone=recipient_phone,
            status=NotificationStatus.PENDING,
            retry_count=0,
            created_at=datetime.utcnow()
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        # Queue Celery task for async sending
        task = send_sms_notification.delay(str(notification.id))
        
        # Update notification with Celery task info
        notification.celery_task_id = task.id
        notification.celery_queue = "notifications"
        notification.status = NotificationStatus.PENDING  # Will become SENT when task runs
        self.db.commit()
        
        logger.info(
            f"SMS notification queued: {notification.id} -> {recipient_phone} "
            f"(task: {task.id})"
        )
        
        return notification
    
    # Message formatting methods (unchanged - these are still useful!)
    
    def _format_ready_message(self, application: PassportApplication, applicant: User) -> str:
        """Format passport ready message"""
        return (
            f"Dear {applicant.first_name}, your passport (Application: {application.application_number}) "
            f"is ready for pickup. Please collect it within {application.pickup_expires_in_days} days. "
            f"Bring valid ID and this reference number."
        )
    
    def _format_reminder_message(
        self, 
        application: PassportApplication, 
        applicant: User, 
        days_remaining: int
    ) -> str:
        """Format pickup reminder message"""
        urgency = "URGENT: " if days_remaining <= 5 else ""
        
        return (
            f"{urgency}Dear {applicant.first_name}, reminder to collect your passport "
            f"(Application: {application.application_number}). "
            f"You have {days_remaining} days remaining before expiry."
        )
    
    def _format_status_update_message(
        self, 
        application: PassportApplication, 
        applicant: User, 
        new_status: ApplicationStatus
    ) -> str:
        """Format status update message"""
        status_messages = {
            ApplicationStatus.UNDER_REVIEW: "is now under review",
            ApplicationStatus.DOCUMENTS_REQUIRED: "requires additional documents",
            ApplicationStatus.PROCESSING: "is being processed",
            ApplicationStatus.QUALITY_CHECK: "is undergoing final quality checks",
            ApplicationStatus.READY_FOR_PICKUP: "is ready for pickup",
        }
        
        status_text = status_messages.get(new_status, f"status updated to {new_status.value}")
        
        return (
            f"Dear {applicant.first_name}, your passport application "
            f"({application.application_number}) {status_text}."
        )
    
    def _format_documents_required_message(
        self, 
        application: PassportApplication, 
        applicant: User, 
        required_documents: List[str]
    ) -> str:
        """Format documents required message"""
        docs_text = ", ".join(required_documents)
        
        return (
            f"Dear {applicant.first_name}, your passport application "
            f"({application.application_number}) requires these documents: {docs_text}. "
            f"Please submit them as soon as possible."
        )
    
    def _format_bulk_message(
        self, 
        template: str, 
        application: PassportApplication, 
        applicant: User
    ) -> str:
        """Format bulk message template with applicant data"""
        return template.format(
            first_name=applicant.first_name,
            last_name=applicant.last_name,
            application_number=application.application_number,
            status=application.status.value if hasattr(application.status, 'value') else application.status,
            priority_level=application.priority_level
        )