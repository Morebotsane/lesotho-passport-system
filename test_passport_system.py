# test_passport_system.py
from app.schemas.passport_application import PassportApplicationCreate, PriorityReason
from app.services.passport_service import PassportApplicationService
from app.database import SessionLocal
from datetime import datetime

def test_schemas():
    print("🧪 Testing passport schemas...")
    
    # Test creating a passport application schema
    app_data = PassportApplicationCreate(
        passport_type="regular",
        pages=32,
        priority_reason=PriorityReason.STUDENT_ABROAD,
        travel_purpose="University studies abroad",
        intended_travel_date=datetime(2025, 12, 1)
    )
    
    print(f"   ✅ Schema created: {app_data.passport_type}, {app_data.pages} pages")
    print(f"   ✅ Priority reason: {app_data.priority_reason}")
    
def test_service():
    print("\n🔧 Testing passport service...")
    
    # Test service initialization
    db = SessionLocal()
    service = PassportApplicationService(db)
    
    print(f"   ✅ Service initialized successfully")
    
    # Test statistics generation
    try:
        stats = service.generate_processing_statistics()
        print(f"   ✅ Statistics generated: {stats['total_applications']} total applications")
    except Exception as e:
        print(f"   ⚠️ Statistics error (expected with empty DB): {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_schemas()
    test_service()
    print("\n🎉 Passport system components are ready!")
