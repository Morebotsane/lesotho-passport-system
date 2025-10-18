# migrate_appointment_table.py
import psycopg2
from app.core.config import settings

def migrate_appointments_table():
    """Add missing columns to pickup_appointments table"""
    
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    
    print("Adding missing columns to pickup_appointments table...")
    
    # Add all the missing columns
    migrations = [
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS location_id UUID REFERENCES pickup_locations(id);",
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS time_slot_id UUID REFERENCES time_slots(id);",
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS confirmation_code VARCHAR(10) UNIQUE;",
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS special_requirements TEXT;",
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS checked_in_at TIMESTAMP;",
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;", 
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP;",
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS cancellation_reason TEXT;",
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS original_appointment_id UUID REFERENCES pickup_appointments(id);",
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS rescheduled_from_datetime TIMESTAMP;",
        "ALTER TABLE pickup_appointments ADD COLUMN IF NOT EXISTS reschedule_count INTEGER DEFAULT 0;",
        "CREATE INDEX IF NOT EXISTS ix_pickup_appointments_confirmation_code ON pickup_appointments(confirmation_code);",
        "CREATE INDEX IF NOT EXISTS ix_pickup_appointments_scheduled_datetime ON pickup_appointments(scheduled_datetime);"
    ]
    
    for migration in migrations:
        try:
            cur.execute(migration)
            print(f"✅ Executed: {migration[:50]}...")
        except Exception as e:
            print(f"⚠️  Error with {migration[:30]}...: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("✅ Migration completed!")

if __name__ == "__main__":
    migrate_appointments_table()