# recreate_appointment_tables.py
from app.database import engine, Base
from app.models.appointment import PickupLocation, TimeSlot, PickupAppointment

def create_appointment_tables():
    print("Creating appointment tables...")
    # Create only the new appointment tables
    PickupLocation.__table__.create(engine, checkfirst=True)
    TimeSlot.__table__.create(engine, checkfirst=True) 
    PickupAppointment.__table__.create(engine, checkfirst=True)
    print("✅ Appointment tables created!")

if __name__ == "__main__":
    create_appointment_tables()