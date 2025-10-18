# app/api/appointments.py
"""
Appointment scheduling API endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date
import uuid
from sqlalchemy import func

from app.api.deps import get_current_active_user, get_current_officer, get_db
from app.models.user import User
from app.models.appointment import PickupLocation, PickupAppointment, AppointmentStatus, AppointmentType, TimeSlot
from app.schemas.appointment import (
    AppointmentCreate, AppointmentReschedule, AppointmentCancel,
    AvailabilityRequest, PickupLocationResponse, AppointmentResponse
)
from app.services.appointment_service import AppointmentService

router = APIRouter()

@router.get("/locations", response_model=List[PickupLocationResponse])
def get_pickup_locations(
    *,
    db: Session = Depends(get_db),
    active_only: bool = Query(True)
) -> Any:
    """Get all pickup locations"""
    query = db.query(PickupLocation)
    
    if active_only:
        query = query.filter(PickupLocation.is_active == True)
    
    return query.order_by(PickupLocation.name).all()

@router.post("/admin/generate-slots")
def generate_time_slots(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Should be admin
    days_ahead: int = Query(30, ge=1, le=90),
    location_id: Optional[str] = Query(None)
) -> Any:
    """Generate time slots for locations (Admin only)"""
    from datetime import datetime, timedelta, time as dt_time
    from app.api.deps import require_admin
    require_admin(current_user)
    
    # Get locations to generate slots for
    if location_id:
        locations = [db.query(PickupLocation).filter(PickupLocation.id == location_id).first()]
        if not locations[0]:
            raise HTTPException(status_code=404, detail="Location not found")
    else:
        locations = db.query(PickupLocation).filter(PickupLocation.is_active == True).all()
    
    total_slots_created = 0
    
    for location in locations:
        # Parse operating days
        operating_days = [int(d) for d in location.operating_days.split(',')]
        
        # Generate slots for each day
        start_date = datetime.now().date()
        
        for day_offset in range(days_ahead):
            current_date = start_date + timedelta(days=day_offset)
            weekday = current_date.weekday()
            
            # Skip if location is closed on this day
            if weekday not in operating_days:
                continue
            
            # Check if slots already exist for this date
            existing = db.query(TimeSlot).filter(
                TimeSlot.location_id == location.id,
                func.date(TimeSlot.slot_date) == current_date
            ).first()
            
            if existing:
                continue  # Skip if slots already exist
            
            # Generate time slots for this day
            current_time = datetime.combine(current_date, location.opens_at)
            end_time = datetime.combine(current_date, location.closes_at)
            slot_duration = timedelta(minutes=location.slot_duration_minutes)
            
            while current_time + slot_duration <= end_time:
                slot_end = current_time + slot_duration
                
                # Create time slot
                time_slot = TimeSlot(
                    id=uuid.uuid4(),
                    location_id=location.id,
                    slot_date=current_time,
                    start_time=current_time.time(),
                    end_time=slot_end.time(),
                    max_capacity=location.max_appointments_per_slot,
                    current_bookings=0,
                    status='available',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(time_slot)
                total_slots_created += 1
                
                current_time = slot_end
    
    db.commit()
    
    return {
        "message": f"Generated {total_slots_created} time slots",
        "locations_processed": len(locations),
        "days_ahead": days_ahead
    }

@router.post("/check-availability")
def check_appointment_availability(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    availability_request: AvailabilityRequest
) -> Any:
    """Check appointment availability"""
    service = AppointmentService(db)
    
    try:
        availability = service.check_availability(availability_request)
        
        # Helper function to format time slots
        def format_time_slots(slots):
            return [
                {
                    "id": str(slot.id),
                    "start_time": slot.start_time.strftime("%H:%M"),
                    "end_time": slot.end_time.strftime("%H:%M"),
                    "remaining_capacity": slot.remaining_capacity,
                    "max_capacity": slot.max_capacity
                }
                for slot in slots
            ]
        
        # Format alternative dates with their slots
        formatted_alternative_dates = {}
        for date_str, slots in availability["alternative_dates"].items():
            formatted_alternative_dates[date_str] = format_time_slots(slots)
        
        return {
            "location": {
                "id": str(availability["location"].id),
                "name": availability["location"].name,
                "address": availability["location"].address,
                "phone": availability["location"].phone,
                "email": availability["location"].email,
                "opens_at": availability["location"].opens_at.strftime("%H:%M"),
                "closes_at": availability["location"].closes_at.strftime("%H:%M")
            },
            "requested_date": availability["requested_date"].isoformat(),
            "available_slots": format_time_slots(availability["available_slots"]),
            "alternative_dates": formatted_alternative_dates,
            "total_available_slots": availability["total_available_slots"]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_appointment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    appointment_data: AppointmentCreate
) -> Any:
    """Create a new appointment"""
    service = AppointmentService(db)
    
    try:
        appointment = service.create_appointment(appointment_data, current_user.id)
        
        return {
            "id": str(appointment.id),
            "confirmation_code": appointment.confirmation_code,
            "scheduled_datetime": appointment.scheduled_datetime.isoformat(),
            "location_name": appointment.location.name,
            "status": appointment.status
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/officer/daily-schedule")
def get_officer_daily_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    date: Optional[str] = Query(None)
) -> Any:
    """Get officer's daily appointment schedule"""
    from datetime import datetime, date as dt_date
    
    # Parse date or use today
    if date:
        schedule_date = datetime.strptime(date, "%Y-%m-%d").date()
    else:
        schedule_date = dt_date.today()
    
    # Get appointments for officer's location
    if not current_user.assigned_location_id:
        return {
            "date": schedule_date.isoformat(),
            "location": None,
            "appointments": [],
            "summary": {
                "total": 0,
                "submission": 0,
                "collection": 0,
                "checked_in": 0,
                "completed": 0
            }
        }
    
    # Query appointments
    appointments = db.query(PickupAppointment).filter(
        PickupAppointment.location_id == current_user.assigned_location_id,
        func.date(PickupAppointment.scheduled_datetime) == schedule_date
    ).order_by(PickupAppointment.scheduled_datetime).all()
    
    # Calculate summary
    summary = {
        "total": len(appointments),
        "submission": len([a for a in appointments if a.appointment_type == AppointmentType.SUBMISSION]),
        "collection": len([a for a in appointments if a.appointment_type == AppointmentType.COLLECTION]),
        "checked_in": len([a for a in appointments if a.status == AppointmentStatus.CHECKED_IN.value]),
        "completed": len([a for a in appointments if a.status == AppointmentStatus.COMPLETED.value])
    }
    
    # FIXED: Manually serialize the location
    location_dict = None
    if current_user.assigned_location:
        location_dict = {
            "id": str(current_user.assigned_location.id),
            "name": current_user.assigned_location.name,
            "address": current_user.assigned_location.address,
            "phone": current_user.assigned_location.phone,
            "email": current_user.assigned_location.email
        }
    
    return {
        "date": schedule_date.isoformat(),
        "location": location_dict,  # CHANGED: Use dict instead of model
        "appointments": [
            {
                "id": str(apt.id),
                "confirmation_code": apt.confirmation_code,
                "time": apt.scheduled_datetime.strftime("%H:%M"),
                "type": apt.appointment_type.value,
                "status": apt.status,
                "application_number": apt.passport_application.application_number,
                "applicant_name": f"{apt.passport_application.first_name} {apt.passport_application.last_name}"
            }
            for apt in appointments
        ],
        "summary": summary
    }

