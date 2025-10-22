# seed_passport_offices.py
"""
Seed script to populate pickup locations with actual Lesotho passport offices
"""
from app.database import SessionLocal
from app.models.appointment import PickupLocation
from datetime import time

def seed_passport_offices():
    """Populate the database with Lesotho passport offices"""
    
    db = SessionLocal()
    
    # Check if locations already exist
    existing_count = db.query(PickupLocation).count()
    if existing_count > 0:
        print(f"Found {existing_count} existing locations. Skipping seeding.")
        db.close()
        return
    
    # Lesotho passport offices data
    passport_offices = [
        {
            "name": "Main Passport Office - Maseru",
            "address": "Ministry of Home Affairs, Kingsway Road, Maseru 100",
            "phone": "+266 2232 3771",
            "email": "passports.maseru@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",  # Mon-Fri
            "slot_duration_minutes": 30,
            "max_appointments_per_slot": 3,
            "advance_booking_days": 21
        },
        {
            "name": "Leribe District Passport Office",
            "address": "District Administrator's Office, Main Road, Leribe",
            "phone": "+266 2240 0234",
            "email": "passports.leribe@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",
            "slot_duration_minutes": 30,
            "max_appointments_per_slot": 2,
            "advance_booking_days": 14
        },
        {
            "name": "Berea District Passport Office",
            "address": "Government Complex, Teyateyaneng",
            "phone": "+266 2250 0445",
            "email": "passports.berea@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",  # Tue-Fri (closed Mondays)
            "slot_duration_minutes": 30,
            "max_appointments_per_slot": 2,
            "advance_booking_days": 14
        },
        {
            "name": "Mafeteng District Passport Office", 
            "address": "District Commissioner's Office, Mafeteng",
            "phone": "+266 2270 0156",
            "email": "passports.mafeteng@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",  # Mon, Wed, Fri
            "slot_duration_minutes": 30,
            "max_appointments_per_slot": 1,
            "advance_booking_days": 10
        },
        {
            "name": "Mohale's Hoek District Passport Office",
            "address": "Government Offices, Mohale's Hoek",
            "phone": "+266 2278 5432",
            "email": "passports.mohaleshoek@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",  # Mon, Wed, Fri
            "slot_duration_minutes": 30,
            "max_appointments_per_slot": 1,
            "advance_booking_days": 10
        },
        {
            "name": "Quthing District Passport Office",
            "address": "District Administration Building, Quthing",
            "phone": "+266 2295 0123",
            "email": "passports.quthing@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",  # Tue, Thu only
            "slot_duration_minutes": 45,
            "max_appointments_per_slot": 1,
            "advance_booking_days": 7
        },
        {
            "name": "Qacha's Nek District Passport Office",
            "address": "Government Complex, Qacha's Nek",
            "phone": "+266 2295 4567",
            "email": "passports.qachasnek@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",  # Tue, Thu only  
            "slot_duration_minutes": 45,
            "max_appointments_per_slot": 1,
            "advance_booking_days": 7
        },
        {
            "name": "Butha-Buthe District Passport Office",
            "address": "District Office Complex, Butha-Buthe",
            "phone": "+266 2246 0890",
            "email": "passports.buthabuthe@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",  # Mon, Wed, Fri
            "slot_duration_minutes": 30,
            "max_appointments_per_slot": 2,
            "advance_booking_days": 14
        },
        {
            "name": "Mokhotlong District Passport Office",
            "address": "District Administrative Centre, Mokhotlong",
            "phone": "+266 2290 2345",
            "email": "passports.mokhotlong@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",  # Tue, Fri only
            "slot_duration_minutes": 60,
            "max_appointments_per_slot": 1,
            "advance_booking_days": 7
        },
        {
            "name": "Thaba-Tseka District Passport Office",
            "address": "Government Buildings, Thaba-Tseka",
            "phone": "+266 2290 6789",
            "email": "passports.thabatseka@gov.ls",
            "opens_at": time(8, 0),
            "closes_at": time(16, 30),
            "operating_days": "0,1,2,3,4",  # Wed, Fri only
            "slot_duration_minutes": 60,
            "max_appointments_per_slot": 1,
            "advance_booking_days": 7
        }
    ]
    
    # Create location objects
    locations_created = []
    for office_data in passport_offices:
        location = PickupLocation(
            name=office_data["name"],
            address=office_data["address"],
            phone=office_data["phone"],
            email=office_data["email"],
            opens_at=office_data["opens_at"],
            closes_at=office_data["closes_at"],
            operating_days=office_data["operating_days"],
            slot_duration_minutes=office_data["slot_duration_minutes"],
            max_appointments_per_slot=office_data["max_appointments_per_slot"],
            advance_booking_days=office_data["advance_booking_days"],
            is_active=True
        )
        
        db.add(location)
        locations_created.append(location)
    
    # Commit all locations
    db.commit()
    
    # Print summary
    print("✅ Successfully created Lesotho passport offices:")
    for i, location in enumerate(locations_created, 1):
        print(f"{i:2d}. {location.name}")
        print(f"    📍 {location.address}")
        print(f"    📞 {location.phone}")
        print(f"    🕐 {location.opens_at.strftime('%H:%M')} - {location.closes_at.strftime('%H:%M')}")
        print(f"    📅 Operating days: {location.operating_days}")
        print(f"    ⏱️  {location.slot_duration_minutes}min slots, max {location.max_appointments_per_slot} per slot")
        print()
    
    db.close()
    print(f"🎉 Total locations created: {len(locations_created)}")

if __name__ == "__main__":
    print("🏢 Seeding Lesotho Passport Offices...")
    seed_passport_offices()
    print("✨ Database seeding complete!")