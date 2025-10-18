# create_tables.py
from dotenv import load_dotenv
load_dotenv()  # This loads the .env file

from app.database import create_tables
from app.models import *  # Import all models

if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    print("✅ All tables created successfully!")