@router.get("/my-appointments")
def get_my_appointments(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    include_completed: bool = Query(False)
) -> Any:
    """Get current user's appointments"""
    service = AppointmentService(db)
    appointments = service.get_appointments_by_user(current_user.id, include_completed)
    
    return [
        {
            "id": str(appointment.id),
            "confirmation_code": appointment.confirmation_code,
            "scheduled_datetime": appointment.scheduled_datetime.isoformat(),
            "location_name": appointment.location.name,
            "status": appointment.status,
            "type": appointment.appointment_type.value,  # ADD THIS LINE
            "application_number": appointment.passport_application.application_number,
            "can_be_rescheduled": appointment.can_be_rescheduled
        }
        for appointment in appointments
    ]

@router.put("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    appointment_id: uuid.UUID,
    new_time_slot_id: uuid.UUID,
    reason: Optional[str] = None
) -> Any:
    """Reschedule an appointment"""
    service = AppointmentService(db)
    
    try:
        appointment = service.reschedule_appointment(
            appointment_id=appointment_id,
            new_time_slot_id=new_time_slot_id,
            reason=reason
        )
        
        # Return complete appointment data
        return {
            "id": str(appointment.id),
            "confirmation_code": appointment.confirmation_code,
            "scheduled_datetime": appointment.scheduled_datetime.isoformat(),
            "location_name": appointment.location.name,
            "status": appointment.status,
            "passport_application_id": str(appointment.passport_application_id),
            "application_number": appointment.passport_application.application_number,
            "duration_minutes": appointment.duration_minutes,
            "reschedule_count": appointment.reschedule_count,
            "can_be_rescheduled": appointment.can_be_rescheduled,
            "is_upcoming": appointment.is_upcoming,
            "is_today": appointment.is_today,
            "created_at": appointment.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{appointment_id}/cancel")
def cancel_appointment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    appointment_id: uuid.UUID,
    reason: str
) -> Any:
    """Cancel an appointment"""
    service = AppointmentService(db)
    
    try:
        appointment = service.cancel_appointment(appointment_id, reason)
        return {"message": "Appointment cancelled successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Officer endpoints
@router.post("/{appointment_id}/check-in")
def check_in_appointment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Officers only
    appointment_id: uuid.UUID
) -> Any:
    """Check in an appointment (officer action)"""
    service = AppointmentService(db)
    
    try:
        appointment = service.check_in_appointment(appointment_id, current_user.id)
        return {
            "message": "Appointment checked in",
            "status": appointment.status
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Officer endpoints
@router.post("/{appointment_id}/complete")
def complete_appointment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Officers only
    appointment_id: uuid.UUID
) -> Any:
    """Complete an appointment (officer action)"""
    service = AppointmentService(db)
    
    try:
        appointment = service.complete_appointment(appointment_id, current_user.id)
        return {
            "message": "Appointment completed",
            "status": appointment.status
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Admin endpoints
@router.post("/admin/locations", status_code=status.HTTP_201_CREATED)
def create_location(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),  # Should be admin only
    location_data: dict
) -> Any:
    """Create a new pickup location (Admin only)"""
    from app.api.deps import require_admin
    require_admin(current_user)
    
    new_location = PickupLocation(
        id=uuid.uuid4(),
        name=location_data["name"],
        address=location_data["address"],
        phone=location_data.get("phone"),
        email=location_data.get("email"),
        opens_at=location_data["opens_at"],
        closes_at=location_data["closes_at"],
        is_active=location_data.get("is_active", True)
    )
    
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    
    return new_location


@router.put("/admin/locations/{location_id}")
def update_location(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    location_id: uuid.UUID,
    location_data: dict
) -> Any:
    """Update pickup location (Admin only)"""
    from app.api.deps import require_admin
    require_admin(current_user)
    
    location = db.query(PickupLocation).filter(PickupLocation.id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    if "name" in location_data:
        location.name = location_data["name"]
    if "address" in location_data:
        location.address = location_data["address"]
    if "phone" in location_data:
        location.phone = location_data["phone"]
    if "email" in location_data:
        location.email = location_data["email"]
    if "opens_at" in location_data:
        location.opens_at = location_data["opens_at"]
    if "closes_at" in location_data:
        location.closes_at = location_data["closes_at"]
    if "is_active" in location_data:
        location.is_active = location_data["is_active"]
    
    db.commit()
    db.refresh(location)
    
    return location


@router.delete("/admin/locations/{location_id}")
def delete_location(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    location_id: uuid.UUID
) -> Any:
    """Deactivate pickup location (Admin only)"""
    from app.api.deps import require_admin
    require_admin(current_user)
    
    location = db.query(PickupLocation).filter(PickupLocation.id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    location.is_active = False
    db.commit()
    
    return {"message": "Location deactivated successfully"}
