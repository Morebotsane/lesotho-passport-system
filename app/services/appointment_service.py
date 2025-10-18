# app/services/appointment_service.py - COMPLETE VERSION
"""
Appointment scheduling service
Handles appointment booking, rescheduling, and calendar management
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta, date, time
import uuid

from app.models.appointment import (
    PickupLocation, TimeSlot, PickupAppointment, 
    AppointmentStatus, TimeSlotStatus, AppointmentType
)
from app.models.passport_application import PassportApplication, ApplicationStatus
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate, AvailabilityRequest, AppointmentFilter
)

class AppointmentService:
    """Service for appointment scheduling and management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_appointment(
        self, 
        appointment_data: AppointmentCreate, 
        applicant_id: uuid.UUID
    ) -> PickupAppointment:
        """Create a new pickup appointment"""
        
        # Verify passport application belongs to applicant
        application = self.db.query(PassportApplication).filter(
            and_(
                PassportApplication.id == appointment_data.passport_application_id,
                PassportApplication.applicant_id == applicant_id
            )
        ).first()
        
        if not application:
            raise ValueError("Application not found")
        
        # CHECK STATUS BASED ON APPOINTMENT TYPE - KEY FIX
        from app.models.appointment import AppointmentType
        
        if appointment_data.appointment_type == AppointmentType.SUBMISSION:
            # For submission appointments, application must be in submitted status
            if application.status != ApplicationStatus.SUBMITTED.value:
                raise ValueError(f"Application must be in 'submitted' status for submission appointments. Current status: {application.status}")
        elif appointment_data.appointment_type == AppointmentType.COLLECTION:
            # For collection appointments, passport must be ready for pickup
            if application.status != ApplicationStatus.READY_FOR_PICKUP.value:
                raise ValueError(f"Passport must be ready for pickup. Current status: {application.status}")
        else:
            raise ValueError(f"Invalid appointment type: {appointment_data.appointment_type}")
        
        # Check if application already has an active appointment of this type
        existing = self.db.query(PickupAppointment).filter(
            and_(
                PickupAppointment.passport_application_id == appointment_data.passport_application_id,
                PickupAppointment.appointment_type == appointment_data.appointment_type,
                PickupAppointment.status.in_([
                    AppointmentStatus.SCHEDULED.value,
                    AppointmentStatus.CONFIRMED.value
                ])
            )
        ).first()
        
        if existing:
            raise ValueError(f"Application already has an active {appointment_data.appointment_type.value} appointment")
        
        # Verify time slot is available
        time_slot = self.db.query(TimeSlot).filter(
            TimeSlot.id == appointment_data.time_slot_id
        ).first()
        
        if not time_slot or not time_slot.is_available:
            raise ValueError("Time slot is not available")
        
        if time_slot.location_id != appointment_data.location_id:
            raise ValueError("Location does not match time slot")
        
        # Create appointment
        appointment = PickupAppointment(
            passport_application_id=appointment_data.passport_application_id,
            location_id=appointment_data.location_id,
            time_slot_id=appointment_data.time_slot_id,
            scheduled_datetime=datetime.combine(
                time_slot.slot_date.date(), 
                time_slot.start_time
            ),
            appointment_type=appointment_data.appointment_type,  # ADD THIS LINE
            duration_minutes=time_slot.location.slot_duration_minutes,
            notes=appointment_data.notes,
            special_requirements=appointment_data.special_requirements,
            status=AppointmentStatus.CONFIRMED.value
        )
        
        appointment.generate_confirmation_code()
        time_slot.book_slot()
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment
    
    def check_availability(self, availability_request: AvailabilityRequest) -> Dict[str, Any]:
        """Check appointment availability for requested dates"""
        
        location = self.db.query(PickupLocation).filter(
            PickupLocation.id == availability_request.location_id
        ).first()
        
        if not location:
            raise ValueError("Location not found")
        
        # Generate time slots if needed
        dates_to_check = [availability_request.preferred_date]
        if availability_request.alternative_dates:
            dates_to_check.extend(availability_request.alternative_dates)
        
        for check_date in dates_to_check:
            self._generate_time_slots_for_date(location, check_date)
        
        # Get available slots
        preferred_slots = self._get_available_slots_for_date(
            location, 
            availability_request.preferred_date,
            availability_request.preferred_time_range
        )
        
        alternative_slots = {}
        if availability_request.alternative_dates:
            for alt_date in availability_request.alternative_dates:
                slots = self._get_available_slots_for_date(
                    location, alt_date, availability_request.preferred_time_range
                )
                if slots:
                    alternative_slots[alt_date.isoformat()] = slots
        
        total_available = len(preferred_slots) + sum(
            len(slots) for slots in alternative_slots.values()
        )
        
        return {
            "location": location,
            "requested_date": availability_request.preferred_date,
            "available_slots": preferred_slots,
            "alternative_dates": alternative_slots,
            "total_available_slots": total_available
        }
    
    def reschedule_appointment(
        self, 
        appointment_id: uuid.UUID,
        new_time_slot_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> PickupAppointment:
        """Reschedule an existing appointment"""
        
        appointment = self.db.query(PickupAppointment).filter(
            PickupAppointment.id == appointment_id
        ).first()
        
        if not appointment:
            raise ValueError("Appointment not found")
        
        if not appointment.can_be_rescheduled:
            raise ValueError("Appointment cannot be rescheduled")
        
        new_slot = self.db.query(TimeSlot).filter(
            TimeSlot.id == new_time_slot_id
        ).first()
        
        if not new_slot or not new_slot.is_available:
            raise ValueError("New time slot is not available")
        
        # Release old slot and book new one
        if appointment.time_slot:
            appointment.time_slot.release_slot()
        
        appointment.rescheduled_from_datetime = appointment.scheduled_datetime
        appointment.reschedule_count += 1
        appointment.time_slot_id = new_time_slot_id
        appointment.location_id = new_slot.location_id
        appointment.scheduled_datetime = datetime.combine(
            new_slot.slot_date.date(),
            new_slot.start_time
        )
        appointment.status = AppointmentStatus.RESCHEDULED.value
        
        if reason:
            appointment.notes = f"Rescheduled: {reason}. Previous notes: {appointment.notes or 'None'}"
        
        new_slot.book_slot()
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment
    
    def cancel_appointment(self, appointment_id: uuid.UUID, reason: str) -> PickupAppointment:
        """Cancel an appointment"""
        
        appointment = self.db.query(PickupAppointment).filter(
            PickupAppointment.id == appointment_id
        ).first()
        
        if not appointment:
            raise ValueError("Appointment not found")
        
        if appointment.status in [AppointmentStatus.COMPLETED.value, AppointmentStatus.CANCELLED.value]:
            raise ValueError("Cannot cancel completed or already cancelled appointment")
        
        appointment.cancel(reason)
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment
         
    def check_in_appointment(self, appointment_id: uuid.UUID, officer_id: uuid.UUID) -> PickupAppointment:
        """Check in an appointment (officer action)"""
        from datetime import date
        
        appointment = self.db.query(PickupAppointment).filter(
            PickupAppointment.id == appointment_id
        ).first()
        
        if not appointment:
            raise ValueError("Appointment not found")
        
        # Check if appointment is today (using date comparison, not property)
        appointment_date = appointment.scheduled_datetime.date()
        today = date.today()
        
        print(f"🔍 Check-in attempt: Appointment date={appointment_date}, Today={today}")
        
        if appointment_date != today:
            raise ValueError(f"Can only check in appointments scheduled for today. This appointment is for {appointment_date}")
        
        # Check status is valid for check-in
        if appointment.status not in ['scheduled', 'confirmed', 'rescheduled']:
            raise ValueError(f"Cannot check in appointment with status: {appointment.status}")
        
        appointment.check_in()
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment        
    
    def complete_appointment(self, appointment_id: uuid.UUID, officer_id: uuid.UUID) -> PickupAppointment:
        """Complete an appointment (passport collected)"""
        
        appointment = self.db.query(PickupAppointment).filter(
            PickupAppointment.id == appointment_id
        ).first()
        
        if not appointment:
            raise ValueError("Appointment not found")
        
        appointment.complete()
        
        # Update passport application to collected
        if appointment.passport_application:
            appointment.passport_application.status = ApplicationStatus.COLLECTED.value
            appointment.passport_application.collected_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment
    
    def get_appointments_by_user(self, user_id: uuid.UUID, include_completed: bool = False) -> List[PickupAppointment]:
        """Get appointments for a specific user"""
        
        query = self.db.query(PickupAppointment).join(
            PassportApplication,
            PassportApplication.id == PickupAppointment.passport_application_id
        ).filter(
            PassportApplication.applicant_id == user_id
        )
        
        if not include_completed:
            query = query.filter(
                PickupAppointment.status != AppointmentStatus.COMPLETED.value
            )
        
        return query.order_by(desc(PickupAppointment.scheduled_datetime)).all()
    
    # Helper methods
    def _generate_time_slots_for_date(self, location: PickupLocation, target_date: date):
        """Generate time slots for a date if they don't exist"""
        
        if not location.is_open_on_day(target_date.weekday()):
            return
        
        # Check if slots already exist
        existing = self.db.query(TimeSlot).filter(
            and_(
                TimeSlot.location_id == location.id,
                func.date(TimeSlot.slot_date) == target_date
            )
        ).count()
        
        if existing > 0:
            return
        
        # Generate slots
        current_time = location.opens_at
        slot_duration = timedelta(minutes=location.slot_duration_minutes)
        
        while current_time < location.closes_at:
            slot_end = (datetime.combine(date.today(), current_time) + slot_duration).time()
            
            if slot_end > location.closes_at:
                break
            
            time_slot = TimeSlot(
                location_id=location.id,
                slot_date=datetime.combine(target_date, current_time),
                start_time=current_time,
                end_time=slot_end,
                max_capacity=location.max_appointments_per_slot
            )
            
            self.db.add(time_slot)
            current_time = slot_end
        
        self.db.commit()
    
    def _get_available_slots_for_date(
        self, 
        location: PickupLocation, 
        target_date: date,
        time_range: Optional[Dict[str, time]] = None
    ) -> List[TimeSlot]:
        """Get available time slots for a specific date"""
        
        query = self.db.query(TimeSlot).filter(
            and_(
                TimeSlot.location_id == location.id,
                func.date(TimeSlot.slot_date) == target_date,
                TimeSlot.status == TimeSlotStatus.AVAILABLE.value,
                TimeSlot.current_bookings < TimeSlot.max_capacity
            )
        )
        
        # Apply time range filter
        if time_range and "start" in time_range and "end" in time_range:
            query = query.filter(
                and_(
                    TimeSlot.start_time >= time_range["start"],
                    TimeSlot.start_time <= time_range["end"]
                )
            )
        
        # Only future slots for today
        if target_date == date.today():
            current_time = datetime.now().time()
            query = query.filter(TimeSlot.start_time > current_time)
        
        return query.order_by(TimeSlot.start_time).all()